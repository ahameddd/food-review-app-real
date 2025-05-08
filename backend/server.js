const express = require('express');
const cors = require('cors');
const admin = require('firebase-admin');
const multer = require('multer');
const { v4: uuidv4 } = require('uuid');
const path = require('path');

const app = express();
const port = 5001;

// Initialize Firebase
const serviceAccount = require('./firebase-credentials.json');
admin.initializeApp({
  credential: admin.credential.cert(serviceAccount),
  storageBucket: "restaurant-reviews-7e260.firebasestorage.app"
});

const db = admin.firestore();
const bucket = admin.storage().bucket();

// Configure multer for file uploads
const storage = multer.memoryStorage();
const upload = multer({ 
  storage: storage,
  limits: { fileSize: 5 * 1024 * 1024 }, // 5MB limit
  fileFilter: (req, file, cb) => {
    if (file.mimetype.startsWith('image/')) {
      cb(null, true);
    } else {
      cb(new Error('Only images are allowed'));
    }
  }
});

// Middleware
app.use(cors());
app.use(express.json());

// Auth middlewares
const authMiddleware = async (req, res, next) => {
  try {
    const authHeader = req.headers.authorization;
    if (!authHeader || !authHeader.startsWith('Bearer ')) {
      return res.status(401).json({ error: 'Unauthorized - No token provided' });
    }

    const token = authHeader.split('Bearer ')[1];
    const decodedToken = await admin.auth().verifyIdToken(token);
    req.user = decodedToken;
    next();
  } catch (error) {
    console.error('Auth error:', error);
    return res.status(401).json({ error: 'Unauthorized - Invalid token' });
  }
};

// API endpoints

// Health check endpoint
app.get('/api/health', (req, res) => {
  res.json({ status: 'ok', message: 'Server is running' });
});

// Reviews endpoints
app.get('/api/reviews', async (req, res) => {
  try {
    // Query parameters for filtering
    const { restaurant, sortBy, order, minRating, userId } = req.query;
    
    let query = db.collection('reviews');
    
    // Apply filters
    if (restaurant) {
      query = query.where('restaurant', '==', restaurant);
    }
    
    if (minRating) {
      query = query.where('rating', '>=', parseInt(minRating));
    }
    
    if (userId) {
      query = query.where('userId', '==', userId);
    }
    
    // Get the documents
    let snapshot = await query.get();
    let reviews = [];
    
    snapshot.forEach(doc => {
      reviews.push({
        id: doc.id,
        ...doc.data()
      });
    });
    
    // Sort results
    if (sortBy) {
      reviews.sort((a, b) => {
        if (order === 'desc') {
          return b[sortBy] - a[sortBy];
        }
        return a[sortBy] - b[sortBy];
      });
    } else {
      // Default sort by timestamp desc
      reviews.sort((a, b) => {
        const dateA = a.timestamp instanceof admin.firestore.Timestamp ? 
          a.timestamp.toDate() : new Date(a.timestamp);
        const dateB = b.timestamp instanceof admin.firestore.Timestamp ? 
          b.timestamp.toDate() : new Date(b.timestamp);
        return dateB - dateA;
      });
    }
    
    res.json(reviews);
  } catch (error) {
    console.error('Error getting reviews:', error);
    res.status(500).json({ error: 'Failed to retrieve reviews' });
  }
});

app.get('/api/reviews/:id', async (req, res) => {
  try {
    const docRef = await db.collection('reviews').doc(req.params.id).get();
    
    if (!docRef.exists) {
      return res.status(404).json({ error: 'Review not found' });
    }
    
    res.json({
      id: docRef.id,
      ...docRef.data()
    });
  } catch (error) {
    console.error('Error getting review:', error);
    res.status(500).json({ error: 'Failed to retrieve review' });
  }
});

