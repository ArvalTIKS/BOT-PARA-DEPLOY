
// Client-specific configuration for Cliente Final Test
module.exports = {
    client: {
        id: 'ccabe071-33ac-4cdd-a9b5-9ea2440d6145',
        name: 'Cliente Final Test',
        email: 'final@test.com',
        openai_api_key: 'sk-final',
        openai_assistant_id: 'asst-final'
    },
    server: {
        host: '0.0.0.0',
        port: 3002,
        gracefulShutdownTimeoutMs: 30000
    },
    session: {
        authDirectory: './whatsapp_session',
        persistData: true,
        backupAuthData: true
    },
    puppeteer: {
        navigationTimeout: 120000,
        pageLoadTimeout: 90000,
        defaultTimeout: 60000
    },
    reconnection: {
        maxAttempts: 10,
        baseDelayMs: 20000,
        maxDelayMs: 120000,
        sessionRecoveryDelayMs: 30000
    }
};
