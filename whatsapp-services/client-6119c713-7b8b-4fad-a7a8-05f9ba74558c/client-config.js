
// Client-specific configuration for 97
module.exports = {
    client: {
        id: '6119c713-7b8b-4fad-a7a8-05f9ba74558c',
        name: '97',
        email: 'tikschile@gmail.com',
        openai_api_key: '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',
        openai_assistant_id: 'asst_QDJ31SyKI7uOVd58tSo38PEt'
    },
    server: {
        host: '0.0.0.0',
        port: 3001,
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
