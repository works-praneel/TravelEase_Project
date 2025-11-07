FROM python:3.10-slim

WORKDIR /app

# Install dependencies first (faster builds)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all backend files into the container
COPY . .

EXPOSE 5010

ENV PYTHONUNBUFFERED=1

CMD ["python", "crowdpulse_app.py"]
