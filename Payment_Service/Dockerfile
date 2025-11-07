FROM python:3.9-slim
WORKDIR /app
COPY . .
RUN pip install -r requirements.txt
EXPOSE 5003
CMD ["gunicorn", "-b", "0.0.0.0:5003", "Payment_Service_App:app"]