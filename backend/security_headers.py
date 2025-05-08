from flask_talisman import Talisman

def configure_security_headers(app):
    """Configure secure HTTP headers for the Flask application."""
    
    # Content Security Policy
    csp = {
        'default-src': "'self'",
        'script-src': ["'self'", "'unsafe-inline'", "https://storage.googleapis.com"],
        'style-src': ["'self'", "'unsafe-inline'", "https://fonts.googleapis.com"],
        'img-src': ["'self'", "data:", "https:", "http:"],
        'font-src': ["'self'", "https://fonts.gstatic.com"],
        'connect-src': ["'self'", "https://firebaseio.com", "https://*.googleapis.com", "*"],
        'frame-src': ["'self'", "https://firebaseapp.com"],
    }
    
    # Initialize Talisman with content_security_policy=None for development
    # In production, remove the content_security_policy=None to enable CSP
    talisman = Talisman(
        app,
        content_security_policy=None,  # Disable CSP in development
        content_security_policy_nonce_in=['script-src', 'style-src'],
        force_https=False,  # Don't force HTTPS in development
    )
    
    return talisman

def get_cors_config():
    """Return CORS configuration options."""
    return {
        'resources': {r"/*": {  # Allow all routes
            'origins': "*",  # Allow all origins in development
            'methods': ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            'allow_headers': ["Content-Type", "Authorization", "*"],
            'expose_headers': ["Content-Type", "X-Request-ID"],
            'supports_credentials': True,
            'max_age': 600,
            'vary_header': True
        }}
    } 