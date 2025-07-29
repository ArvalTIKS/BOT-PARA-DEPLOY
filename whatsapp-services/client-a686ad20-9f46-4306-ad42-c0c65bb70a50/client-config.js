
// Client-specific configuration for Cliente Prueba
module.exports = {
    client: {
        id: 'a686ad20-9f46-4306-ad42-c0c65bb70a50',
        name: 'Cliente Prueba',
        email: 'test@example.com',
        openai_api_key: 'sk-test-key',
        openai_assistant_id: 'asst_test_id'
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
        maxAttempts: 5,
        baseDelayMs: 15000,
        maxDelayMs: 120000,
        sessionRecoveryDelayMs: 30000
    }
};
