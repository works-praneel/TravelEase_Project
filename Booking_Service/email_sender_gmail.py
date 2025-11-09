import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def _get_creds():
    user = os.getenv("EMAIL_USER")
    pwd  = os.getenv("EMAIL_PASS")
    return user, pwd

def send_confirmation_email(recipient_email, booking_details):
    """
    Send booking confirmation via Gmail SMTP.
    Returns True on success, False on failure.
    """
    GMAIL_USER, GMAIL_PASS = _get_creds()
    if not GMAIL_USER or not GMAIL_PASS:
        # credentials missing
        return False

    msg = MIMEMultipart("alternative")
    msg["Subject"] = "TravelEase Booking Confirmation ✈️"
    msg["From"] = GMAIL_USER
    msg["To"] = recipient_email

    html = f"""
    <html>
      <body style="font-family:Arial, sans-serif; line-height:1.6;">
        <h2 style="color:#4A90E2;">TravelEase Booking Confirmation</h2>
        <p>Your booking is <b>confirmed</b>.</p>
        <hr>
        <p><b>Booking Reference:</b> {booking_details.get('booking_reference')}</p>
        <p><b>Flight ID:</b> {booking_details.get('flight_id')}</p>
        <p><b>Amount Paid:</b> ₹{booking_details.get('amount_paid')}</p>
        <p><b>Transaction ID:</b> {booking_details.get('transaction_id')}</p>
        <hr>
        <p>Thanks,<br/>TravelEase Team</p>
      </body>
    </html>
    """
    msg.attach(MIMEText(html, "html"))

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(GMAIL_USER, GMAIL_PASS)
            server.send_message(msg)
        return True
    except Exception as e:
        # log error for internal debugging
        print(f"[ERROR] Confirmation email failed: {e}")
        return False


def send_cancellation_email(recipient_email, booking_details, refund_amount):
    """
    Send cancellation email. Returns True on success, False on failure.
    """
    GMAIL_USER, GMAIL_PASS = _get_creds()
    if not GMAIL_USER or not GMAIL_PASS:
        return False

    msg = MIMEMultipart("alternative")
    msg["Subject"] = "TravelEase Booking Cancelled"
    msg["From"] = GMAIL_USER
    msg["To"] = recipient_email

    html = f"""
    <html>
      <body style="font-family:Arial, sans-serif; line-height:1.6;">
        <h2 style="color:#d9534f;">TravelEase Booking Cancellation</h2>
        <p>Your booking has been <b>cancelled</b>.</p>
        <hr>
        <p><b>Booking Reference:</b> {booking_details.get('booking_reference')}</p>
        <p><b>Flight:</b> {booking_details.get('flight')}</p>
        <p><b>Original Price:</b> ₹{booking_details.get('price')}</p>
        <p><b>Refund Amount:</b> ₹{refund_amount}</p>
        <hr>
        <p>Refund will be processed within 5-7 business days.</p>
        <p>Regards,<br/>TravelEase Team</p>
      </body>
    </html>
    """
    msg.attach(MIMEText(html, "html"))

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(GMAIL_USER, GMAIL_PASS)
            server.send_message(msg)
        return True
    except Exception as e:
        print(f"[ERROR] Cancellation email failed: {e}")
        return False
