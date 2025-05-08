from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import datetime
import json
import random

# Try to import security modules, but continue if they're not available
try:
    from security import rate_limit, validate_review_input, sanitize_review_input
    from security_headers import configure_security_headers, get_cors_config
    security_modules_available = True
except ImportError as e:
    print(f"Warning: Security modules not fully available: {e}")
    security_modules_available = False
    # Define dummy functions to avoid errors
    def rate_limit(f):
        return f
    def validate_review_input(data):
        return []
    def sanitize_review_input(data):
        return data

app = Flask(__name__)

# Apply security headers if available
if security_modules_available:
    try:
        configure_security_headers(app)
        # Configure CORS using secure configuration
        CORS(app, **get_cors_config())
    except Exception as e:
        print(f"Warning: Could not apply security configuration: {e}")
        # Fall back to basic CORS
        CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)
else:
    # Basic CORS configuration for development
    print("Using basic CORS configuration (security modules not available)")
    CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)

# In-memory fallback data in case Firebase connection fails
sample_reviews = [
    {
        "id": "1",
        "restaurant": "Delicious Bites",
        "rating": 5,
        "foodRating": 5,
        "serviceRating": 4,
        "ambianceRating": 5,
        "review": "Amazing food and atmosphere! The staff was very friendly and the dishes were incredibly flavorful.",
        "photoUrl": None,
        "userId": "user1",
        "userName": "John Smith",
        "location": {"latitude": 37.7749, "longitude": -122.4194},
        "timestamp": datetime.datetime.now().isoformat()
    },
    {
        "id": "2",
        "restaurant": "Golden Dragon",
        "rating": 4,
        "foodRating": 4,
        "serviceRating": 3,
        "ambianceRating": 4,
        "review": "Authentic Chinese cuisine with great flavor. Service was a bit slow but the food made up for it.",
        "photoUrl": None,
        "userId": "user2",
        "userName": "Emily Johnson",
        "location": {"latitude": 37.7833, "longitude": -122.4167},
        "timestamp": (datetime.datetime.now() - datetime.timedelta(days=1)).isoformat()
    },
    {
        "id": "3",
        "restaurant": "Pasta Paradise",
        "rating": 5,
        "foodRating": 5,
        "serviceRating": 5,
        "ambianceRating": 4,
        "review": "Best Italian food in town! The homemade pasta was exceptional and the service was top-notch.",
        "photoUrl": None,
        "userId": "user3",
        "userName": "Michael Brown",
        "location": {"latitude": 37.7900, "longitude": -122.4000},
        "timestamp": (datetime.datetime.now() - datetime.timedelta(days=2)).isoformat()
    }
]

sample_users = {
    "user1": {
        "name": "John Smith",
        "email": "john@example.com",
        "favorites": ["2"],
        "reviewCount": 1,
        "createdAt": (datetime.datetime.now() - datetime.timedelta(days=10)).isoformat()
    },
    "user2": {
        "name": "Emily Johnson",
        "email": "emily@example.com",
        "favorites": ["1", "3"],
        "reviewCount": 1,
        "createdAt": (datetime.datetime.now() - datetime.timedelta(days=15)).isoformat()
    },
    "user3": {
        "name": "Michael Brown",
        "email": "michael@example.com",
        "favorites": [],
        "reviewCount": 1,
        "createdAt": (datetime.datetime.now() - datetime.timedelta(days=20)).isoformat()
    }
}

# Try to initialize Firebase
firebase_enabled = False
db = None

try:
    import firebase_admin
    from firebase_admin import credentials, firestore, auth
    
    # Try to load credentials from file
    try:
        cred = credentials.Certificate('./firebase-credentials.json')
        firebase_admin.initialize_app(cred)
        db = firestore.client()
        firebase_enabled = True
        print("Firebase initialized successfully")
    except Exception as e:
        print(f"Firebase initialization error: {e}")
        print("Using sample data as fallback")
except ImportError:
    print("Firebase admin SDK not available, using sample data")

# Authentication middleware
def get_user_from_token(token):
    if not firebase_enabled:
        # For demo, allow any token and use a demo user
        return {"uid": "demo_user", "name": "Demo User"}
        
    try:
        # Verify and decode the token with full check_revoked option
        decoded_token = auth.verify_id_token(token, check_revoked=True)
        
        # Check if token is expired (Firebase does this but adding extra check)
        now = datetime.datetime.now()
        exp = datetime.datetime.fromtimestamp(decoded_token.get('exp', 0))
        
        if now > exp:
            print("Token expired")
            return None
            
        return decoded_token
    except auth.ExpiredIdTokenError:
        print("Firebase token expired")
        return None
    except auth.RevokedIdTokenError:
        print("Firebase token revoked")
        return None
    except auth.InvalidIdTokenError:
        print("Firebase token invalid")
        return None
    except Exception as e:
        print(f"Token verification error: {e}")
        return None

