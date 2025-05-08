// Global variables
let currentUser = null;
let activeSection = 'home';

// Simple authentication system - no Firebase
async function initApp() {
  try {
    showSpinner();
    
    // Initialize UI components
    initNavigation();
    initStarRating();
    initFilterFunctionality();
    initSearchFunctionality();
    initLocationFeature();
    initPhotoPreview();
    initProfileTabs();
    initAuthUI();
    initReviewForm();
    
    // Test backend connection
    const backendAvailable = await testBackend();
    
    // Load initial data
    if (backendAvailable) {
      await Promise.all([
        loadReviews(),
        loadTrendingItems()
      ]);
    } else {
      document.getElementById('error-message').textContent = 'Backend server is not available. Please start the server and refresh the page.';
      document.getElementById('error-container').style.display = 'block';
    }
    
    // Register service worker for offline capabilities
    if ('serviceWorker' in navigator) {
      try {
        const registration = await navigator.serviceWorker.register('/service-worker.js');
        console.log('ServiceWorker registration successful with scope: ', registration.scope);
      } catch (error) {
        console.log('ServiceWorker registration failed: ', error);
      }
    }
    
    hideSpinner();
  } catch (error) {
    console.error('Error initializing app:', error);
    document.getElementById('error-message').textContent = `Error initializing app: ${error.message}`;
    document.getElementById('error-container').style.display = 'block';
    hideSpinner();
  }
}

// Navigation function
function initNavigation() {
  console.log("Initializing navigation");
  document.querySelectorAll('.nav-link').forEach(link => {
    link.addEventListener('click', (e) => {
      e.preventDefault();
      const targetSection = e.target.getAttribute('data-section');
      navigateTo(targetSection);
    });
  });
}

// Initialize star rating functionality
function initStarRating() {
  document.querySelectorAll('.rating-stars').forEach(container => {
    const stars = container.querySelectorAll('.star');
    const category = container.getAttribute('data-category');
    const input = document.querySelector(`.rating-input[data-category="${category}"]`);
    
    stars.forEach((star, index) => {
      star.addEventListener('click', () => {
        const rating = index + 1;
        // Set the hidden input value
        if (input) input.value = rating;
        
        // Update visual stars
        stars.forEach((s, i) => {
          if (i < rating) {
            s.classList.add('selected');
          } else {
            s.classList.remove('selected');
          }
        });
      });
    });
  });
}

// Initialize filter functionality
function initFilterFunctionality() {
  const sortFilter = document.getElementById('sortFilter');
  if (sortFilter) {
    sortFilter.addEventListener('change', () => {
      loadReviews({ sort: sortFilter.value });
    });
  }
}

// Initialize search functionality
function initSearchFunctionality() {
  const searchFilter = document.getElementById('searchFilter');
  if (searchFilter) {
    let timeoutId;
    searchFilter.addEventListener('input', (e) => {
      clearTimeout(timeoutId);
      timeoutId = setTimeout(() => {
        loadReviews({ search: e.target.value });
      }, 300); // Debounce search for 300ms
    });
  }
}

// Navigation function
function navigateTo(section) {
  console.log("Navigating to:", section);
  document.querySelectorAll('.section').forEach(s => {
    s.style.display = 'none';
  });
  
  const sectionElement = document.getElementById(`${section}Section`);
  if (sectionElement) {
    sectionElement.style.display = 'block';
  } else {
    console.error(`Section not found: ${section}Section`);
    return;
  }
  
  document.querySelectorAll('.nav-link').forEach(link => {
    link.classList.remove('active');
  });
  
  const navLink = document.querySelector(`.nav-link[data-section="${section}"]`);
  if (navLink) {
    navLink.classList.add('active');
  }
  
  activeSection = section;
  
  // Always load fresh data when navigating to these sections
  if (section === 'home') {
    loadTrending();
  } else if (section === 'reviews') {
    loadReviews();
  } else if (section === 'profile' && currentUser) {
    loadUserReviews();
  }
}

