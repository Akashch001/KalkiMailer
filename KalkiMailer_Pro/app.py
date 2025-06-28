import os
import smtplib
import csv
from flask import Flask, request, render_template
from email.message import EmailMessage
from concurrent.futures import ThreadPoolExecutor

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'

MAX_THREADS = 5

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        subject = request.form.get("subject")
        message_body = request.form.get("message")

        email_file = request.files.get("email_file")
        smtp_file = request.files.get("smtp_file")
        attachment = request.files.get("attachment")

        if not email_file or not smtp_file:
            return "⚠️ Please upload both recipient and SMTP files."

        recipients = [line.strip() for line in email_file.read().decode("utf-8").splitlines() if line.strip()]

        smtp_lines = smtp_file.read().decode("utf-8").splitlines()
        smtp_credentials = []
        for line in csv.reader(smtp_lines):
            if len(line) >= 2:
                smtp_credentials.append((line[0].strip(), line[1].strip()))

        if not smtp_credentials:
            return "⚠️ No valid SMTP credentials found."

        def send_email(recipient, smtp_index):
            sender_email, sender_password = smtp_credentials[smtp_index % len(smtp_credentials)]
            msg = EmailMessage()
            msg["Subject"] = subject
            msg["From"] = sender_email
            msg["To"] = recipient
            msg.set_content(message_body)

            if attachment:
                attachment.stream.seek(0)
                file_data = attachment.read()
                msg.add_attachment(file_data, maintype="application", subtype="octet-stream", filename=attachment.filename)

            try:
                with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
                    smtp.login(sender_email, sender_password)
                    smtp.send_message(msg)
                    print(f"✅ Sent to {recipient} via {sender_email}")
            except Exception as e:
                print(f"❌ Failed to {recipient} via {sender_email}: {e}")

        with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
            for i, recipient in enumerate(recipients):
                executor.submit(send_email, recipient, i)

        return "✅ All emails have been processed with multiple SMTPs!"

    return render_template("index.html")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
