# 📦 sms-logger

A lightweight SMS-based logging system for personal use, allowing you to track mileage, work hours, and other metrics via simple text messages.

## 🔧 Features

- **SMS Command Parsing**: Supports commands like `MILEAGE` and `HOURS` with flexible date formats.
- **Date Normalization**: Accepts `today()`, `YYYY-MM-DD`, `YYYY/MM/DD`, and `YYYY MM DD`.
- **Time Zone Awareness**: All dates and times are normalized to Eastern Time (ET).
- **Secure Logging**: Only processes messages from an authorized phone number.
- **Local Storage**: Logs are stored in a local SQLite database.
- **Modular Design**: Easily extendable to support additional log types.

## 📱 SMS Command Formats

### Mileage Logging

MILEAGE, date, name, position, distance
- `date`: `today()`, `YYYY-MM-DD`, `YYYY/MM/DD`, or `YYYY MM DD`
- `name`: Location name or identifier
- `position`: One of `start`, `mid`, or `end`
- `distance`: Miles traveled (e.g., `12.5`)

**Example:**
MILEAGE, today(), Kevin, start, 10.0

### Hours Logging
HOURS, date, hours_today, hours_week_total
- `date`: Same flexible formats as above
- `hours_today`: Hours worked today (e.g., `8.25`)
- `hours_week_total`: Cumulative hours worked this week (e.g., `32.75`)

**Example:**
HOURS, today(), 8.25, 32.75

## 🛠️ Setup Instructions

### 1. Clone the Repository

```bash
git clone https://github.com/kevinkeithley/sms-logger.git
cd sms-logger
```

### 2. Install Dependencies

Ensure Python 3.12+ is installed. Then run:

```bash
pip install -r requirements.txt
```

### 3. Configure Environment Variables
Create a `.env` file in the project root with the following contents:
```bash
AUTHORIZED_NUMBER=+1234567890
TAILSCALE_LOGGER_URL=http://your-local-logger-url/log
```

### 4. Deploy to Fly.io
Ensure you have `flyctl` installed:
```bash
flyctl deploy
```
