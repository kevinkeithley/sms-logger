from flask import Flask, request, Response
from twilio.twiml.messaging_response import MessagingResponse
from dotenv import load_dotenv
import os

# Load environment variables from .env
load_dotenv()

app = Flask(__name__)

@app.route("/sms", methods=["POST"])
def sms_reply():
    incoming_msg = request.form.get("Body")
    sender = request.form.get("From")

    print(f"📩 SMS received from {sender}: {incoming_msg}")

    # Optional: send a response back
    resp = MessagingResponse()
    resp.message("✅ Message received. Thanks!")

    return Response(str(resp), mimetype="application/xml")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
