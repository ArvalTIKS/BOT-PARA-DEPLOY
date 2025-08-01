
// Client-specific configuration for Consultorio Dr. Martinez
module.exports = {
    client: {
        id: '76d7e128-c577-46d0-bb06-0b45eb0939e9',
        name: 'Consultorio Dr. Martinez',
        email: 'martinez@example.com',
        openai_api_key: 'sk-test-key-2',
        openai_assistant_id: 'asst_test_2'
    },
    server: {
        host: '0.0.0.0',
        port: 3003,
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