// Simplified authentication UI
function initAuthUI() {
  // Login form submission
  const loginForm = document.getElementById('loginForm');
  if (loginForm) {
    loginForm.addEventListener('submit', (e) => {
      e.preventDefault();
      const username = document.getElementById('loginUsername').value;
      if (username.trim()) {
        loginUser(username);
        navigateTo('home');
      } else {
        const errorDiv = document.getElementById('loginError');
        errorDiv.textContent = "Please enter a username";
        errorDiv.style.display = 'block';
      }
    });
  }
  
  // Signup form submission
  const signupForm = document.getElementById('signupForm');
  if (signupForm) {
    signupForm.addEventListener('submit', (e) => {
      e.preventDefault();
      const username = document.getElementById('signupUsername').value;
      if (username.trim()) {
        loginUser(username);
        navigateTo('home');
      } else {
        const errorDiv = document.getElementById('signupError');
        errorDiv.textContent = "Please enter a username";
        errorDiv.style.display = 'block';
      }
    });
  }
  
  // Logout
  const logoutBtn = document.getElementById('logoutBtn');
  if (logoutBtn) {
    logoutBtn.addEventListener('click', (e) => {
      e.preventDefault();
      logoutUser();
      navigateTo('home');
    });
  }
}

// Initialize profile tabs
function initProfileTabs() {
  const loginTab = document.getElementById('loginTab');
  const signupTab = document.getElementById('signupTab');
  const loginForm = document.getElementById('loginForm');
  const signupForm = document.getElementById('signupForm');
  
  if (loginTab && signupTab) {
    loginTab.addEventListener('click', (e) => {
      e.preventDefault();
      loginTab.classList.add('active');
      signupTab.classList.remove('active');
      loginForm.style.display = 'block';
      signupForm.style.display = 'none';
    });
    
    signupTab.addEventListener('click', (e) => {
      e.preventDefault();
      signupTab.classList.add('active');
      loginTab.classList.remove('active');
      signupForm.style.display = 'block';
      loginForm.style.display = 'none';
    });
  }
}

// Initialize review form
function initReviewForm() {
  const reviewForm = document.getElementById('reviewForm');
  if (reviewForm) {
    // Handle star ratings
    document.querySelectorAll('.rating-stars').forEach(container => {
      const stars = container.querySelectorAll('.star');
      const category = container.getAttribute('data-category');
      const input = document.querySelector(`.rating-input[data-category="${category}"]`);
      
      stars.forEach((star, index) => {
        star.addEventListener('click', () => {
          const rating = index + 1;
          // Set the hidden input value
          if (input) input.value = rating;
          
          // Update visual stars
          stars.forEach((s, i) => {
            if (i < rating) {
              s.classList.add('selected');
            } else {
              s.classList.remove('selected');
            }
          });
        });
      });
    });
    
    // Form submission
    reviewForm.addEventListener('submit', (e) => {
      e.preventDefault();
      if (!currentUser) {
        alert('Please sign in to submit a review');
        navigateTo('profile');
        return;
      }
      
      const formData = new FormData(reviewForm);
      const reviewData = {
        restaurant: formData.get('restaurant'),
        rating: parseInt(formData.get('rating') || 0),
        foodRating: parseInt(formData.get('foodRating') || 0),
        serviceRating: parseInt(formData.get('serviceRating') || 0),
        ambianceRating: parseInt(formData.get('ambianceRating') || 0),
        review: formData.get('review'),
        userName: currentUser.displayName
      };
      
      const photoInput = document.getElementById('photoInput');
      const photo = photoInput.files[0];
      
      submitReview(reviewData, photo);
    });
  }
}

// Initialize location feature
function initLocationFeature() {
  const getLocationBtn = document.getElementById('getLocationBtn');
  if (getLocationBtn) {
    getLocationBtn.addEventListener('click', (e) => {
      e.preventDefault();
      
      // Create hidden input fields if they don't exist
      let latInput = document.getElementById('latitudeInput');
      let lngInput = document.getElementById('longitudeInput');
      
      if (!latInput) {
        latInput = document.createElement('input');
        latInput.type = 'hidden';
        latInput.id = 'latitudeInput';
        latInput.name = 'latitude';
        document.getElementById('reviewForm').appendChild(latInput);
      }
      
      if (!lngInput) {
        lngInput = document.createElement('input');
        lngInput.type = 'hidden';
        lngInput.id = 'longitudeInput';
        lngInput.name = 'longitude';
        document.getElementById('reviewForm').appendChild(lngInput);
      }
      
      const locationStatus = document.getElementById('locationStatus');
      
      if (navigator.geolocation) {
        locationStatus.textContent = 'Getting your location...';
        locationStatus.classList.remove('error');
        locationStatus.classList.add('loading');
        
        navigator.geolocation.getCurrentPosition(
          (position) => {
            latInput.value = position.coords.latitude;
            lngInput.value = position.coords.longitude;
            locationStatus.textContent = '✓ Location added successfully';
            locationStatus.classList.remove('loading', 'error');
            locationStatus.classList.add('success');
            getLocationBtn.textContent = 'Update Location';
          },
          (error) => {
            console.error('Geolocation error:', error);
            locationStatus.textContent = `Error: ${error.message}`;
            locationStatus.classList.remove('loading', 'success');
            locationStatus.classList.add('error');
          }
        );
      } else {
        locationStatus.textContent = 'Geolocation is not supported by your browser';
        locationStatus.classList.remove('loading', 'success');
        locationStatus.classList.add('error');
      }
    });
  }
}

