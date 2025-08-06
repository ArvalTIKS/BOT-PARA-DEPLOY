#!/usr/bin/env node
/**
 * ROBUST CHROMIUM SOLUTION SCRIPT
 * This script ensures Puppeteer is properly installed with bundled Chromium
 * It automatically installs Puppeteer if missing and verifies Chromium availability
 */

const fs = require('fs');
const { execSync } = require('child_process');
const path = require('path');

async function ensurePuppeteer(serviceDir) {
    console.log(`🔧 ROBUST CHROMIUM: Ensuring Puppeteer is ready in ${serviceDir}`);
    
    try {
        // Check if node_modules and puppeteer exist
        const nodeModulesPath = path.join(serviceDir, 'node_modules');
        const puppeteerPath = path.join(nodeModulesPath, 'puppeteer');
        
        if (!fs.existsSync(puppeteerPath)) {
            console.log('📦 Installing Puppeteer with bundled Chromium...');
            
            // Create package.json if it doesn't exist
            const packageJsonPath = path.join(serviceDir, 'package.json');
            if (!fs.existsSync(packageJsonPath)) {
                const packageJson = {
                    "name": "whatsapp-client-service",
                    "version": "1.0.0",
                    "main": "service.js",
                    "dependencies": {
                        "whatsapp-web.js": "^1.25.0",
                        "puppeteer": "^21.11.0",
                        "axios": "^1.6.0",
                        "cors": "^2.8.5", 
                        "express": "^4.18.2",
                        "qrcode": "^1.5.3"
                    }
                };
                fs.writeFileSync(packageJsonPath, JSON.stringify(packageJson, null, 2));
            }
            
            // Install with Chromium download enabled
            process.env.PUPPETEER_SKIP_CHROMIUM_DOWNLOAD = 'false';
            execSync('npm install', { 
                cwd: serviceDir, 
                stdio: 'inherit',
                env: { ...process.env, PUPPETEER_SKIP_CHROMIUM_DOWNLOAD: 'false' }
            });
        }
        
        // Verify Puppeteer and Chromium are working
        const puppeteer = require(path.join(puppeteerPath, 'index.js'));
        const chromiumPath = puppeteer.executablePath();
        
        if (!fs.existsSync(chromiumPath)) {
            throw new Error(`Bundled Chromium not found at: ${chromiumPath}`);
        }
        
        console.log(`✅ ROBUST CHROMIUM: Ready at ${chromiumPath}`);
        return chromiumPath;
        
    } catch (error) {
        console.error('❌ ROBUST CHROMIUM: Installation failed:', error.message);
        
        // Emergency fallback: Try to install just Puppeteer
        try {
            console.log('🔄 Attempting emergency Puppeteer installation...');
            execSync('npm install puppeteer@21.11.0', { 
                cwd: serviceDir, 
                stdio: 'inherit',
                env: { ...process.env, PUPPETEER_SKIP_CHROMIUM_DOWNLOAD: 'false' }
            });
            
            const puppeteer = require('puppeteer');
            const chromiumPath = puppeteer.executablePath();
            console.log(`✅ EMERGENCY INSTALL: Chromium ready at ${chromiumPath}`);
            return chromiumPath;
            
        } catch (emergencyError) {
            console.error('❌ EMERGENCY INSTALL FAILED:', emergencyError.message);
            throw new Error('Could not install Puppeteer with bundled Chromium');
        }
    }
}

// Export for use in other scripts
if (require.main === module) {
    // Called directly from command line
    const serviceDir = process.argv[2] || process.cwd();
    ensurePuppeteer(serviceDir)
        .then(() => process.exit(0))
        .catch(() => process.exit(1));
} else {
    // Required as module
    module.exports = { ensurePuppeteer };
}