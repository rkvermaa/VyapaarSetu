/**
 * VyapaarSetu Baileys WhatsApp Service
 *
 * Provides API for:
 * - Starting WhatsApp sessions per user
 * - Generating QR codes for authentication
 * - Sending/receiving messages
 */

import express from 'express';
import pino from 'pino';
import { config } from './config.js';
import {
  startSession,
  getSessionStatus,
  sendMessage,
  disconnectSession,
  logoutSession,
  getAllSessions,
  resetSession,
  restoreSessions,
} from './sessions.js';

const app = express();
const logger = pino({ level: 'info' });

// Middleware
app.use(express.json());

// Simple API key authentication
const authenticate = (req, res, next) => {
  const apiKey = req.headers['x-api-key'];
  if (apiKey !== config.apiKey) {
    return res.status(401).json({ error: 'Unauthorized' });
  }
  next();
};

// Health check (no auth required)
app.get('/health', (req, res) => {
  res.json({ status: 'ok', service: 'vyapaarsetu-baileys' });
});

// List all sessions
app.get('/sessions', authenticate, (req, res) => {
  const sessions = getAllSessions();
  res.json({ sessions });
});

// Start WhatsApp session
app.post('/sessions/:userId/start', authenticate, async (req, res) => {
  const { userId } = req.params;
  try {
    logger.info(`Starting session for user: ${userId}`);
    const result = await startSession(userId);
    res.json(result);
  } catch (err) {
    logger.error(`Failed to start session for ${userId}:`, err);
    res.status(500).json({ error: err.message });
  }
});

// Get session status
app.get('/sessions/:userId/status', authenticate, async (req, res) => {
  const { userId } = req.params;
  try {
    const status = getSessionStatus(userId);
    if (status.status === 'connecting') {
      await new Promise(resolve => setTimeout(resolve, 1000));
      const updatedStatus = getSessionStatus(userId);
      return res.json(updatedStatus);
    }
    res.json(status);
  } catch (err) {
    logger.error(`Failed to get status for ${userId}:`, err);
    res.status(500).json({ error: err.message });
  }
});

// Send message
app.post('/sessions/:userId/send', authenticate, async (req, res) => {
  const { userId } = req.params;
  const { to, message } = req.body;
  if (!to || !message) {
    return res.status(400).json({ error: 'Missing required fields: to, message' });
  }
  try {
    const result = await sendMessage(userId, to, message);
    res.json(result);
  } catch (err) {
    logger.error(`Failed to send message for ${userId}:`, err);
    res.status(500).json({ error: err.message });
  }
});

// Disconnect (soft — keeps credentials)
app.post('/sessions/:userId/disconnect', authenticate, async (req, res) => {
  const { userId } = req.params;
  try {
    const result = await disconnectSession(userId);
    res.json(result);
  } catch (err) {
    logger.error(`Failed to disconnect session for ${userId}:`, err);
    res.status(500).json({ error: err.message });
  }
});

// Logout (full — removes credentials)
app.post('/sessions/:userId/logout', authenticate, async (req, res) => {
  const { userId } = req.params;
  try {
    const result = await logoutSession(userId);
    res.json(result);
  } catch (err) {
    logger.error(`Failed to logout session for ${userId}:`, err);
    res.status(500).json({ error: err.message });
  }
});

// Reset session
app.post('/sessions/:userId/reset', authenticate, async (req, res) => {
  const { userId } = req.params;
  try {
    logger.info(`Resetting session for user: ${userId}`);
    const result = await resetSession(userId);
    res.json(result);
  } catch (err) {
    logger.error(`Failed to reset session for ${userId}:`, err);
    res.status(500).json({ error: err.message });
  }
});

// Error handling
app.use((err, req, res, next) => {
  logger.error('Unhandled error:', err);
  res.status(500).json({ error: 'Internal server error' });
});

// Start server
app.listen(config.port, () => {
  logger.info(`VyapaarSetu Baileys WhatsApp Service running on port ${config.port}`);
  logger.info(`Backend webhook URL: ${config.backendWebhookUrl}`);

  // Auto-restore previously connected sessions with retry
  const maxRetries = 5;
  const retryRestore = async (attempt = 1) => {
    logger.info(`Auto-restoring saved WhatsApp sessions (attempt ${attempt}/${maxRetries})...`);
    try {
      await restoreSessions();
    } catch (err) {
      if (attempt < maxRetries) {
        const delay = attempt * 5000;
        logger.warn(`Session restore failed, retrying in ${delay / 1000}s: ${err.message}`);
        setTimeout(() => retryRestore(attempt + 1), delay);
      } else {
        logger.error(`Session restore failed after ${maxRetries} attempts: ${err.message}`);
      }
    }
  };
  setTimeout(() => retryRestore(), 3000);
});
