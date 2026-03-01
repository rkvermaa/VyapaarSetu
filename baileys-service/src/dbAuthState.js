/**
 * Database-backed Auth State for Baileys (VyapaarSetu)
 *
 * Stores auth credentials in PostgreSQL via backend API.
 */

import { proto } from '@whiskeysockets/baileys';
import { initAuthCreds } from '@whiskeysockets/baileys';
import axios from 'axios';
import pino from 'pino';
import { config } from './config.js';

const logger = pino({ level: 'info' });

const BufferJSON = {
  replacer: (k, value) => {
    if (Buffer.isBuffer(value) || value instanceof Uint8Array || value?.type === 'Buffer') {
      return {
        type: 'Buffer',
        data: Buffer.from(value?.data || value).toString('base64'),
      };
    }
    return value;
  },
  reviver: (_, value) => {
    if (typeof value === 'object' && value !== null && value.type === 'Buffer' && value.data) {
      return Buffer.from(value.data, 'base64');
    }
    return value;
  },
};

function serializeData(data) {
  return JSON.parse(JSON.stringify(data, BufferJSON.replacer));
}

function deserializeData(data) {
  return JSON.parse(JSON.stringify(data), BufferJSON.reviver);
}

/**
 * Create database-backed auth state for Baileys.
 */
export async function useDBAuthState(sessionId) {
  const apiUrl = config.backendUrl;
  const apiKey = config.apiKey;

  const headers = {
    'Content-Type': 'application/json',
    'X-API-Key': apiKey,
  };

  let keysCache = {};
  let credsCache = null;
  let pendingKeyUpdates = {};
  let keyUpdateTimeout = null;

  async function loadAuth() {
    try {
      const response = await axios.get(
        `${apiUrl}/api/v1/channel/whatsapp/auth/${sessionId}`,
        { headers, timeout: 10000 }
      );

      const { creds, keys, has_credentials } = response.data;

      if (has_credentials && creds && Object.keys(creds).length > 0) {
        credsCache = deserializeData(creds);
        keysCache = keys || {};
        logger.info(`Loaded existing auth for session ${sessionId}`);
        return true;
      }

      logger.info(`No existing auth for session ${sessionId}, will create new`);
      return false;
    } catch (err) {
      if (err.response?.status === 404) {
        logger.info(`No auth found for session ${sessionId}`);
        return false;
      }
      logger.error(`Failed to load auth for session ${sessionId}: ${err.message}`);
      return false;
    }
  }

  async function saveCreds() {
    if (!credsCache) return;

    try {
      await axios.put(
        `${apiUrl}/api/v1/channel/whatsapp/auth/${sessionId}/creds`,
        { creds: serializeData(credsCache) },
        { headers, timeout: 10000 }
      );
      logger.debug(`Saved creds for session ${sessionId}`);
    } catch (err) {
      logger.error(`Failed to save creds for session ${sessionId}: ${err.message}`);
    }
  }

  function scheduleKeySync() {
    if (keyUpdateTimeout) {
      clearTimeout(keyUpdateTimeout);
    }

    keyUpdateTimeout = setTimeout(async () => {
      const updates = { ...pendingKeyUpdates };
      pendingKeyUpdates = {};

      if (Object.keys(updates).length === 0) return;

      const setKeys = {};
      const deleteKeys = [];

      for (const [key, value] of Object.entries(updates)) {
        if (value === null) {
          deleteKeys.push(key);
        } else {
          setKeys[key] = value;
        }
      }

      try {
        await axios.patch(
          `${apiUrl}/api/v1/channel/whatsapp/auth/${sessionId}/keys`,
          { set_keys: setKeys, delete_keys: deleteKeys },
          { headers, timeout: 10000 }
        );
        logger.debug(`Synced ${Object.keys(setKeys).length} keys for session ${sessionId}`);
      } catch (err) {
        logger.error(`Failed to sync keys for session ${sessionId}: ${err.message}`);
        pendingKeyUpdates = { ...updates, ...pendingKeyUpdates };
      }
    }, 500);
  }

  const hasExisting = await loadAuth();

  if (!hasExisting || !credsCache) {
    credsCache = initAuthCreds();
    logger.info(`Initialized new auth creds for session ${sessionId}`);
  }

  const state = {
    creds: credsCache,
    keys: {
      get: async (type, ids) => {
        const result = {};
        for (const id of ids) {
          const key = `${type}:${id}`;
          let value = keysCache[key];

          if (value) {
            try {
              value = deserializeData(value);
              if (type === 'app-state-sync-key' && value) {
                value = proto.Message.AppStateSyncKeyData.fromObject(value);
              }
            } catch (e) {
              logger.warn(`Failed to deserialize key ${key}: ${e.message}`);
              value = null;
            }
          }

          result[id] = value || null;
        }
        return result;
      },
      set: async (data) => {
        for (const [type, entries] of Object.entries(data)) {
          for (const [id, value] of Object.entries(entries)) {
            const key = `${type}:${id}`;
            if (value === null || value === undefined) {
              delete keysCache[key];
              pendingKeyUpdates[key] = null;
            } else {
              const serialized = serializeData(value);
              keysCache[key] = serialized;
              pendingKeyUpdates[key] = serialized;
            }
          }
        }
        scheduleKeySync();
      },
    },
  };

  return { state, saveCreds };
}

/**
 * Delete stored auth for a session.
 */
export async function deleteDBAuth(sessionId) {
  try {
    await axios.delete(
      `${config.backendUrl}/api/v1/channel/whatsapp/auth/${sessionId}`,
      {
        headers: {
          'Content-Type': 'application/json',
          'X-API-Key': config.apiKey,
        },
        timeout: 10000,
      }
    );
    logger.info(`Deleted auth for session ${sessionId}`);
    return true;
  } catch (err) {
    logger.error(`Failed to delete auth for session ${sessionId}: ${err.message}`);
    return false;
  }
}