// Initialize photo preview
function initPhotoPreview() {
  const photoInput = document.getElementById('photoInput');
  const photoPreview = document.getElementById('photoPreview');
  
  if (photoInput && photoPreview) {
    photoInput.addEventListener('change', (e) => {
      const file = e.target.files[0];
      
      if (file) {
        const reader = new FileReader();
        reader.onload = (e) => {
          photoPreview.innerHTML = `<img src="${e.target.result}" alt="Preview">`;
          photoPreview.style.display = 'block';
        };
        reader.readAsDataURL(file);
      } else {
        photoPreview.innerHTML = '<p>No photo selected</p>';
        photoPreview.style.display = 'block';
      }
    });
  }
}

// Load reviews from API
function loadReviews(filters = {}) {
  const reviewsList = document.getElementById('reviewsList');
  if (!reviewsList) return;
  
  reviewsList.innerHTML = '<div class="loading">Loading reviews...</div>';
  
  const params = new URLSearchParams();
  for (const [key, value] of Object.entries(filters)) {
    if (value) params.append(key, value);
  }
  
  // Always add a timestamp parameter to prevent caching
  params.append('_t', Date.now());
  console.log('Loading reviews with params:', params.toString());
  
  // First try the test endpoint to see if the backend is available
  fetch('/api/test')
    .then(response => {
      if (!response.ok) {
        throw new Error(`Backend server not available: ${response.status}`);
      }
      return response.json();
    })
    .then(() => {
      // If test endpoint succeeds, get reviews
      console.log('Backend test succeeded, fetching reviews');
      return fetch(`/api/reviews?${params}`);
    })
    .then(response => {
      if (!response.ok) {
        throw new Error(`Error fetching reviews: ${response.status}`);
      }
      console.log('Reviews fetched successfully, parsing JSON');
      return response.json();
    })
    .then(reviews => {
      if (!Array.isArray(reviews)) {
        console.error('Invalid reviews response:', reviews);
        throw new Error('Invalid response from server');
      }
      
      console.log('Loaded reviews:', reviews);
      
      if (reviews.length === 0) {
        reviewsList.innerHTML = '<p>No reviews found</p>';
        return;
      }
      
      let html = '';
      reviews.forEach(review => {
        const date = new Date(review.timestamp).toLocaleDateString();
        const stars = '★'.repeat(review.rating) + '☆'.repeat(5 - review.rating);
        
        html += `
          <div class="review-card">
            <div class="review-header">
              <h3>${review.restaurant}</h3>
              <div class="rating">${stars}</div>
            </div>
            <p class="review-text">${review.review}</p>
            <div class="review-footer">
              <span class="review-author">By ${review.userName}</span>
              <span class="review-date">${date}</span>
            </div>
            ${review.photoUrl ? `<div class="review-photo"><img src="${review.photoUrl}" alt="Review photo"></div>` : ''}
          </div>
        `;
      });
      
      reviewsList.innerHTML = html;
      console.log(`Rendered ${reviews.length} reviews`);
    })
    .catch(error => {
      console.error('Error loading reviews:', error);
      reviewsList.innerHTML = `<div class="error">Error loading reviews: ${error.message}</div>`;
    });
}

