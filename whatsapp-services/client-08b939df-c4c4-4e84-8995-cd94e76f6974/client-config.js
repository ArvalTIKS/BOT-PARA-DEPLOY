
// Client-specific configuration for Marketing Digital Pro
module.exports = {
    client: {
        id: '08b939df-c4c4-4e84-8995-cd94e76f6974',
        name: 'Marketing Digital Pro',
        email: 'crmtiks@gmail.com',
        openai_api_key: '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',
        openai_assistant_id: 'asst_7meiavwKWwXE8VctnSeTPTAF'
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
