
// Client-specific configuration for Test Credenciales Reales
module.exports = {
    client: {
        id: 'db935610-381b-414e-991b-ac1ad0c63309',
        name: 'Test Credenciales Reales',
        email: 'test.credenciales@gmail.com',
        openai_api_key: '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',
        openai_assistant_id: 'asst_JseDE8SFShgszYaPw4bZHZpu'
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
