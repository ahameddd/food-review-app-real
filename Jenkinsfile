pipeline {
    agent any
    
    environment {
        DOCKER_IMAGE_FRONTEND = 'food-review-app/frontend'
        DOCKER_IMAGE_BACKEND = 'food-review-app/backend'
        DOCKER_TAG = "${env.BUILD_NUMBER}"
    }
    
    stages {
        stage('Build Frontend') {
            steps {
                dir('frontend') {
                    sh 'npm install'
                    sh 'npm run build'
                }
            }
        }
        
        stage('Build Backend') {
            steps {
                dir('backend') {
                    sh 'pip install -r requirements.txt'
                    sh 'pip install -r requirements-security.txt'
                }
            }
        }
        
        stage('Test') {
            steps {
                dir('backend') {
                    sh 'pip install pytest'
                    sh 'pytest'
                }
                // Frontend tests are not set up yet
                // dir('frontend') {
                //     sh 'npm test'
                // }
            }
        }
        
        stage('Security Scan') {
            steps {
                sh 'docker-compose run scan-frontend'
                sh 'docker-compose run scan-backend'
                sh 'python security-report.py'
            }
        }
        
        stage('Build Docker Images') {
            steps {
                sh "docker build -t ${DOCKER_IMAGE_FRONTEND}:${DOCKER_TAG} ./frontend"
                sh "docker build -t ${DOCKER_IMAGE_BACKEND}:${DOCKER_TAG} ./backend"
            }
        }
        
        stage('Deploy to Staging') {
            when {
                branch 'main'
            }
            steps {
                script {
                    // Deploy to staging environment
                    sh "docker-compose -f docker-compose.staging.yml up -d"
                }
            }
        }
        
        stage('Deploy to Production') {
            when {
                branch 'main'
                beforeAgent true
            }
            steps {
                timeout(time: 1, unit: 'HOURS') {
                    input message: 'Approve production deployment?'
                }
                script {
                    // Deploy to production environment
                    sh "docker-compose -f docker-compose.prod.yml up -d"
                }
            }
        }
    }
    
    post {
        always {
            // Clean up workspace
            cleanWs()
        }
        success {
            echo 'Pipeline completed successfully!'
        }
        failure {
            echo 'Pipeline failed!'
        }
    }
} 