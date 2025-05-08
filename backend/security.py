import time
import re
from functools import wraps
from flask import request, jsonify

# Simple in-memory rate limiter
class RateLimiter:
    def __init__(self, max_requests=100, time_window=60):
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests = {}
        
    def is_allowed(self, ip):
        current_time = time.time()
        # Clean up old entries
        self.requests = {k: v for k, v in self.requests.items() 
                         if current_time - v[-1] < self.time_window}
        
        # Check if IP exists and has request history
        if ip not in self.requests:
            self.requests[ip] = [current_time]
            return True
            
        # If requests within time window exceed limit
        if len(self.requests[ip]) >= self.max_requests:
            return False
            
        # Add this request timestamp
        self.requests[ip].append(current_time)
        return True

# Create rate limiter with 100 requests per minute
rate_limiter = RateLimiter(100, 60)

# Rate limiting decorator
def rate_limit(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        ip = request.remote_addr
        if not rate_limiter.is_allowed(ip):
            return jsonify({"error": "Rate limit exceeded"}), 429
        return f(*args, **kwargs)
    return decorated_function

# Input validation functions
def validate_review_input(data):
    errors = []
    
    if not data or not isinstance(data, dict):
        errors.append("Invalid or missing review data")
        return errors
    
    print(f"Validating review data: {data}")
    
    # Required fields
    required_fields = ['restaurant', 'rating', 'review', 'userId', 'userName']
    for field in required_fields:
        if field not in data or data[field] is None or data[field] == '':
            errors.append(f"Missing required field: {field}")
    
    # Type validation
    if 'rating' in data:
        try:
            rating = int(data['rating'])
            if rating < 1 or rating > 5:
                errors.append("Rating must be between 1 and 5")
        except (ValueError, TypeError):
            errors.append("Rating must be an integer")
    
    # String length validation
    if 'review' in data and data['review'] and len(data['review']) > 1000:
        errors.append("Review is too long (maximum 1000 characters)")
    
    if 'restaurant' in data and data['restaurant'] and len(data['restaurant']) > 100:
        errors.append("Restaurant name is too long (maximum 100 characters)")
    
    # Basic validation is enough during development
    # Skip XSS checks for now
    
    return errors

# Sanitize input to prevent XSS
def sanitize_string(input_str):
    if not isinstance(input_str, str):
        return input_str
        
    # Replace potentially dangerous characters
    sanitized = re.sub(r'<[^>]*>', '', input_str)  # Remove HTML tags
    sanitized = re.sub(r'javascript:', '', sanitized, flags=re.IGNORECASE)  # Remove javascript: protocol
    sanitized = re.sub(r'on\w+=', '', sanitized, flags=re.IGNORECASE)  # Remove event handlers
    
    return sanitized

def sanitize_review_input(data):
    sanitized_data = {}
    
    for key, value in data.items():
        if isinstance(value, str):
            sanitized_data[key] = sanitize_string(value)
        elif isinstance(value, dict):
            sanitized_data[key] = sanitize_review_input(value)
        elif isinstance(value, list):
            sanitized_data[key] = [sanitize_string(item) if isinstance(item, str) else item for item in value]
        else:
            sanitized_data[key] = value
            
    return sanitized_data 