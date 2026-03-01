/**
 * Configuration for VyapaarSetu Baileys WhatsApp Service
 */

export const config = {
  // Server
  port: process.env.PORT || 3001,

  // Backend base URL (Python FastAPI)
  backendUrl: process.env.BACKEND_URL || 'http://127.0.0.1:8000',

  // Backend webhook base URL
  backendWebhookUrl: process.env.BACKEND_WEBHOOK_URL || 'http://127.0.0.1:8000/api/v1/channel/whatsapp/webhook',

  // Sessions directory (legacy fallback)
  sessionsDir: process.env.SESSIONS_DIR || './sessions',

  // Use database for auth storage (recommended)
  useDBAuth: process.env.USE_DB_AUTH !== 'false',

  // API key for securing this service
  apiKey: process.env.API_KEY || 'baileys-secret-key',
};