// Load trending data from API
function loadTrending() {
  const trendingContainer = document.getElementById('trendingContainer');
  if (!trendingContainer) return;
  
  trendingContainer.innerHTML = '<div class="loading">Loading trending data...</div>';
  
  // Add a timestamp parameter to prevent caching
  const params = new URLSearchParams();
  params.append('_t', Date.now());
  
  // First try the test endpoint to see if the backend is available
  fetch('/api/test')
    .then(response => {
      if (!response.ok) {
        throw new Error(`Backend server not available: ${response.status}`);
      }
      return response.json();
    })
    .then(() => {
      // If test endpoint succeeds, get trending data
      return fetch(`/api/trending?${params}`);
    })
    .then(response => {
      if (!response.ok) {
        throw new Error(`Error fetching trending data: ${response.status}`);
      }
      return response.json();
    })
    .then(data => {
      if (!data || typeof data !== 'object') {
        console.error('Invalid trending data:', data);
        throw new Error('Invalid response from server');
      }
      
      let html = '<div class="trending-sections">';
      
      // Top restaurants
      html += '<div class="trending-section"><h3>Top Restaurants</h3>';
      if (data.topRestaurants && data.topRestaurants.length > 0) {
        html += '<div class="restaurant-cards">';
        data.topRestaurants.forEach(restaurant => {
          // Handle both naming conventions (API changed)
          const name = restaurant.name || restaurant.restaurant;
          const rating = restaurant.averageRating || restaurant.avgRating || 0;
          const stars = '★'.repeat(Math.round(rating)) + '☆'.repeat(5 - Math.round(rating));
          html += `
            <div class="restaurant-card">
              <h4>${name}</h4>
              <div class="rating">${stars}</div>
              <p>${restaurant.reviewCount} reviews</p>
            </div>
          `;
        });
        html += '</div>';
      } else {
        html += '<p>No top restaurants found</p>';
      }
      html += '</div>';
      
      // Recent activity
      html += '<div class="trending-section"><h3>Recent Activity</h3>';
      if (data.recentActivity && data.recentActivity.length > 0) {
        html += '<div class="activity-list">';
        data.recentActivity.forEach(activity => {
          const date = new Date(activity.timestamp).toLocaleDateString();
          const stars = '★'.repeat(activity.rating) + '☆'.repeat(5 - activity.rating);
          
          // Handle different API response formats
          const snippet = activity.snippet || activity.review?.substring(0, 100) + '...' || '';
          
          html += `
            <div class="activity-item">
              <div class="activity-header">
                <span>${activity.userName}</span> reviewed <span>${activity.restaurant}</span>
              </div>
              <div class="rating">${stars}</div>
              <p>${snippet}</p>
              <div class="activity-date">${date}</div>
            </div>
          `;
        });
        html += '</div>';
      } else {
        html += '<p>No recent activity</p>';
      }
      html += '</div>';
      
      html += '</div>';
      trendingContainer.innerHTML = html;
    })
    .catch(error => {
      console.error('Error loading trending data:', error);
      trendingContainer.innerHTML = `<div class="error">Error loading trending data: ${error.message}</div>`;
    });
}

// Alias for loadTrending to maintain compatibility
function loadTrendingItems() {
  return loadTrending();
}

// Login user
function loginUser(username) {
  currentUser = {
    uid: "user-" + Date.now(),
    displayName: username,
    username: username
  };
  localStorage.setItem('username', username);
  updateUIForSignedInUser();
}

// Logout user
function logoutUser() {
  currentUser = null;
  localStorage.removeItem('username');
  updateUIForSignedOutUser();
}

// UI updates based on authentication state
function updateUIForSignedInUser() {
  document.querySelectorAll('.auth-only').forEach(el => {
    el.style.display = 'block';
  });
  
  document.querySelectorAll('.guest-only').forEach(el => {
    el.style.display = 'none';
  });
  
  const userDisplayName = document.getElementById('userDisplayName');
  if (userDisplayName) {
    userDisplayName.textContent = currentUser.displayName;
  }
  
  const userInitial = document.getElementById('userInitial');
  if (userInitial) {
    userInitial.textContent = currentUser.displayName.charAt(0).toUpperCase();
  }

  // Load user's reviews when profile is shown
  if (activeSection === 'profile') {
    loadUserReviews();
  }
}

function updateUIForSignedOutUser() {
  document.querySelectorAll('.auth-only').forEach(el => {
    el.style.display = 'none';
  });
  
  document.querySelectorAll('.guest-only').forEach(el => {
    el.style.display = 'block';
  });
  
  if (activeSection === 'profile') {
    // Reset profile forms
    const loginTab = document.getElementById('loginTab');
    if (loginTab) loginTab.click();
    
    const loginUsername = document.getElementById('loginUsername');
    if (loginUsername) loginUsername.value = '';
    
    const signupUsername = document.getElementById('signupUsername');
    if (signupUsername) signupUsername.value = '';
    
    // Hide error messages
    const loginError = document.getElementById('loginError');
    if (loginError) loginError.style.display = 'none';
    
    const signupError = document.getElementById('signupError');
    if (signupError) signupError.style.display = 'none';
  }
}

