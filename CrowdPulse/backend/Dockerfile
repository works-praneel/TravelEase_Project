FROM python:3.10-slim

WORKDIR /app
COPY . .

# Inject YouTube API key securely via build argument from Jenkins
ARG YOUTUBE_API_KEY
ENV YOUTUBE_API_KEY=${YOUTUBE_API_KEY}

RUN pip install --no-cache-dir \
    flask \
    flask-cors \
    vaderSentiment \
    google-api-python-client \
    python-dotenv \
    textblob

EXPOSE 5010
CMD ["python", "crowdpulse_app.py"]
