# Jarbis

A personal agentic assistant with a Telegram interface + web dashboard. Logs expenses, meals, calendar events, and reminders in natural language.

---

## Features

### Telegram Bot
- **Expenses** — log, query by period, edit, and delete (single or bulk)
- **Nutrition** — log meals with estimated calories, query calorie summaries, edit and delete
- **Calendar** — create, update, and delete events in Google Calendar
- **Reminders** — set reminders with exact date/time (triggers a Telegram notification)
- **Preferences** — save monthly/weekly budget, daily calorie goal, timezone
- **Multi-turn** — conversational context (last 10 messages)
- **Anti-hallucination** — the agent verifies every write operation before confirming it

### Web Dashboard
- Daily summary: spend, calories, next event
- **Day detail view**: pick any date and see that day's expenses (donut chart by category + transaction list) and meals (grouped by meal type with calories per item)
- Monthly expenses: donut chart by category, progress vs monthly budget
- Transaction history: today / week / month
- Nutrition: calorie ring, meal breakdown, weekly progress
- Agenda: next 14 days from Google Calendar + pending reminders

---

## Architecture

```
User (Telegram)
  → natural language message
    → API Gateway (AWS)
      → Lambda A: jarbis-handler
          · responds 200 to Telegram immediately (avoids 5s timeout)
          · validates secret token and authorized chat_id
          · invokes Lambda B asynchronously (InvocationType=Event)
        → Lambda B: jarbis-agent
            · fetches conversation history from DynamoDB (last 10 messages)
            · calls Claude Haiku 3.5 with tools
            · agentic loop: Claude decides which tools to call
            · executes tools, verifies results
            · saves turn to DynamoDB
            · sends response to user via Telegram Bot API

Dashboard
  → React + Vite (Vercel)
    → FastAPI (Render)
      → DynamoDB (expenses, meals, reminders, preferences)
      → Google Calendar API
```

### Reminders

```
set_reminder(message, datetime)
  → DynamoDB: jarbis-reminders
  → EventBridge Scheduler: one-shot job at the given datetime
      → Lambda C: jarbis-reminder-dispatcher
          · sends message via Telegram
          · marks reminder as sent=true in DynamoDB
```

---

## Stack

| Component | Service | Cost |
|---|---|---|
| Bot | Telegram Bot API | Free |
| API Gateway | AWS API Gateway | Free tier |
| Agent | AWS Lambda Python 3.12 | Free tier |
| LLM | Claude Haiku 3.5 (Anthropic) | ~$0.80/1M tokens |
| Database | AWS DynamoDB | Free tier |
| Scheduler | AWS EventBridge Scheduler | Free tier |
| Calendar | Google Calendar API | Free |
| Dashboard backend | FastAPI on Render | Free tier |
| Dashboard frontend | React + Vite on Vercel | Free |

**Estimated cost: ~$0–1/month** for personal use.

---

## Project Structure

```
jarbis/
├── agent/
│   ├── handler.py              # Lambda A — Telegram webhook → async agent invoke
│   ├── agent_runner.py         # Lambda B — runs the agentic loop
│   ├── agent.py                # Loop: Claude + tools + history + anti-hallucination
│   ├── conversation.py         # Read/write conversation history in DynamoDB
│   ├── scheduler.py            # Creates EventBridge Schedules for reminders
│   ├── storage.py              # All DynamoDB operations
│   ├── telegram.py             # send_message, send_typing helpers
│   ├── google_calendar.py      # Google Calendar API wrapper
│   ├── auth_calendar.py        # OAuth2 authorization script (local only, run once)
│   ├── deploy.sh               # Docker (Linux) build + zip + Lambda deploy
│   ├── requirements.txt        # Pinned versions
│   └── tools/
│       ├── __init__.py         # Combines all DEFINITIONS and HANDLERS
│       ├── expenses.py         # save, get_summary, get_recent, update, delete, delete_bulk
│       ├── nutrition.py        # log, get_summary, get_recent, update, delete, delete_bulk
│       ├── calendar.py         # create, list, update, delete (with post-action verification)
│       ├── reminders.py        # set_reminder, list_reminders, delete_reminder
│       └── preferences.py      # save_preference, get_preference
└── dashboard/
    ├── backend/
    │   ├── main.py             # FastAPI app, CORS, auth
    │   ├── db.py               # DynamoDB resource, helpers
    │   ├── requirements.txt    # Pinned versions
    │   └── routers/
    │       ├── summary.py      # GET /api/summary — daily summary
    │       ├── expenses.py     # GET /api/expenses/{today,weekly,monthly}
    │       ├── nutrition.py    # GET /api/nutrition/{today,weekly}
    │       ├── calendar.py     # GET /api/calendar/{days}
    │       └── reminders.py    # GET /api/reminders
    └── frontend/
        ├── src/
        │   ├── App.jsx
        │   ├── main.jsx
        │   ├── lib/
        │   │   ├── api.js      # Fetch wrapper with Bearer token
        │   │   └── utils.js    # formatKRW, formatDate, categoryColor, etc.
        │   ├── components/
        │   │   ├── Layout.jsx
        │   │   ├── StatCard.jsx
        │   │   └── Skeleton.jsx
        │   └── pages/
        │       ├── Home.jsx
        │       ├── Daily.jsx       # Per-day detail: date picker + expenses donut + meal breakdown
        │       ├── Expenses.jsx
        │       ├── Nutrition.jsx
        │       ├── Agenda.jsx
        │       └── Login.jsx
        └── public/
            └── sw.js           # No-cache Service Worker (for iOS PWA)
```