// Load user's reviews
function loadUserReviews() {
  const userReviewsContainer = document.getElementById('userReviewsContainer');
  if (!userReviewsContainer || !currentUser) return;

  userReviewsContainer.innerHTML = '<div class="loading">Loading your reviews...</div>';

  // Add a timestamp parameter to prevent caching
  const params = new URLSearchParams();
  params.append('userId', currentUser.uid);
  params.append('_t', Date.now());

  fetch(`http://localhost:5001/api/reviews?${params}`)
    .then(response => {
      if (!response.ok) {
        throw new Error(`Error fetching user reviews: ${response.status}`);
      }
      return response.json();
    })
    .then(reviews => {
      if (!Array.isArray(reviews)) {
        throw new Error('Invalid response from server');
      }

      if (reviews.length === 0) {
        userReviewsContainer.innerHTML = '<p>You haven\'t written any reviews yet.</p>';
        return;
      }

      let html = '<div class="reviews-list">';
      reviews.forEach(review => {
        const date = new Date(review.timestamp).toLocaleDateString();
        const stars = '★'.repeat(review.rating) + '☆'.repeat(5 - review.rating);
        
        html += `
          <div class="review-card">
            <div class="review-header">
              <h3>${review.restaurant}</h3>
              <div class="rating">${stars}</div>
            </div>
            <p class="review-text">${review.review}</p>
            <div class="review-footer">
              <span class="review-date">${date}</span>
            </div>
            ${review.photoUrl ? `<div class="review-photo"><img src="${review.photoUrl}" alt="Review photo"></div>` : ''}
          </div>
        `;
      });
      html += '</div>';
      userReviewsContainer.innerHTML = html;
    })
    .catch(error => {
      console.error('Error loading user reviews:', error);
      userReviewsContainer.innerHTML = `<div class="error">Error loading your reviews: ${error.message}</div>`;
    });
}

// Review submission
function submitReview(reviewData, photoFile) {
  const submitBtn = document.querySelector('#reviewForm button[type="submit"]');
  const statusMessage = document.getElementById('reviewStatus');
  
  if (submitBtn) submitBtn.disabled = true;
  if (statusMessage) {
    statusMessage.textContent = 'Submitting your review...';
    statusMessage.className = 'status-message loading';
  }
  
  // Make sure we have all required fields to pass validation
  const completeReviewData = {
    restaurant: reviewData.restaurant || '',
    rating: parseInt(reviewData.rating) || 5,
    foodRating: parseInt(reviewData.foodRating) || 5,
    serviceRating: parseInt(reviewData.serviceRating) || 5,
    ambianceRating: parseInt(reviewData.ambianceRating) || 5,
    review: reviewData.review || '',
    userId: currentUser?.uid || 'anonymous',
    userName: currentUser?.displayName || 'Anonymous User',
    location: reviewData.location || null,
    photoUrl: null,
    timestamp: new Date().toISOString()
  };
  
  console.log('Submitting review data:', completeReviewData);
  
  // Submit to backend API
  fetch('http://localhost:5001/api/reviews', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(completeReviewData)
  })
  .then(response => {
    console.log('Review submission response status:', response.status);
    return response.text().then(text => {
      console.log('Response text:', text);
      try {
        const json = JSON.parse(text);
        if (!response.ok) {
          throw new Error(`Server error: ${response.status}${json.errors ? ' - ' + json.errors.join(', ') : ''}`);
        }
        return json;
      } catch (e) {
        console.error('Error parsing response as JSON:', e);
        if (!response.ok) {
          throw new Error(`Server error: ${response.status}`);
        }
        return { message: "Success (non-JSON response)" };
      }
    });
  })
  .then(data => {
    console.log('Review submitted successfully:', data);
    if (data.error) {
      throw new Error(data.error);
    }
    
    if (statusMessage) {
      statusMessage.textContent = 'Review submitted successfully!';
      statusMessage.className = 'status-message success';
    }
    
    // Reset form
    const reviewForm = document.getElementById('reviewForm');
    if (reviewForm) reviewForm.reset();
    
    // Reset photo preview
    const photoPreview = document.getElementById('photoPreview');
    if (photoPreview) photoPreview.innerHTML = '<p>No photo selected</p>';
    
    // Force refresh of the data after a delay
    console.log('Scheduling data refresh after submission...');
    setTimeout(refreshAllData, 1500);
    
    // Navigate to reviews page after the refresh
    setTimeout(() => {
      console.log('Navigating to reviews section');
      navigateTo('reviews');
    }, 2000);
  })
  .catch(error => {
    console.error('Error submitting review:', error);
    if (statusMessage) {
      statusMessage.textContent = `Error: ${error.message}`;
      statusMessage.className = 'status-message error';
    }
  })
  .finally(() => {
    if (submitBtn) submitBtn.disabled = false;
  });
}

