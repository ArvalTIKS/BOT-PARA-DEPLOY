
// Client-specific configuration for Estudio Jurídico Villegas
module.exports = {
    client: {
        id: '441fc6e5-a564-4ba4-a302-64d388659170',
        name: 'Estudio Jurídico Villegas',
        email: 'villegas@example.com',
        openai_api_key: 'sk-test-key-1',
        openai_assistant_id: 'asst_test_1'
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
