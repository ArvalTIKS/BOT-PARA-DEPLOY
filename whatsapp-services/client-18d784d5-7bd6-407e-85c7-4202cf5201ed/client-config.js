
// Client-specific configuration for test
module.exports = {
    client: {
        id: '18d784d5-7bd6-407e-85c7-4202cf5201ed',
        name: 'test',
        email: 'anni8sept@gmail.com',
        openai_api_key: 'sk-weiudbinef wfheifwf',
        openai_assistant_id: 'test'
    },
    server: {
        host: '0.0.0.0',
        port: 3006,
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
