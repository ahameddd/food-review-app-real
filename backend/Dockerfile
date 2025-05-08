# Python backend
FROM python:3.10-slim

WORKDIR /app

# Copy requirements file
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt
# Ensure flask-talisman is installed
RUN pip install --no-cache-dir flask-talisman==1.0.0

# Copy application files
COPY . .

# Environment variables
ENV PORT=5001
ENV FLASK_APP=server.py
ENV PYTHONUNBUFFERED=1

# Expose API port
EXPOSE 5001

# Start the server
CMD ["python", "server.py"]