app.post('/api/reviews', upload.single('photo'), async (req, res) => {
  try {
    const reviewData = JSON.parse(req.body.reviewData);
    let photoUrl = null;
    
    // Upload image if provided
    if (req.file) {
      const fileName = `${uuidv4()}-${req.file.originalname}`;
      const fileUpload = bucket.file(fileName);
      
      await fileUpload.save(req.file.buffer, {
        metadata: {
          contentType: req.file.mimetype
        }
      });
      
      // Make the file publicly accessible
      await fileUpload.makePublic();
      
      photoUrl = `https://storage.googleapis.com/${bucket.name}/${fileName}`;
    }
    
    // Create the review document with detailed ratings
    const review = {
      restaurant: reviewData.restaurant,
      rating: parseInt(reviewData.rating),
      // Detailed category ratings
      foodRating: parseInt(reviewData.foodRating) || 0,
      serviceRating: parseInt(reviewData.serviceRating) || 0,
      ambianceRating: parseInt(reviewData.ambianceRating) || 0,
      review: reviewData.review,
      photoUrl: photoUrl,
      userId: reviewData.userId || 'anonymous',
      userName: reviewData.userName || 'Anonymous User',
      location: reviewData.location || null,
      timestamp: admin.firestore.FieldValue.serverTimestamp()
    };
    
    const docRef = await db.collection('reviews').add(review);
    
    // Update the user's review count
    if (review.userId !== 'anonymous') {
      const userRef = db.collection('users').doc(review.userId);
      const userDoc = await userRef.get();
      
      if (userDoc.exists) {
        await userRef.update({
          reviewCount: admin.firestore.FieldValue.increment(1)
        });
      }
    }
    
    const savedReview = await docRef.get();
    
    res.status(201).json({
      id: docRef.id,
      ...savedReview.data(),
      timestamp: review.timestamp
    });
  } catch (error) {
    console.error('Error adding review:', error);
    res.status(500).json({ error: 'Failed to add review' });
  }
});

// Trending endpoints (formerly analytics)
app.get('/api/trending', async (req, res) => {
  try {
    const reviewsSnapshot = await db.collection('reviews').get();
    const reviews = [];
    
    reviewsSnapshot.forEach(doc => {
      reviews.push({
        id: doc.id,
        ...doc.data()
      });
    });
    
    // Get top restaurants by average rating (min 2 reviews)
    const restaurantRatings = {};
    reviews.forEach(review => {
      if (!restaurantRatings[review.restaurant]) {
        restaurantRatings[review.restaurant] = {
          totalRating: 0,
          count: 0,
          photos: [],
          latestReview: null
        };
      }
      restaurantRatings[review.restaurant].totalRating += review.rating;
      restaurantRatings[review.restaurant].count += 1;
      
      if (review.photoUrl) {
        restaurantRatings[review.restaurant].photos.push(review.photoUrl);
      }
      
      // Keep track of the latest review
      const reviewDate = review.timestamp instanceof admin.firestore.Timestamp ? 
        review.timestamp.toDate() : new Date(review.timestamp);
      
      if (!restaurantRatings[review.restaurant].latestReview || 
          (reviewDate > new Date(restaurantRatings[review.restaurant].latestReview.timestamp))) {
        restaurantRatings[review.restaurant].latestReview = {
          id: review.id,
          review: review.review,
          rating: review.rating,
          timestamp: reviewDate
        };
      }
    });
    
    const topRestaurants = Object.entries(restaurantRatings)
      .filter(([_, data]) => data.count >= 1) // Changed from 2 to 1 for demo purposes
      .map(([restaurant, data]) => ({
        restaurant,
        averageRating: data.totalRating / data.count,
        reviewCount: data.count,
        photoUrl: data.photos.length > 0 ? data.photos[0] : null,
        latestReview: data.latestReview
      }))
      .sort((a, b) => b.averageRating - a.averageRating)
      .slice(0, 6);
    
    // Recent activity
    const recentActivity = reviews
      .sort((a, b) => {
        const dateA = a.timestamp instanceof admin.firestore.Timestamp ? 
          a.timestamp.toDate() : new Date(a.timestamp);
        const dateB = b.timestamp instanceof admin.firestore.Timestamp ? 
          b.timestamp.toDate() : new Date(b.timestamp);
        return dateB - dateA;
      })
      .slice(0, 10)
      .map(review => ({
        id: review.id,
        restaurant: review.restaurant,
        userName: review.userName || 'Anonymous User',
        userId: review.userId,
        action: 'reviewed',
        rating: review.rating,
        review: review.review.substring(0, 100) + (review.review.length > 100 ? '...' : ''),
        photoUrl: review.photoUrl,
        timestamp: review.timestamp
      }));
    
    const trending = {
      topRestaurants,
      recentActivity
    };
    
    res.json(trending);
  } catch (error) {
    console.error('Error generating trending data:', error);
    res.status(500).json({ error: 'Failed to generate trending data' });
  }
});

