# SMS Logger

A Twilio-powered SMS ingester that parses text messages for logging mileage and work hours. Runs on Fly.io and forwards validated data to a backend service via Tailscale.

## Overview

This service acts as the SMS interface for a personal tracking system:
- **Receives SMS** via Twilio webhook
- **Parses commands** for mileage and hours tracking
- **Validates data** and provides immediate feedback
- **Forwards to backend** for storage and processing
- **Handles queries** for reports and summaries

## Architecture

```
SMS → Twilio → Fly.io (this service) → Tailscale → Backend Service
                                                    └→ SQLite DB
```

## Features

- ✅ **Secure** - Only processes messages from authorized phone number
- ✅ **Flexible date parsing** - Accepts multiple date formats including `today()`
- ✅ **Data validation** - Ensures correct format before forwarding
- ✅ **Query support** - Get summaries and reports via SMS
- ✅ **Timezone aware** - All timestamps in Eastern Time
- ✅ **Instant feedback** - Immediate SMS confirmation

## SMS Commands

### Data Entry Commands

**Log Mileage**
```
MILEAGE, date, name, position, distance
```
- `date`: `today()`, `YYYY-MM-DD`, `YYYY/MM/DD`, or `YYYY MM DD`
- `name`: Client name or location (for tracking different trips)
- `position`: `start`, `mid`, or `end` (odometer reading position)
- `distance`: Current odometer reading
- Example: `MILEAGE, today(), Kevin, start, 100.5`
- Example: `MILEAGE, today(), Fairfax, end, 125.8`

This tracks business mileage by recording odometer readings at the start and end of trips to different clients/locations.

**Log Hours**
```
HOURS, date, hours_today, hours_week_total
```
- Example: `HOURS, today(), 8.5, 42.5`

### Query Commands

- `PAYSTATUS` - Current pay period status with hours needed per day
- `PAYPERIOD` - Current pay period summary (regular/OT hours)
- `PAYHISTORY` - Last 3 pay periods comparison
- `MILES` - Today's mileage entries
- `MILES ClientName` - Specific client's recent mileage (30 days)
- `MILES 2025-06-05` - Mileage for specific date
- `MILESWEEK` - This week's mileage summary
- `TIME` - This week's hours breakdown
- `PROCESS` - Manually trigger backend processing
- `COMMANDS` or `?` - Show available commands

## Deployment

This service runs on [Fly.io](https://fly.io):

### Prerequisites
- Fly.io account and CLI (`flyctl`)
- Twilio phone number
- Backend service running with Tailscale

### Environment Variables
Set these as Fly secrets:
```bash
fly secrets set AUTHORIZED_NUMBER=+1234567890
fly secrets set TAILSCALE_LOGGER_URL=https://your-machine.ts.net
```

### Deploy
```bash
fly deploy
```

### Configure Twilio
Set your Twilio phone number's webhook to:
```
https://your-app.fly.dev/sms
```

## Local Development

1. **Clone and setup**
   ```bash
   git clone https://github.com/kevinkeithley/sms-logger.git
   cd sms-logger
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Create `.env` file**
   ```
   AUTHORIZED_NUMBER=+1234567890
   TAILSCALE_LOGGER_URL=https://your-backend.ts.net
   ```

3. **Run locally**
   ```bash
   python app.py
   ```

## Backend Integration

This ingester works with [sms-logger-backend](https://github.com/kevinkeithley/sms-logger-backend) which:
- Stores data in SQLite
- Calculates mileage totals
- Tracks pay periods
- Provides query responses

## Response Examples

**Successful entry:**
```
✅ Entry validated and logged.
```

**Query response (PAYSTATUS):**
```
Pay Period: 2025-06-02 - 2025-06-15
Day 6 of 14
Hours: 42.5 (5 days)
Work days left: 7
Need 5.4 hrs/day for 80 total
```

**Invalid format:**
```
⚠️ Format: MILEAGE, date, name, start|mid|end, distance
```

## Security

- Only accepts messages from the configured `AUTHORIZED_NUMBER`
- Returns 403 Forbidden for unauthorized numbers
- All data forwarded over HTTPS via Tailscale

## Error Handling

- Validates all inputs before forwarding
- Provides specific error messages for malformed commands
- Gracefully handles backend connection failures
- Returns user-friendly SMS responses

## License

MIT License - see [LICENSE](LICENSE) file