// Function to refresh all data
function refreshAllData() {
  console.log('Refreshing all data with timestamp:', Date.now());
  loadReviews({_nocache: Date.now()});
  loadTrending({_nocache: Date.now()});
}

// Function to set up auto-refresh for reviews and trending
function setupAutoRefresh() {
  // Refresh data every 30 seconds
  setInterval(() => {
    // Only refresh if we're on the home or reviews page
    if (activeSection === 'home') {
      loadTrending();
    } else if (activeSection === 'reviews') {
      loadReviews();
    }
  }, 30000); // 30 seconds
}

// Initialize when the DOM content is loaded
document.addEventListener('DOMContentLoaded', () => {
  // Create error container if it doesn't exist
  if (!document.getElementById('error-container')) {
    const errorContainer = document.createElement('div');
    errorContainer.id = 'error-container';
    errorContainer.style.display = 'none';
    errorContainer.style.position = 'fixed';
    errorContainer.style.top = '10px';
    errorContainer.style.left = '50%';
    errorContainer.style.transform = 'translateX(-50%)';
    errorContainer.style.backgroundColor = '#ff5252';
    errorContainer.style.color = 'white';
    errorContainer.style.padding = '10px 20px';
    errorContainer.style.borderRadius = '4px';
    errorContainer.style.zIndex = '1000';
    
    const errorMessage = document.createElement('div');
    errorMessage.id = 'error-message';
    
    const closeButton = document.createElement('button');
    closeButton.textContent = '×';
    closeButton.style.marginLeft = '10px';
    closeButton.style.background = 'none';
    closeButton.style.border = 'none';
    closeButton.style.color = 'white';
    closeButton.style.fontSize = '18px';
    closeButton.style.cursor = 'pointer';
    closeButton.onclick = () => {
      errorContainer.style.display = 'none';
    };
    
    errorContainer.appendChild(errorMessage);
    errorContainer.appendChild(closeButton);
    document.body.appendChild(errorContainer);
  }
  
  initApp();
});

// Register service worker for offline functionality
if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/service-worker.js')
      .then(registration => {
        console.log('Service Worker registered with scope:', registration.scope);
      })
      .catch(error => {
        console.error('Service Worker registration failed:', error);
      });
  });
}

// Test backend server availability
async function testBackend() {
  try {
    const response = await fetch('http://localhost:5001/api/health', {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json'
      },
      timeout: 3000 // 3 second timeout
    });
    
    if (response.ok) {
      return true;
    } else {
      showError('Backend server returned an error: ' + response.status);
      return false;
    }
  } catch (error) {
    showError('Cannot connect to backend server. Please ensure it is running.');
    console.error('Backend connection error:', error);
    return false;
  }
}

// Display error message
function showError(message) {
  const errorContainer = document.getElementById('error-container');
  const errorMessage = document.getElementById('error-message');
  
  if (errorContainer && errorMessage) {
    errorMessage.textContent = message;
    errorContainer.style.display = 'flex';
    
    // Auto-hide after 5 seconds
    setTimeout(() => {
      errorContainer.style.display = 'none';
    }, 5000);
  } else {
    // Fallback to alert if error container not found
    alert(message);
  }
}

function showSpinner() {
  const spinner = document.getElementById('loadingSpinner');
  if (spinner) {
    spinner.style.display = 'flex';
  }
  
  const mainContent = document.getElementById('mainContent');
  if (mainContent) {
    mainContent.style.display = 'none';
  }
}

function hideSpinner() {
  const spinner = document.getElementById('loadingSpinner');
  if (spinner) {
    spinner.style.display = 'none';
  }
  
  const mainContent = document.getElementById('mainContent');
  if (mainContent) {
    mainContent.style.display = 'block';
  }
}