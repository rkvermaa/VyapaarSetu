/**
 * Session Manager — Handles per-user WhatsApp sessions for VyapaarSetu.
 */

import makeWASocket, { DisconnectReason, useMultiFileAuthState, fetchLatestBaileysVersion } from '@whiskeysockets/baileys';
import fs from 'fs';
import path from 'path';
import QRCode from 'qrcode';
import axios from 'axios';
import pino from 'pino';
import { config } from './config.js';
import { useDBAuthState, deleteDBAuth } from './dbAuthState.js';

const logger = pino({ level: 'debug' });

// Store active sessions: userId -> { socket, qr, status, phoneNumber }
const sessions = new Map();

function ensureSessionsDir() {
  if (!fs.existsSync(config.sessionsDir)) {
    fs.mkdirSync(config.sessionsDir, { recursive: true });
  }
}

function getSessionDir(userId) {
  return path.join(config.sessionsDir, userId);
}

/**
 * Start or resume a WhatsApp session for a user.
 */
export async function startSession(userId) {
  ensureSessionsDir();

  if (sessions.has(userId)) {
    const existing = sessions.get(userId);
    if (existing.status === 'connected') {
      return { status: 'connected', phoneNumber: existing.phoneNumber };
    }
    if (existing.status === 'qr' && existing.qrBase64) {
      return { status: 'qr', qr: existing.qrBase64 };
    }
    if (existing.socket) {
      try { existing.socket.end(); } catch (e) { /* ignore */ }
    }
  }

  let state, saveCreds;

  if (config.useDBAuth) {
    logger.info(`Using database auth for user: ${userId}`);
    const dbAuth = await useDBAuthState(userId);
    state = dbAuth.state;
    saveCreds = dbAuth.saveCreds;
  } else {
    const sessionDir = getSessionDir(userId);
    logger.info(`Using file auth for user: ${userId} at ${sessionDir}`);
    const fileAuth = await useMultiFileAuthState(sessionDir);
    state = fileAuth.state;
    saveCreds = fileAuth.saveCreds;
  }

  const { version, isLatest } = await fetchLatestBaileysVersion();
  logger.info(`Using WA version: ${version.join('.')}, isLatest: ${isLatest}`);

  sessions.set(userId, {
    socket: null,
    qr: null,
    qrBase64: null,
    status: 'connecting',
    phoneNumber: null,
  });

  const socket = makeWASocket({
    auth: state,
    version,
    logger: pino({ level: 'warn' }),
    browser: ['VyapaarSetu', 'Chrome', '120.0.6099'],
    syncFullHistory: false,
    markOnlineOnConnect: true,
    connectTimeoutMs: 60000,
    defaultQueryTimeoutMs: 60000,
    keepAliveIntervalMs: 30000,
    retryRequestDelayMs: 250,
    getMessage: async () => ({ conversation: '' }),
  });

  sessions.get(userId).socket = socket;

  socket.ev.on('connection.update', async (update) => {
    const { connection, lastDisconnect, qr } = update;
    const session = sessions.get(userId);

    logger.info(`Connection update for user ${userId}:`, { connection, qr: qr ? 'present' : 'none' });

    if (qr) {
      try {
        const qrBase64 = await QRCode.toDataURL(qr);
        session.qr = qr;
        session.qrBase64 = qrBase64;
        session.status = 'qr';
        logger.info(`QR generated for user: ${userId}`);
      } catch (err) {
        logger.error(`Failed to generate QR for user ${userId}:`, err);
      }
    }

    if (connection === 'close') {
      const statusCode = lastDisconnect?.error?.output?.statusCode;
      const errorMessage = lastDisconnect?.error?.message || 'Unknown error';

      logger.info(`Connection closed for user ${userId}. Status: ${statusCode}. Error: ${errorMessage}`);

      const shouldReconnect = statusCode !== DisconnectReason.loggedOut &&
                              statusCode !== DisconnectReason.forbidden &&
                              statusCode !== 405;

      if (shouldReconnect) {
        session.status = 'reconnecting';
        logger.info(`Will reconnect for user ${userId} in 5 seconds...`);
        setTimeout(() => startSession(userId), 5000);
      } else {
        session.status = 'disconnected';
        session.socket = null;
        session.phoneNumber = null;
        notifyBackend(userId, 'disconnected', { reason: errorMessage });
      }
    }

    if (connection === 'open') {
      const phoneNumber = socket.user?.id?.split(':')[0] || null;
      session.status = 'connected';
      session.phoneNumber = phoneNumber;
      session.qr = null;
      session.qrBase64 = null;

      logger.info(`Connected for user ${userId}. Phone: ${phoneNumber}`);
      notifyBackend(userId, 'connected', { phoneNumber });
    }
  });

  socket.ev.on('creds.update', saveCreds);

  socket.ev.on('messages.upsert', async ({ messages, type }) => {
    if (type === 'history_sync') return;

    for (const msg of messages) {
      if (msg.key.fromMe) continue;
      if (!msg.message) continue;

      const messageText = msg.message.conversation ||
        msg.message.extendedTextMessage?.text ||
        msg.message.imageMessage?.caption ||
        msg.message.videoMessage?.caption ||
        '';

      if (!messageText) continue;

      const remoteJid = msg.key.remoteJid || '';
      // Prefer senderPn (real phone number) over LID-based remoteJid
      const senderPn = msg.key.senderPn || '';
      let senderNumber;
      if (senderPn) {
        senderNumber = senderPn.replace('@s.whatsapp.net', '');
      } else {
        senderNumber = remoteJid
          .replace('@s.whatsapp.net', '')
          .replace('@g.us', '')
          .replace('@lid', '');
      }
      const senderName = msg.pushName || senderNumber;

      logger.info(`Message from ${senderName} (phone=${senderNumber}, jid=${remoteJid}) to user ${userId}: ${messageText.substring(0, 50)}...`);

      await forwardMessageToBackend(userId, {
        from: senderNumber,
        fromName: senderName,
        fromJid: remoteJid,
        senderPn: senderPn,
        message: messageText,
        messageId: msg.key.id,
        timestamp: msg.messageTimestamp,
      });
    }
  });

  return {
    status: 'connecting',
    message: 'Session starting, QR code will be available shortly',
  };
}

