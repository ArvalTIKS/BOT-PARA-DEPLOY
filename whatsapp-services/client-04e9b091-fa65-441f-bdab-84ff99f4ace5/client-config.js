
// Client-specific configuration for Gonzalo
module.exports = {
    client: {
        id: '04e9b091-fa65-441f-bdab-84ff99f4ace5',
        name: 'Gonzalo',
        email: 'crmtiks@gmail.com',
        openai_api_key: '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',
        openai_assistant_id: 'asst_JseDE8SFShgszYaPw4bZHZpu'
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
