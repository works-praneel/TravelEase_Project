FROM python:3.9-slim
WORKDIR /app
COPY . .

RUN pip install -r requirements.txt

# Inject Gmail credentials from Jenkins
ARG EMAIL_USER
ARG EMAIL_PASS
ENV EMAIL_USER=${EMAIL_USER}
ENV EMAIL_PASS=${EMAIL_PASS}

# Default port for Flask
EXPOSE 5000
CMD ["python", "Booking_Service_App.py"]
