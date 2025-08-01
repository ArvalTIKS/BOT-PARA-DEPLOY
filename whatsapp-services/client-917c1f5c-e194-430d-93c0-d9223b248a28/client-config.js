
// Client-specific configuration for Cliente Prueba QR
module.exports = {
    client: {
        id: '917c1f5c-e194-430d-93c0-d9223b248a28',
        name: 'Cliente Prueba QR',
        email: 'prueba@test.com',
        openai_api_key: 'sk-test-key',
        openai_assistant_id: 'asst_test'
    },
    server: {
        host: '0.0.0.0',
        port: 3004,
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
