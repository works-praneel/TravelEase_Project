FROM python:3.10-slim

WORKDIR /app

# Copy backend files into the container
COPY . .

# Install dependencies
RUN pip install --no-cache-dir flask flask-cors vaderSentiment google-api-python-client python-dotenv textblob

# Expose port 5010 for the API
EXPOSE 5010

# Run the backend app
CMD ["python", "crowdpulse_app.py"]
