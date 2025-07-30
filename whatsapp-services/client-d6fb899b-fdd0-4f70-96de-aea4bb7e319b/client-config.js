
// Client-specific configuration for Test MultiTenant
module.exports = {
    client: {
        id: 'd6fb899b-fdd0-4f70-96de-aea4bb7e319b',
        name: 'Test MultiTenant',
        email: 'test@multitenancy.com',
        openai_api_key: 'sk-test',
        openai_assistant_id: 'asst-test'
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
