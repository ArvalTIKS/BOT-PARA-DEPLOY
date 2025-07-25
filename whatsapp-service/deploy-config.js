// Deploy-specific configuration for WhatsApp Baileys service
// This file contains configurations optimized for production deployment

module.exports = {
    // Production environment detection
    isProduction: process.env.NODE_ENV === 'production' || process.env.EMERGENT_ENV === 'deploy',
    
    // WebSocket and connection settings optimized for deploy
    connection: {
        connectTimeoutMs: 180000, // 3 minutes for deploy
        keepAliveIntervalMs: 60000, // 1 minute keep-alive
        defaultQueryTimeoutMs: 30000, // 30 seconds for queries
        retryRequestDelayMs: 2000, // 2 seconds between retries
        maxMsgRetryCount: 5, // More retries in deploy
        requestTimeoutMs: 45000, // 45 seconds request timeout
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
        authDirectory: './baileys_auth_info',
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