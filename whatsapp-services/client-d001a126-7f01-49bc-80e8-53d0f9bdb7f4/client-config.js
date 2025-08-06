
// Client-specific configuration for Roberto
module.exports = {
    client: {
        id: 'd001a126-7f01-49bc-80e8-53d0f9bdb7f4',
        name: 'Roberto',
        email: 'arvalabogadosonline@gmail.com',
        openai_api_key: 'sk-test-roberto',
        openai_assistant_id: 'asst_test_roberto'
    },
    server: {
        host: '0.0.0.0',
        port: 3009,
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