// User profile and favorites endpoints
app.get('/api/users/:userId', async (req, res) => {
  try {
    const userId = req.params.userId;
    const userDoc = await db.collection('users').doc(userId).get();
    
    if (!userDoc.exists) {
      // If user doesn't exist in Firestore but is authenticated, create profile
      try {
        const authUser = await admin.auth().getUser(userId);
        if (authUser) {
          const newUser = {
            name: authUser.displayName || 'User',
            email: authUser.email,
            favorites: [],
            reviewCount: 0,
            createdAt: admin.firestore.FieldValue.serverTimestamp()
          };
          
          await db.collection('users').doc(userId).set(newUser);
          
          return res.json({
            id: userId,
            ...newUser
          });
        }
      } catch (err) {
        // Continue execution - will return 404 below
      }
      
      return res.status(404).json({ error: 'User not found' });
    }
    
    res.json({
      id: userDoc.id,
      ...userDoc.data()
    });
  } catch (error) {
    console.error('Error retrieving user:', error);
    res.status(500).json({ error: 'Failed to retrieve user data' });
  }
});

app.post('/api/users/:userId', authMiddleware, async (req, res) => {
  try {
    const { userId } = req.params;
    const userData = req.body;
    
    // Verify that the authenticated user is updating their own profile
    if (req.user.uid !== userId) {
      return res.status(403).json({ error: 'Forbidden: You can only update your own profile' });
    }
    
    // Remove any sensitive fields
    delete userData.email; // Email should be changed through Firebase Auth
    delete userData.reviewCount; // Should be updated automatically
    
    await db.collection('users').doc(userId).set(userData, { merge: true });
    
    res.status(200).json({ success: true });
  } catch (error) {
    console.error('Error updating user:', error);
    res.status(500).json({ error: 'Failed to update user data' });
  }
});

app.post('/api/users/:userId/favorites', async (req, res) => {
  try {
    const { userId } = req.params;
    const { reviewId } = req.body;
    
    await db.collection('users').doc(userId).set({
      favorites: admin.firestore.FieldValue.arrayUnion(reviewId)
    }, { merge: true });
    
    res.status(200).json({ success: true });
  } catch (error) {
    console.error('Error adding favorite:', error);
    res.status(500).json({ error: 'Failed to add favorite' });
  }
});

app.delete('/api/users/:userId/favorites/:reviewId', authMiddleware, async (req, res) => {
  try {
    const { userId, reviewId } = req.params;
    
    // Verify that the authenticated user is updating their own profile
    if (req.user.uid !== userId) {
      return res.status(403).json({ error: 'Forbidden: You can only update your own favorites' });
    }
    
    await db.collection('users').doc(userId).update({
      favorites: admin.firestore.FieldValue.arrayRemove(reviewId)
    });
    
    res.status(200).json({ success: true });
  } catch (error) {
    console.error('Error removing favorite:', error);
    res.status(500).json({ error: 'Failed to remove favorite' });
  }
});

// Search endpoint
app.get('/api/search', async (req, res) => {
  try {
    const { query } = req.query;
    
    if (!query) {
      return res.status(400).json({ error: 'Search query is required' });
    }
    
    // Simple search implementation (can be enhanced with a proper search engine)
    const reviewsSnapshot = await db.collection('reviews').get();
    const reviews = [];
    
    reviewsSnapshot.forEach(doc => {
      const data = doc.data();
      if (data.restaurant.toLowerCase().includes(query.toLowerCase()) || 
          data.review.toLowerCase().includes(query.toLowerCase())) {
        reviews.push({
          id: doc.id,
          ...data
        });
      }
    });
    
    res.json(reviews);
  } catch (error) {
    console.error('Error searching:', error);
    res.status(500).json({ error: 'Search failed' });
  }
});

// Start server
app.listen(port, () => {
  console.log(`Backend server running at http://localhost:${port}`);
}); 