/**
 * Get session status for a user.
 */
export function getSessionStatus(userId) {
  const session = sessions.get(userId);
  if (!session) {
    return { status: 'not_started', connected: false };
  }
  return {
    status: session.status,
    connected: session.status === 'connected',
    phoneNumber: session.phoneNumber,
    qr: session.qrBase64,
  };
}

/**
 * Send a WhatsApp message via an active session.
 */
export async function sendMessage(userId, to, message) {
  const session = sessions.get(userId);
  if (!session || session.status !== 'connected') {
    throw new Error(`Session not connected for user ${userId}`);
  }
  const jid = to.includes('@') ? to : `${to}@s.whatsapp.net`;
  try {
    await session.socket.sendMessage(jid, { text: message });
    logger.info(`Message sent to ${to} for user ${userId}`);
    return { success: true };
  } catch (err) {
    logger.error(`Failed to send message for user ${userId}:`, err);
    throw err;
  }
}

/**
 * Disconnect session (soft — keeps credentials for resume).
 */
export async function disconnectSession(userId) {
  const session = sessions.get(userId);
  if (!session || !session.socket) {
    return { success: true, message: 'Session not active' };
  }
  try {
    session.socket.end();
    sessions.delete(userId);
    return { success: true, message: 'Disconnected. You can reconnect without QR scan.' };
  } catch (err) {
    logger.error(`Failed to disconnect session for user ${userId}:`, err);
    throw err;
  }
}

/**
 * Logout session (full — removes credentials, requires QR re-scan).
 */
