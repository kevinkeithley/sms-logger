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
TAILSCALE_ENDPOINT = os.getenv("TAILSCALE_LOGGER_URL")


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


def handle_query(query_text):
    """Handle query commands and return response text"""
    query_upper = query_text.strip().upper()

    # Map SMS commands to query types
    query_map = {
        "PAYSTATUS": "pay_status",  # Current pay period status
        "PAYPERIOD": "pay_period",  # Current pay period summary
        "PAYHISTORY": "pay_history",  # Recent pay periods
        "MILES": "mileage_today",  # Today's mileage
        "MILESWEEK": "mileage_summary",  # Week's mileage
        "TIME": "hours_week",  # This week's hours
        "COMMANDS": "help",  # List commands (not HELP)
        "?": "help",  # Alternative
    }

    # Check for direct command match
    query_type = query_map.get(query_upper)

    # Check for commands with parameters
    if not query_type:
        if query_upper.startswith("MILES "):
            # Handle "MILES Kevin" or "MILES 2025-06-05"
            param = query_text[6:].strip()
            if "-" in param:  # Looks like a date
                return {"type": "mileage_summary", "date": param}
            else:  # Assume it's a name
                return {"type": "mileage_summary", "name": param, "days": 30}

    if query_type == "help":
        return None, (
            "📱 Available Commands:\n"
            "PAYSTATUS - Current pay period\n"
            "PAYPERIOD - Pay period totals\n"
            "PAYHISTORY - Recent pay periods\n"
            "MILES - Today's mileage\n"
            "MILESWEEK - Week's mileage\n"
            "TIME - This week's hours\n"
            "COMMANDS or ? - Show this list\n"
            "PROCESS - Run processing"
        )

    if not query_type:
        return None, "❓ Unknown query. Text HELP for commands."

    return {"type": query_type}, None


@app.route("/sms", methods=["POST"])
def sms_reply():
    incoming_msg = request.form.get("Body", "").strip()
    sender = request.form.get("From")

    if sender != AUTHORIZED_NUMBER:
        print(f"❌ Unauthorized sender: {sender}")
        return Response("Unauthorized", status=403)

    print(f"📩 SMS received from {sender}: {incoming_msg}")
    resp = MessagingResponse()

    # Check if this is a data entry (MILEAGE or HOURS with commas)
    if "," in incoming_msg:
        if incoming_msg.upper().startswith("MILEAGE"):
            valid, result = parse_csv_mileage(incoming_msg)
            endpoint = "/log"
        elif incoming_msg.upper().startswith("HOURS"):
            valid, result = parse_csv_hours(incoming_msg)
            endpoint = "/log"
        else:
            resp.message("❓ Unknown command. Try: MILEAGE or HOURS")
            return Response(str(resp), mimetype="application/xml")

        if not valid:
            resp.message(result)
        else:
            print(f"✅ Parsed Entry: {result}")
            try:
                r = requests.post(TAILSCALE_ENDPOINT + endpoint, json=result, timeout=5)
                r.raise_for_status()
                print("✅ Forwarded to local logger.")
                resp.message("✅ Entry validated and logged.")
            except Exception as e:
                print(f"❌ Error forwarding to logger: {e}")
                resp.message("⚠️ Validated, but failed to log. Please try again later.")

    # Check if this is PROCESS command
    elif incoming_msg.upper() == "PROCESS":
        try:
            r = requests.post(TAILSCALE_ENDPOINT + "/process", json={}, timeout=10)
            r.raise_for_status()
            result = r.json()
            resp.message(
                f"✅ Processed {result['processed']['total']} entries\n"
                f"Mileage: {result['processed']['mileage']}, "
                f"Hours: {result['processed']['hours']}"
            )
        except Exception as e:
            print(f"❌ Error triggering process: {e}")
            resp.message("⚠️ Failed to process. Check logs.")

    # Otherwise, treat as a query
    else:
        query_data, help_text = handle_query(incoming_msg)

        if help_text:
            resp.message(help_text)
        else:
            try:
                r = requests.post(
                    TAILSCALE_ENDPOINT + "/query", json=query_data, timeout=5
                )
                r.raise_for_status()
                response_data = r.json()
                resp.message(response_data.get("message", "No data found"))
            except Exception as e:
                print(f"❌ Error querying: {e}")
                resp.message("⚠️ Query failed. Try again later.")

    return Response(str(resp), mimetype="application/xml")


@app.route("/health", methods=["GET"])
def health():
    """Health check endpoint for Fly.io"""
    return {"status": "healthy"}, 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