---

## DynamoDB Tables

| Table | PK | SK | Key attributes |
|---|---|---|---|
| `jarbis-expenses` | `user_id` | `YYYY-MM-DDTHH:MM:SS#uuid` | amount, category, currency, description |
| `jarbis-meals` | `user_id` | `YYYY-MM-DDTHH:MM:SS#uuid` | calories, meal_type, description |
| `jarbis-reminders` | `user_id` | `remind_at#schedule_name` | message, sent, remind_at |
| `jarbis-preferences` | `user_id` | `key` | value |
| `jarbis-conversations` | `user_id` | `ISO8601 timestamp` | role, content (TTL: 24h) |

---

## Setup Guide

### Prerequisites
- AWS account with CLI configured (`aws configure`)
- Anthropic API key
- Telegram bot created via @BotFather
- Google Cloud project with Calendar API enabled
- Docker Desktop (for Linux Lambda builds)
- Python 3.12, Node.js 18+

---

### 1. Clone the repo

```bash
git clone https://github.com/your-username/jarbis.git
cd jarbis
```

---

### 2. DynamoDB — create tables

```bash
# Run for each table (all share the same PK/SK structure)
aws dynamodb create-table \
  --table-name jarbis-expenses \
  --attribute-definitions AttributeName=user_id,AttributeType=S AttributeName=sk,AttributeType=S \
  --key-schema AttributeName=user_id,KeyType=HASH AttributeName=sk,KeyType=RANGE \
  --billing-mode PAY_PER_REQUEST \
  --region us-east-1

# Repeat for: jarbis-meals, jarbis-reminders, jarbis-preferences, jarbis-conversations

# Enable TTL on tables that need it
aws dynamodb update-time-to-live \
  --table-name jarbis-conversations \
  --time-to-live-specification Enabled=true,AttributeName=expires_at \
  --region us-east-1
# Repeat TTL for: jarbis-expenses, jarbis-meals, jarbis-reminders
```

---

### 3. Google Calendar — OAuth2

```bash
cd agent

# 1. Go to Google Cloud Console → create a project
# 2. Enable Calendar API
# 3. Create OAuth2 credentials (type: Desktop app)
# 4. Download credentials.json to the agent/ directory

python auth_calendar.py
# Opens browser → authorize → generates token.json

# Encode token.json for Lambda env var
python -c "import base64; print(base64.b64encode(open('token.json','rb').read()).decode())"
# Save the output as GOOGLE_CALENDAR_CREDENTIALS
```

---

### 4. Lambda — create functions

```bash
# Create IAM role with permissions:
# AmazonDynamoDBFullAccess, AWSLambda_FullAccess,
# AmazonEventBridgeSchedulerFullAccess, CloudWatchLogsFullAccess
# Suggested name: jarbis-lambda-role

aws lambda create-function \
  --function-name jarbis-handler \
  --runtime python3.12 \
  --role arn:aws:iam::YOUR_ACCOUNT_ID:role/jarbis-lambda-role \
  --handler handler.lambda_handler \
  --zip-file fileb://placeholder.zip \
  --timeout 10 \
  --memory-size 128 \
  --region us-east-1

aws lambda create-function \
  --function-name jarbis-agent \
  --runtime python3.12 \
  --role arn:aws:iam::YOUR_ACCOUNT_ID:role/jarbis-lambda-role \
  --handler agent_runner.lambda_handler \
  --zip-file fileb://placeholder.zip \
  --timeout 120 \
  --memory-size 256 \
  --region us-east-1

aws lambda create-function \
  --function-name jarbis-reminder-dispatcher \
  --runtime python3.12 \
  --role arn:aws:iam::YOUR_ACCOUNT_ID:role/jarbis-lambda-role \
  --handler reminder_dispatcher.lambda_handler \
  --zip-file fileb://placeholder.zip \
  --timeout 30 \
  --memory-size 128 \
  --region us-east-1
```

Set these environment variables on `jarbis-handler` and `jarbis-agent`:

```
ANTHROPIC_API_KEY=sk-ant-...
TELEGRAM_BOT_TOKEN=...
TELEGRAM_CHAT_ID=your_numeric_chat_id
TELEGRAM_SECRET_TOKEN=random_secure_string
AGENT_LAMBDA_NAME=jarbis-agent
DYNAMODB_TABLE_EXPENSES=jarbis-expenses
DYNAMODB_TABLE_MEALS=jarbis-meals
DYNAMODB_TABLE_REMINDERS=jarbis-reminders
DYNAMODB_TABLE_PREFERENCES=jarbis-preferences
DYNAMODB_TABLE_CONVERSATIONS=jarbis-conversations
AWS_REGION=us-east-1
GOOGLE_CALENDAR_CREDENTIALS=<base64 of token.json>
GOOGLE_CALENDAR_ID=primary
EVENTBRIDGE_ROLE_ARN=arn:aws:iam::YOUR_ACCOUNT_ID:role/jarbis-lambda-role
DISPATCHER_LAMBDA_ARN=arn:aws:lambda:us-east-1:YOUR_ACCOUNT_ID:function:jarbis-reminder-dispatcher
```

---

### 5. API Gateway — Telegram webhook

```bash
# Create an HTTP API in API Gateway pointing to jarbis-handler
# Get the URL: https://xxxx.execute-api.us-east-1.amazonaws.com/

# Register the webhook with Telegram
curl "https://api.telegram.org/bot<TOKEN>/setWebhook" \
  -d "url=https://xxxx.execute-api.us-east-1.amazonaws.com/" \
  -d "secret_token=YOUR_TELEGRAM_SECRET_TOKEN"
```

---

### 6. Deploy the agent

```bash
cd agent
bash deploy.sh
# Requires Docker running — builds with the official Lambda Linux image
```

---

### 7. Dashboard backend (Render)

1. Create a new Web Service on Render pointing to the repo, root directory `dashboard/backend`
2. Build command: `pip install -r requirements.txt`
3. Start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
4. Set environment variables on Render:

```
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
AWS_REGION=us-east-1
DYNAMODB_TABLE_EXPENSES=jarbis-expenses
DYNAMODB_TABLE_MEALS=jarbis-meals
DYNAMODB_TABLE_REMINDERS=jarbis-reminders
DYNAMODB_TABLE_PREFERENCES=jarbis-preferences
GOOGLE_CALENDAR_CREDENTIALS=<base64 of token.json>
GOOGLE_CALENDAR_ID=primary
DASHBOARD_ACCESS_TOKEN=your_dashboard_secret_token
CORS_ALLOWED_ORIGINS=https://your-app.vercel.app
```

5. To keep Render alive on the free tier: set up an UptimeRobot monitor with a HEAD request to `https://your-app.onrender.com/health` every 5 minutes.

---

### 8. Dashboard frontend (Vercel)

```bash
cd dashboard/frontend
npm install
```

Create `.env.production`:
```
VITE_API_URL=https://your-app.onrender.com
```

Deploy to Vercel:
```bash
npx vercel --prod
```

Or connect the repo on vercel.com with root directory set to `dashboard/frontend`.

---

### 9. iOS PWA (optional)

1. Open the dashboard in Safari
2. Share → Add to Home Screen
3. The Service Worker (`public/sw.js`) bypasses the cache so the latest version always loads

---

## Environment Variables Reference

### Agent (Lambda)
| Variable | Description |
|---|---|
| `ANTHROPIC_API_KEY` | Anthropic API key |
| `TELEGRAM_BOT_TOKEN` | Telegram bot token |
| `TELEGRAM_CHAT_ID` | Authorized numeric chat ID |
| `TELEGRAM_SECRET_TOKEN` | Webhook secret (required — startup fails if missing) |
| `AGENT_LAMBDA_NAME` | Name of the jarbis-agent function |
| `DYNAMODB_TABLE_*` | DynamoDB table names |
| `AWS_REGION` | AWS region |
| `GOOGLE_CALENDAR_CREDENTIALS` | token.json encoded in base64 |
| `GOOGLE_CALENDAR_ID` | Calendar ID (`primary` or specific) |
| `EVENTBRIDGE_ROLE_ARN` | IAM role ARN for EventBridge Scheduler |
| `DISPATCHER_LAMBDA_ARN` | ARN of jarbis-reminder-dispatcher |

### Dashboard backend (Render)
| Variable | Description |
|---|---|
| `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` | IAM credentials |
| `AWS_REGION` | AWS region |
| `DYNAMODB_TABLE_*` | DynamoDB table names |
| `GOOGLE_CALENDAR_CREDENTIALS` | token.json encoded in base64 |
| `GOOGLE_CALENDAR_ID` | Calendar ID |
| `DASHBOARD_ACCESS_TOKEN` | Dashboard access token |
| `CORS_ALLOWED_ORIGINS` | Frontend domain (e.g. `https://jarbis.vercel.app`) |

### Dashboard frontend (Vercel)
| Variable | Description |
|---|---|
| `VITE_API_URL` | Backend URL on Render |

---

## Usage Examples

```
"spent 15,000 won on ramen"
"had oatmeal with fruit for breakfast, around 400 calories"
"create an event this Friday at 7pm, dinner with friends"
"remind me to call the doctor tomorrow at 9am"
"how much did I spend this month?"
"how are my calories looking today?"
"what do I have this week?"
"set my monthly budget to 800,000 won"
"fix today's lunch, it was 650 calories not 400"
"delete the transport expense from Monday"
```
