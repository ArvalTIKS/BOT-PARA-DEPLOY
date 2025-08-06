// Deploy-specific configuration for WhatsApp service
// This file contains configurations optimized for production deployment

module.exports = {
    // Production environment detection
    isProduction: process.env.NODE_ENV === 'production' || process.env.EMERGENT_ENV === 'deploy',
    
    // Puppeteer settings optimized for deploy
    puppeteer: {
        navigationTimeout: 120000, // 2 minutes for deploy
        pageLoadTimeout: 90000, // 90 seconds page load
        defaultTimeout: 60000, // 60 seconds default timeout
    },
    
    // Reconnection strategy for deploy
    reconnection: {
        maxAttempts: 5, // More attempts in deploy
        baseDelayMs: 15000, // 15 seconds base delay
        maxDelayMs: 120000, // 2 minutes max delay
        sessionRecoveryDelayMs: 30000, // 30 seconds for session recovery
    },
    
    // Session persistence settings
    session: {
        persistData: true, // Always persist in deploy
        authDirectory: './whatsapp_session',
        cleanupOnFailure: false, // Don't cleanup auth data in deploy
        backupAuthData: true, // Create backups in deploy
    },
    
    // Server settings for deploy
    server: {
        host: '0.0.0.0',
        port: process.env.PORT || 3001,
        gracefulShutdownTimeoutMs: 30000, // 30 seconds for graceful shutdown
    },
    
    // Logging configuration
    logging: {
        level: 'info', // More verbose logging in deploy
        enableConsoleLog: true,
        enableFileLog: false, // Supervisor handles file logging
    },
    
    // Performance optimizations for deploy
    performance: {
        enableCompression: true,
        maxConcurrentConnections: 100,
        messageQueueSize: 1000,
        processMessageBatchSize: 10,
    }
};