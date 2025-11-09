FROM python:3.10-slim
WORKDIR /app
COPY . .

# Install all dependencies
RUN pip install --no-cache-dir flask flask-cors vaderSentiment google-api-python-client python-dotenv textblob prometheus-flask-exporter

# Pass YouTube API key from Jenkins
ARG YOUTUBE_API_KEY
ENV YOUTUBE_API_KEY=${YOUTUBE_API_KEY}

EXPOSE 5010
CMD ["python", "crowdpulse_app.py"]