export async function logoutSession(userId) {
  const session = sessions.get(userId);
  try {
    if (session?.socket) {
      await session.socket.logout();
    }
    sessions.delete(userId);
    if (config.useDBAuth) {
      await deleteDBAuth(userId);
    } else {
      const sessionDir = getSessionDir(userId);
      if (fs.existsSync(sessionDir)) {
        fs.rmSync(sessionDir, { recursive: true });
      }
    }
    return { success: true, message: 'Logged out. QR scan required to reconnect.' };
  } catch (err) {
    logger.error(`Failed to logout session for user ${userId}:`, err);
    throw err;
  }
}

/**
 * Forward incoming WhatsApp message to backend webhook.
 */
async function forwardMessageToBackend(userId, messageData) {
  try {
    const webhookUrl = `${config.backendWebhookUrl}/message`;
    logger.info(`Forwarding message to backend: ${webhookUrl}`);

    await axios.post(webhookUrl, {
      userId,
      from: messageData.from,
      fromName: messageData.fromName,
      fromJid: messageData.fromJid,
      senderPn: messageData.senderPn || '',
      message: messageData.message,
      messageId: messageData.messageId,
      timestamp: messageData.timestamp,
      channel: 'whatsapp',
    }, {
      headers: {
        'Content-Type': 'application/json',
        'X-API-Key': config.apiKey,
      },
      timeout: 120000,
    });
  } catch (err) {
    logger.error(`Failed to forward message to backend for user ${userId}: ${err.message}`);
  }
}

/**
 * Notify backend about session status changes.
 */
async function notifyBackend(userId, event, data) {
  try {
    await axios.post(`${config.backendWebhookUrl}/status`, {
      userId,
      event,
      ...data,
    }, {
      headers: {
        'Content-Type': 'application/json',
        'X-API-Key': config.apiKey,
      },
      timeout: 5000,
    });
  } catch (err) {
    logger.error(`Failed to notify backend about ${event} for user ${userId}: ${err.message}`);
  }
}

/**
 * Auto-restore sessions that have saved credentials in the database.
 */
export async function restoreSessions() {
  if (!config.useDBAuth) {
    logger.info('DB auth disabled, skipping session restore');
    return;
  }

  try {
    const response = await axios.get(
      `${config.backendUrl}/api/v1/channel/whatsapp/auth/restorable`,
      {
        headers: {
          'Content-Type': 'application/json',
          'X-API-Key': config.apiKey,
        },
        timeout: 10000,
      }
    );

    const restorable = response.data?.sessions || [];
    if (restorable.length === 0) {
      logger.info('No sessions to restore');
      return;
    }

    logger.info(`Found ${restorable.length} session(s) to restore`);

    for (const session of restorable) {
      const sessionId = session.session_id;
      logger.info(`Restoring session ${sessionId} (user: ${session.user_id}, phone: ${session.phone_number || 'unknown'})`);
      try {
        await startSession(sessionId);
      } catch (err) {
        logger.error(`Failed to restore session ${sessionId}: ${err.message}`);
      }
      await new Promise(resolve => setTimeout(resolve, 2000));
    }
  } catch (err) {
    logger.error(`Failed to fetch restorable sessions: ${err.message}`);
    throw err;
  }
}

/**
 * Get all active sessions summary.
 */
export function getAllSessions() {
  const result = {};
  for (const [userId, session] of sessions) {
    result[userId] = {
      status: session.status,
      connected: session.status === 'connected',
      phoneNumber: session.phoneNumber,
    };
  }
  return result;
}

/**
 * Reset session — clear credentials and start fresh.
 */
export async function resetSession(userId) {
  const session = sessions.get(userId);
  if (session?.socket) {
    try { session.socket.end(); } catch (e) { /* ignore */ }
  }
  sessions.delete(userId);
  if (config.useDBAuth) {
    await deleteDBAuth(userId);
  } else {
    const sessionDir = getSessionDir(userId);
    if (fs.existsSync(sessionDir)) {
      fs.rmSync(sessionDir, { recursive: true, force: true });
    }
  }
  return await startSession(userId);
}
