"""
Robust URL detection for multiple Emergent deployment environments
Handles preview, deployment, and development environments with multiple fallbacks
"""
import os
import logging

# Configure logging
logger = logging.getLogger(__name__)

def get_backend_base_url():
    """
    Get the backend base URL with multiple fallbacks for different environments
    Priority order:
    1. DEPLOYMENT_URL (production deployment)
    2. PREVIEW_ENDPOINT (preview environment) 
    3. BASE_URL (configured base URL)
    4. Auto-detect from request headers (if available)
    5. Development fallback
    """
    
    # Priority 1: Production deployment URL
    deployment_url = os.environ.get('DEPLOYMENT_URL', '').strip()
    if deployment_url:
        logger.info(f"Using DEPLOYMENT_URL: {deployment_url}")
        return deployment_url
    
    # Priority 2: Preview environment URL  
    preview_endpoint = os.environ.get('PREVIEW_ENDPOINT', '').strip()
    if preview_endpoint:
        logger.info(f"Using PREVIEW_ENDPOINT: {preview_endpoint}")
        return preview_endpoint
        
    # Priority 3: Base URL fallback
    base_url = os.environ.get('BASE_URL', '').strip()
    if base_url:
        logger.info(f"Using BASE_URL: {base_url}")
        return base_url
    
    # Priority 4: Development fallback
    dev_url = "http://localhost:8001"
    logger.info(f"Using DEVELOPMENT fallback: {dev_url}")
    return dev_url

def get_frontend_base_url():
    """
    Get the frontend base URL for email links and redirects
    Same priority system as backend
    """
    
    # Priority 1: Production deployment URL
    deployment_url = os.environ.get('DEPLOYMENT_URL', '').strip()
    if deployment_url:
        logger.info(f"Frontend using DEPLOYMENT_URL: {deployment_url}")
        return deployment_url
    
    # Priority 2: Preview environment URL
    preview_endpoint = os.environ.get('PREVIEW_ENDPOINT', '').strip() 
    if preview_endpoint:
        logger.info(f"Frontend using PREVIEW_ENDPOINT: {preview_endpoint}")
        return preview_endpoint
        
    # Priority 3: Base URL fallback
    base_url = os.environ.get('BASE_URL', '').strip()
    if base_url:
        logger.info(f"Frontend using BASE_URL: {base_url}")
        return base_url
    
    # Priority 4: Development fallback  
    dev_url = "http://localhost:3000"
    logger.info(f"Frontend using DEVELOPMENT fallback: {dev_url}")
    return dev_url

def detect_environment():
    """
    Detect which environment we're running in based on URLs
    Returns: 'production', 'preview', or 'development'
    """
    
    deployment_url = os.environ.get('DEPLOYMENT_URL', '').strip()
    if deployment_url and '.emergent.host' in deployment_url:
        return 'production'
        
    preview_endpoint = os.environ.get('PREVIEW_ENDPOINT', '').strip()
    if preview_endpoint and '.preview.emergentagent.com' in preview_endpoint:
        return 'preview'
        
    base_url = os.environ.get('BASE_URL', '').strip()
    if base_url and ('emergent' in base_url):
        if '.emergent.host' in base_url:
            return 'production'
        elif '.preview.emergentagent.com' in base_url:
            return 'preview'
    
    return 'development'

def get_environment_info():
    """
    Get comprehensive environment information for debugging
    """
    env = detect_environment()
    backend_url = get_backend_base_url()
    frontend_url = get_frontend_base_url()
    
    return {
        'environment': env,
        'backend_url': backend_url,
        'frontend_url': frontend_url,
        'deployment_url': os.environ.get('DEPLOYMENT_URL', ''),
        'preview_endpoint': os.environ.get('PREVIEW_ENDPOINT', ''),
        'base_url': os.environ.get('BASE_URL', ''),
        'fallback_used': backend_url == "http://localhost:8001"
    }

# Initialize logging on import
logger.info("URL detection module loaded")
env_info = get_environment_info()
logger.info(f"Environment detected: {env_info}")