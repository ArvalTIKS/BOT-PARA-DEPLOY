
// Client-specific configuration for test
module.exports = {
    client: {
        id: 'd9de9a3d-c1c7-4380-b833-1d7735f6fdbc',
        name: 'test',
        email: 'anni8sept@gmail.com',
        openai_api_key: 'sk-jasbediadaoidaidnandaidn',
        openai_assistant_id: 'aindsiuandiandiandiad'
    },
    server: {
        host: '0.0.0.0',
        port: 3008,
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
