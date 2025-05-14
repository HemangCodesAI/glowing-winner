import smtplib

try:
    smtp = smtplib.SMTP("smtp.gmail.com", 587, timeout=10)
    smtp.ehlo()
    print("✅ Connection successful")
except Exception as e:
    print("❌ Connection failed:", e)
