
// Client-specific configuration for Roberto Deploy Test
module.exports = {
    client: {
        id: '6e5e007a-25fa-485d-b61d-ef5fc6d04701',
        name: 'Roberto Deploy Test',
        email: 'roberto.deploy@gmail.com',
        openai_api_key: 'sk-test-roberto-deploy',
        openai_assistant_id: 'asst_test_roberto_deploy'
    },
    server: {
        host: '0.0.0.0',
        port: 3010,
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
