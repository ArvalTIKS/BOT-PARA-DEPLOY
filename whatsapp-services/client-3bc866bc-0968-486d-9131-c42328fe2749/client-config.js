
// Client-specific configuration for Cliente Test Escalabilidad
module.exports = {
    client: {
        id: '3bc866bc-0968-486d-9131-c42328fe2749',
        name: 'Cliente Test Escalabilidad',
        email: 'test@escalabilidad.com',
        openai_api_key: 'sk-test-escalabilidad',
        openai_assistant_id: 'asst_test_escalabilidad'
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
