
// Client-specific configuration for Gonzalo
module.exports = {
    client: {
        id: '0b060bf9-3f33-4dd4-bbb7-603dd6b48d60',
        name: 'Gonzalo',
        email: 'gonzalo@test.com',
        openai_api_key: 'sk-1234567890abcdef1234567890abcdef1234567890abcdef12',
        openai_assistant_id: 'asst_1234567890abcdef1234567890abcdef'
    },
    server: {
        host: '0.0.0.0',
        port: 3007,
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
