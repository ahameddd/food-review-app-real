<<<<<<< HEAD
# Restaurant Reviews App

This application allows users to review restaurants, browse and search existing reviews, and see trending restaurants based on user ratings.

## Features

- User authentication (username-based)
- Write and submit restaurant reviews with ratings, photos, and location
- View trending restaurants and recent review activity
- Search for restaurants and reviews
- User profiles with favorites and review history
- Modern, responsive UI design

## Running the Application

### With Docker (recommended)

```bash
# Build and start the containers
docker-compose up --build -d

# View logs
docker-compose logs -f

# Stop the containers
docker-compose down
```

The application will be available at http://localhost:80

### Without Docker

#### Backend

```bash
cd backend
pip install -r requirements.txt
python server.py
```

#### Frontend

```bash
cd frontend
# Any static file server will work, for example:
python -m http.server 80
```

## Security Scanning

The project includes Trivy for security scanning:

```bash
# Run security scan for frontend
docker-compose run scan-frontend

# Run security scan for backend
docker-compose run scan-backend

# Generate security report
python security-report.py
```

## Project Structure

```
restaurant-reviews/
├── backend/
│   ├── socket_server.py      # WebSocket server with sentiment analysis
│   └── api/                  # REST API endpoints
├── frontend/
│   ├── reviews-display/      # Reviews display page
│   ├── review-submission/    # Review submission page
│   └── analytics-dashboard/  # Analytics dashboard
├── reports/                  # Security scan reports
├── security/                 # Security tools
└── README.md
```

## Development

### Prerequisites

- Python 3.8+
- Node.js 14+
- Docker and Docker Compose
- Web browser with WebSocket support

### Backend Setup

1. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Start the WebSocket server:
   ```bash
   python backend/socket_server.py
   ```

### Frontend Setup

1. Start a local server:
   ```bash
   # Using Python's built-in server
   python -m http.server 8000
   ```

2. Access the application:
   - Reviews Display: http://localhost:8000/reviews-display
   - Review Submission: http://localhost:8000/review-submission
   - Analytics Dashboard: http://localhost:8000/analytics-dashboard

## Testing

Run the test suite:
```bash
pytest
```

## Code Quality

- Format code:
  ```bash
  black .
  ```
- Lint code:
  ```bash
  flake8
  ```

## Monitoring & Security

### Monitoring Tools

- Prometheus: Metrics collection
- Grafana: Visualization
- ELK Stack: Logging

### Security Tools

- SonarQube: Code quality and security
- OWASP ZAP: Security testing
- Trivy: Vulnerability scanning

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- NLTK for sentiment analysis
- Firebase for backend services
- Chart.js for data visualization
- D3.js for word cloud visualization 
=======
>>>>>>> 798c8ae (Initial Commit)
