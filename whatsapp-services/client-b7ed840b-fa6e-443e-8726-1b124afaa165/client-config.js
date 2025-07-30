
// Client-specific configuration for Estudio Jurídico Villegas
module.exports = {
    client: {
        id: 'b7ed840b-fa6e-443e-8726-1b124afaa165',
        name: 'Estudio Jurídico Villegas',
        email: 'brozech@gmail.com',
        openai_api_key: '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',
        openai_assistant_id: 'asst_NBxgKOlNULUyJR1UrqnwFsd4'
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
