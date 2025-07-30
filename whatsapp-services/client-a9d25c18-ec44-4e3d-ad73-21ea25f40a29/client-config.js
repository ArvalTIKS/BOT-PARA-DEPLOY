
// Client-specific configuration for TIKS Negocios
module.exports = {
    client: {
        id: 'a9d25c18-ec44-4e3d-ad73-21ea25f40a29',
        name: 'TIKS Negocios',
        email: 'negocios@tiks.cl',
        openai_api_key: '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',
        openai_assistant_id: 'asst_J9ajHxmFap4F417bGuRWMGGq'
    },
    server: {
        host: '0.0.0.0',
        port: 3005,
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