# Convert Firestore timestamps to string when needed
def convert_timestamps(obj):
    if isinstance(obj, dict):
        for key, value in obj.items():
            # Check if it's a Firestore timestamp
            if hasattr(value, 'seconds') and hasattr(value, 'nanoseconds'):
                # Convert Firestore timestamp to datetime then to ISO format
                obj[key] = datetime.datetime.fromtimestamp(value.seconds + value.nanoseconds / 1e9).isoformat()
            elif isinstance(value, dict):
                convert_timestamps(value)
            elif isinstance(value, list):
                for item in value:
                    if isinstance(item, dict):
                        convert_timestamps(item)
    return obj

# Safe timestamp parsing for comparison
def safe_timestamp_to_datetime(timestamp):
    """Convert different timestamp formats to datetime for safe comparison"""
    if timestamp is None:
        return datetime.datetime.min.replace(tzinfo=None)
        
    # If it's already a datetime
    if isinstance(timestamp, datetime.datetime):
        # Ensure it's timezone-naive for comparison
        if timestamp.tzinfo is not None:
            timestamp = timestamp.replace(tzinfo=None)
        return timestamp
        
    # If it's a Firestore timestamp
    if hasattr(timestamp, 'seconds') and hasattr(timestamp, 'nanoseconds'):
        # Convert to timezone-naive datetime
        return datetime.datetime.fromtimestamp(timestamp.seconds + timestamp.nanoseconds / 1e9).replace(tzinfo=None)
        
    # If it's an ISO format string
    if isinstance(timestamp, str):
        try:
            # Try standard ISO format, ensure timezone-naive
            dt = datetime.datetime.fromisoformat(timestamp)
            if dt.tzinfo is not None:
                dt = dt.replace(tzinfo=None)
            return dt
        except ValueError:
            try:
                # Try with more flexible parsing
                dt = datetime.datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%S.%fZ")
                return dt.replace(tzinfo=None)
            except ValueError:
                try:
                    # Try without microseconds
                    dt = datetime.datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%SZ")
                    return dt.replace(tzinfo=None)
                except ValueError:
                    try:
                        # Try just date
                        dt = datetime.datetime.strptime(timestamp, "%Y-%m-%d")
                        return dt.replace(tzinfo=None)
                    except ValueError:
                        # Return minimum date as fallback
                        return datetime.datetime.min.replace(tzinfo=None)
    
    # Fallback
    return datetime.datetime.min.replace(tzinfo=None)

# Helper function for safe timestamp sorting
def sort_by_timestamp(items, reverse=True):
    """Sort items by timestamp safely handling different timestamp formats"""
    return sorted(items, key=lambda x: safe_timestamp_to_datetime(x.get('timestamp')), reverse=reverse)

