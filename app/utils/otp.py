import random
import time
from flask_mail import Message
from flask import current_app
from app.extensions import mail


otp_store = {}

def generate_otp(email):
    otp = str(random.randint(100000, 999999))
    otp_store[email] = {'otp': otp, 'timestamp': time.time()}
    send_email(email, otp)
    return otp

def send_email(recipient, otp):
    msg = Message("Your OTP Code", 
                sender=current_app.config['MAIL_USERNAME'], 
                recipients=[recipient])
    msg.body = f"Your OTP code is {otp}. It expires in 5 minutes."
    mail.send(msg)

def verify_otp(email, user_input):
    if email not in otp_store:
        return False
    stored = otp_store[email]
    if time.time() - stored['timestamp'] > 300:
        return False
    return stored['otp'] == user_input
