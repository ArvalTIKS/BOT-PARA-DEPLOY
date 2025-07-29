
// Client-specific configuration for Cliente Email Test
module.exports = {
    client: {
        id: 'd7f3dddd-d288-4443-90eb-6becb12caffa',
        name: 'Cliente Email Test',
        email: 'nuevo@tikschile.com',
        openai_api_key: 'sk-test-email-key',
        openai_assistant_id: 'asst_email_test'
    },
    server: {
        host: '0.0.0.0',
        port: 3003,
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
        maxAttempts: 5,
        baseDelayMs: 15000,
        maxDelayMs: 120000,
        sessionRecoveryDelayMs: 30000
    }
};
