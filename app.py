from flask import Flask, request, Response
from twilio.twiml.messaging_response import MessagingResponse
from dotenv import load_dotenv
import os
import requests
from datetime import datetime
from zoneinfo import ZoneInfo

EASTERN = ZoneInfo("America/New_York")

# Load environment variables
load_dotenv()

app = Flask(__name__)
AUTHORIZED_NUMBER = os.getenv("AUTHORIZED_NUMBER")


def normalize_date(date_string):
    date_string = date_string.strip()

    if date_string.lower() == "today()":
        return datetime.now(EASTERN).strftime("%Y-%m-%d")

    date_formats = ["%Y-%m-%d", "%Y/%m/%d", "%Y %m %d"]
    for fmt in date_formats:
        try:
            dt = datetime.strptime(date_string, fmt)
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            continue

    raise ValueError(
        f"❌ Invalid date format: '{date_string}'. Use YYYY-MM-DD or today()"
    )


def parse_csv_mileage(message):
    parts = [p.strip() for p in message.split(",")]

    if len(parts) != 5 or parts[0].upper() != "MILEAGE":
        return False, "⚠️ Format: MILEAGE, date, name, start|mid|end, distance"

    _, raw_date, name, position, distance_str = parts

    try:
        date = normalize_date(raw_date)
    except ValueError as e:
        return False, str(e)

    if position.lower() not in ["start", "mid", "end"]:
        return False, "⚠️ Position must be 'start', 'mid', or 'end'"

    try:
        distance = float(distance_str)
    except ValueError:
        return False, "⚠️ Distance must be a number (e.g., 12.5)"

    return True, {
        "type": "mileage",
        "date": date,
        "name": name,
        "position": position.lower(),
        "distance": distance,
    }


def parse_csv_hours(message):
    parts = [p.strip() for p in message.split(",")]

    if len(parts) != 4 or parts[0].upper() != "HOURS":
        return False, "⚠️ Format: HOURS, date, hours_today, hours_week_total"

    _, raw_date, hours_today_str, hours_week_str = parts

    try:
        date = normalize_date(raw_date)
    except ValueError as e:
        return False, str(e)

    try:
        hours_today = float(hours_today_str)
        hours_week = float(hours_week_str)
    except ValueError:
        return False, "⚠️ Hours must be numbers (e.g., 8.25, 32.75)"

    return True, {
        "type": "hours",
        "date": date,
        "hours_today": hours_today,
        "hours_week": hours_week,
    }


@app.route("/sms", methods=["POST"])
def sms_reply():
    incoming_msg = request.form.get("Body")
    sender = request.form.get("From")

    if sender != AUTHORIZED_NUMBER:
        print(f"❌ Unauthorized sender: {sender}")
        return Response("Unauthorized", status=403)

    print(f"📩 SMS received from {sender}: {incoming_msg}")
    resp = MessagingResponse()

    if incoming_msg.upper().startswith("MILEAGE"):
        valid, result = parse_csv_mileage(incoming_msg)
    elif incoming_msg.upper().startswith("HOURS"):
        valid, result = parse_csv_hours(incoming_msg)
    else:
        resp.message("❓ Unknown command. Try: MILEAGE or HOURS")
        return Response(str(resp), mimetype="application/xml")

    if not valid:
        resp.message(result)
    else:
        print(f"✅ Parsed Entry: {result}")
        try:
            TAILSCALE_ENDPOINT = os.getenv("TAILSCALE_LOGGER_URL")
            r = requests.post(TAILSCALE_ENDPOINT, json=result, timeout=5)
            r.raise_for_status()
            print("✅ Forwarded to local logger.")
            resp.message("✅ Entry validated and logged.")
        except Exception as e:
            print(f"❌ Error forwarding to logger: {e}")
            resp.message("⚠️ Validated, but failed to log. Please try again later.")

    return Response(str(resp), mimetype="application/xml")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