# Reviews endpoints
@app.route('/api/reviews', methods=['GET'])
# Temporarily disable rate limiting for debugging
# @rate_limit
def get_reviews():
    try:
        print("Fetching reviews...")
        
        # Query parameters for filtering
        restaurant = request.args.get('restaurant')
        sort_by = request.args.get('sortBy', 'timestamp')
        order = request.args.get('order', 'desc')
        min_rating = request.args.get('minRating')
        user_id = request.args.get('userId')
        
        # If Firebase is enabled and available, get data from it
        if firebase_enabled and db is not None:
            try:
                print("Fetching reviews from Firebase...")
                # Build the query
                query = db.collection('reviews')
                
                # Apply filters
                if restaurant:
                    query = query.where('restaurant', '==', restaurant)
                
                if min_rating:
                    query = query.where('rating', '>=', int(min_rating))
                
                if user_id:
                    query = query.where('userId', '==', user_id)
                
                # Execute query
                results = query.get()
                    
                # Convert to list and format
                reviews = []
                for doc in results:
                    review_data = doc.to_dict()
                    review_data['id'] = doc.id
                    reviews.append(review_data)
                
                # Sort results
                if sort_by == 'rating':
                    reverse = order == 'desc'
                    reviews = sorted(reviews, key=lambda x: x.get('rating', 0), reverse=reverse)
                elif sort_by == 'timestamp':
                    reverse = order == 'desc'
                    reviews = sort_by_timestamp(reviews, reverse=reverse)
                
                # Now convert timestamps to strings for JSON serialization
                reviews = [convert_timestamps(review) for review in reviews]
                
                print(f"Found {len(reviews)} reviews in Firebase")
                return jsonify(reviews)
            except Exception as e:
                print(f"Error fetching from Firebase: {e}")
                print("Falling back to sample data")
                # Fall back to sample data on error
        
        # Use sample data as fallback
        print("Using sample reviews data")
        filtered_reviews = sample_reviews.copy()
        
        # Apply filters to sample data
        if restaurant:
            filtered_reviews = [r for r in filtered_reviews if r.get('restaurant') == restaurant]
        
        if min_rating:
            filtered_reviews = [r for r in filtered_reviews if r.get('rating', 0) >= int(min_rating)]
            
        if user_id:
            filtered_reviews = [r for r in filtered_reviews if r.get('userId') == user_id]
        
        # Sort the results
        if sort_by == 'rating':
            reverse = order == 'desc'
            filtered_reviews = sorted(filtered_reviews, key=lambda x: x.get('rating', 0), reverse=reverse)
        else:  # Default to timestamp
            reverse = order == 'desc'
            filtered_reviews = sorted(filtered_reviews, 
                                     key=lambda x: safe_timestamp_to_datetime(x.get('timestamp')), 
                                     reverse=reverse)
            
        return jsonify(filtered_reviews)
    except Exception as e:
        print(f"Error getting reviews: {e}")
        # Return sample data on error
        return jsonify(sample_reviews)

@app.route('/api/trending', methods=['GET'])
# Temporarily disable rate limiting for debugging
# @rate_limit
def get_trending():
    try:
        print("Fetching trending data...")
        
        # If Firebase is enabled and available, get data from it
        if firebase_enabled and db is not None:
            try:
                print("Fetching trending data from Firebase...")
                # Get all reviews
                reviews_ref = db.collection('reviews').limit(50).get()
                reviews = []
                
                for doc in reviews_ref:
                    review_data = doc.to_dict()
                    review_data['id'] = doc.id
                    reviews.append(review_data)
                
                # Get top restaurants by average rating
                restaurant_ratings = {}
                for review in reviews:
                    restaurant = review.get('restaurant')
                    if not restaurant:
                        continue
                        
                    if restaurant not in restaurant_ratings:
                        restaurant_ratings[restaurant] = {
                            'totalRating': 0,
                            'count': 0,
                            'photos': [],
                            'latestReview': None
                        }
                    
                    restaurant_ratings[restaurant]['totalRating'] += review.get('rating', 0)
                    restaurant_ratings[restaurant]['count'] += 1
                    
                    # Track photos
                    if review.get('photoUrl'):
                        restaurant_ratings[restaurant]['photos'].append(review.get('photoUrl'))
                    
                    # Track latest review - using safe timestamp comparison
                    if restaurant_ratings[restaurant]['latestReview'] is None:
                        restaurant_ratings[restaurant]['latestReview'] = review
                    else:
                        current_timestamp = safe_timestamp_to_datetime(restaurant_ratings[restaurant]['latestReview'].get('timestamp'))
                        new_timestamp = safe_timestamp_to_datetime(review.get('timestamp'))
                        
                        if new_timestamp > current_timestamp:
                            restaurant_ratings[restaurant]['latestReview'] = review
                
                # Format top restaurants
                top_restaurants = []
                for restaurant, data in restaurant_ratings.items():
                    if data['count'] > 0:
                        avg_rating = data['totalRating'] / data['count']
                        
                        top_restaurants.append({
                            'restaurant': restaurant,  # Use consistent naming
                            'avgRating': round(avg_rating, 1),
                            'reviewCount': data['count'],
                            'latestReview': convert_timestamps(data['latestReview']) if data['latestReview'] else None,
                            'photos': data['photos'][:3]  # Limit to 3 photos
                        })
                
                # Sort by average rating
                top_restaurants.sort(key=lambda x: x['avgRating'], reverse=True)
                
                # Get recent activity - using our safe sorting function
                sorted_reviews = sort_by_timestamp(reviews, reverse=True)
                recent_activity = []
                
                for review in sorted_reviews[:5]:
                    converted_review = convert_timestamps(review)  # Convert timestamps now
                    recent_activity.append(converted_review)
                
                print(f"Found {len(top_restaurants)} top restaurants and {len(recent_activity)} recent activities")
                return jsonify({
                    'topRestaurants': top_restaurants[:5],
                    'recentActivity': recent_activity
                })
            except Exception as e:
                print(f"Error fetching trending from Firebase: {e}")
                print("Falling back to sample data")
                # Fall back to sample data on error
        
        # Generate trending data from sample reviews
        print("Using sample data for trending")
        top_restaurants = []
        restaurant_names = set(review['restaurant'] for review in sample_reviews)
        
        for restaurant in restaurant_names:
            restaurant_reviews = [r for r in sample_reviews if r['restaurant'] == restaurant]
            avg_rating = sum(r['rating'] for r in restaurant_reviews) / len(restaurant_reviews)
            top_restaurants.append({
                "restaurant": restaurant,
                "avgRating": round(avg_rating, 1),
                "reviewCount": len(restaurant_reviews),
                "lastReviewDate": max(safe_timestamp_to_datetime(r.get('timestamp')) for r in restaurant_reviews).isoformat()
            })
        
        # Sort by average rating (descending)
        top_restaurants = sorted(top_restaurants, key=lambda x: x['avgRating'], reverse=True)
        
        # Get recent activity
        recent_reviews = sorted(
            sample_reviews, 
            key=lambda x: safe_timestamp_to_datetime(x.get('timestamp')), 
            reverse=True
        )[:5]
        
        trending_data = {
            "topRestaurants": top_restaurants,
            "recentActivity": recent_reviews
        }
        
        return jsonify(trending_data)
    except Exception as e:
        print(f"Error getting trending data: {e}")
        # Return empty data on error
        return jsonify({"topRestaurants": [], "recentActivity": []})

@app.route('/api/reviews', methods=['POST'])
# @rate_limit
def create_review():
    try:
        # Get JSON data
        review_data = request.get_json()
        print(f"Received review data: {review_data}")
        
        # Validate input but show detailed validation errors
        validation_errors = validate_review_input(review_data)
        if validation_errors:
            print(f"Validation errors: {validation_errors}")
            return jsonify({"errors": validation_errors}), 400
            
        # Sanitize input to prevent XSS
        review_data = sanitize_review_input(review_data)
        
        # If Firebase is not enabled, add to sample data
        if not firebase_enabled or db is None:
            # Generate a unique ID
            new_id = str(len(sample_reviews) + 1)
            
            # Set timestamp and ID if not already set
            review_data['timestamp'] = review_data.get('timestamp') or datetime.datetime.now().isoformat()
            review_data['id'] = new_id
            
            # Add to sample data - make a copy to avoid modifying the original
            sample_reviews.append(review_data.copy())
            
            # Update user review count
            user_id = review_data.get('userId')
            if user_id in sample_users:
                sample_users[user_id]['reviewCount'] = sample_users[user_id].get('reviewCount', 0) + 1
            
            return jsonify(review_data), 201
        
        # If Firebase is enabled
        # Add current timestamp
        review_data['timestamp'] = firestore.SERVER_TIMESTAMP
        
        # Add to Firestore
        review_ref = db.collection('reviews').document()
        review_ref.set(review_data)
        
        # Get the document with the generated ID
        review_doc = review_ref.get()
        review_with_id = review_doc.to_dict()
        review_with_id['id'] = review_doc.id
        
        # Update user's review count
        user_id = review_data.get('userId')
        if user_id:
            user_ref = db.collection('users').document(user_id)
            user_doc = user_ref.get()
            
            if user_doc.exists:
                # Update review count
                user_ref.update({
                    'reviewCount': firestore.Increment(1)
                })
        
        # Return the created review
        return jsonify(convert_timestamps(review_with_id)), 201
    except Exception as e:
        print(f"Error creating review: {e}")
        return jsonify({"error": "Failed to create review"}), 500

# Add a simple test endpoint to check if the server is running
@app.route('/api/test', methods=['GET'])
def test_endpoint():
    """Simple endpoint to test if the API is working"""
    return jsonify({
        'status': 'ok',
        'message': 'API server is running',
        'timestamp': datetime.datetime.now().isoformat()
    })

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'ok',
        'message': 'Server is running',
        'firebase_enabled': firebase_enabled
    })

if __name__ == '__main__':
    # Print information about the server
    print(f"Starting server on port {os.environ.get('PORT', 5001)}")
    print(f"Firebase enabled: {firebase_enabled}")
    # Use 0.0.0.0 to make it accessible from other devices/Docker
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5001)), debug=True) 