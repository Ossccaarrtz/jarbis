# Jarbis

Asistente personal agentic con interfaz Telegram + dashboard web. Registra gastos, comidas, eventos de calendario y recordatorios en lenguaje natural.

---

## Funcionalidades

### Bot de Telegram
- **Gastos** — registrar, consultar por período, corregir y eliminar (individual o en bloque)
- **Nutrición** — registrar comidas con calorías estimadas, consultar resumen calórico, corregir y eliminar
- **Calendario** — crear, modificar y eliminar eventos en Google Calendar
- **Recordatorios** — crear recordatorios con fecha/hora exacta (disparan notificación por Telegram)
- **Preferencias** — guardar budget mensual/semanal, meta calórica diaria, zona horaria
- **Multi-turno** — contexto conversacional (últimos 10 mensajes)
- **Anti-alucinación** — el agente verifica toda operación de escritura antes de confirmarla

### Dashboard Web
- Resumen del día: gasto, calorías, próximo evento
- Gastos del mes: gráfica de dona por categoría, progreso vs budget mensual
- Historial de transacciones: hoy / semana / mes
- Nutrición: anillo calórico, desglose por comida, progreso semanal
- Agenda: próximos 14 días de Google Calendar + recordatorios pendientes

---

## Arquitectura

```
Usuario (Telegram)
  → mensaje en lenguaje natural
    → API Gateway (AWS)
      → Lambda A: jarbis-handler
          · responde 200 a Telegram inmediatamente (evita timeout 5s)
          · valida secret token y chat_id autorizado
          · invoca Lambda B de forma async (InvocationType=Event)
        → Lambda B: jarbis-agent
            · recupera historial de DynamoDB (últimos 10 mensajes)
            · llama Claude Haiku 3.5 con tools
            · loop agentic: Claude decide qué tools llamar
            · ejecuta tools, verifica resultados
            · guarda turno en DynamoDB
            · responde al usuario por Telegram Bot API

Dashboard
  → React + Vite (Vercel)
    → FastAPI (Render)
      → DynamoDB (gastos, comidas, recordatorios, preferencias)
      → Google Calendar API
```

### Recordatorios

```
set_reminder(message, datetime)
  → DynamoDB: jarbis-reminders
  → EventBridge Scheduler: job one-shot en la fecha indicada
      → Lambda C: jarbis-reminder-dispatcher
          · envía mensaje por Telegram
          · marca reminder como sent=true en DynamoDB
```

---

## Stack

| Componente | Servicio | Costo |
|---|---|---|
| Bot | Telegram Bot API | Gratis |
| API Gateway | AWS API Gateway | Free tier |
| Agente | AWS Lambda Python 3.12 | Free tier |
| LLM | Claude Haiku 3.5 (Anthropic) | ~$0.80/1M tokens |
| Base de datos | AWS DynamoDB | Free tier |
| Scheduler | AWS EventBridge Scheduler | Free tier |
| Calendario | Google Calendar API | Gratis |
| Backend dashboard | FastAPI en Render | Free tier |
| Frontend dashboard | React + Vite en Vercel | Gratis |

**Costo estimado: ~$0–1/mes** para uso personal.

---

## Estructura del proyecto

```
jarbis/
├── agent/
│   ├── handler.py              # Lambda A — webhook Telegram → invoca agente async
│   ├── agent_runner.py         # Lambda B — ejecuta loop agentic
│   ├── agent.py                # Loop: Claude + tools + historial + anti-alucinación
│   ├── conversation.py         # Lectura/escritura de historial en DynamoDB
│   ├── scheduler.py            # Crea EventBridge Schedules para recordatorios
│   ├── storage.py              # Todas las operaciones DynamoDB
│   ├── telegram.py             # send_message, send_typing helpers
│   ├── google_calendar.py      # Wrapper Google Calendar API
│   ├── auth_calendar.py        # Script de autorización OAuth2 (solo local, una vez)
│   ├── deploy.sh               # Build Docker (Linux) + zip + deploy a Lambda
│   ├── requirements.txt        # Versiones pinneadas
│   └── tools/
│       ├── __init__.py         # Agrega todos los DEFINITIONS y HANDLERS
│       ├── expenses.py         # save, get_summary, get_recent, update, delete, delete_bulk
│       ├── nutrition.py        # log, get_summary, get_recent, update, delete, delete_bulk
│       ├── calendar.py         # create, list, update, delete (con verificación post-acción)
│       ├── reminders.py        # set_reminder, list_reminders, delete_reminder
│       └── preferences.py      # save_preference, get_preference
└── dashboard/
    ├── backend/
    │   ├── main.py             # FastAPI app, CORS, auth
    │   ├── db.py               # DynamoDB resource, helpers
    │   ├── requirements.txt    # Versiones pinneadas
    │   └── routers/
    │       ├── summary.py      # GET /api/summary — resumen del día
    │       ├── expenses.py     # GET /api/expenses/{today,weekly,monthly}
    │       ├── nutrition.py    # GET /api/nutrition/{today,weekly}
    │       ├── calendar.py     # GET /api/calendar/{days}
    │       └── reminders.py    # GET /api/reminders
    └── frontend/
        ├── src/
        │   ├── App.jsx
        │   ├── main.jsx
        │   ├── lib/
        │   │   ├── api.js      # Wrapper fetch con Bearer token
        │   │   └── utils.js    # formatKRW, formatDate, categoryColor, etc.
        │   ├── components/
        │   │   ├── Layout.jsx
        │   │   ├── StatCard.jsx
        │   │   └── Skeleton.jsx
        │   └── pages/
        │       ├── Home.jsx
        │       ├── Expenses.jsx
        │       ├── Nutrition.jsx
        │       ├── Agenda.jsx
        │       └── Login.jsx
        └── public/
            └── sw.js           # Service Worker sin caché (para PWA en iOS)
```

---

## DynamoDB — tablas

| Tabla | PK | SK | Atributos clave |
|---|---|---|---|
| `jarbis-expenses` | `user_id` | `YYYY-MM-DDTHH:MM:SS#uuid` | amount, category, currency, description |
| `jarbis-meals` | `user_id` | `YYYY-MM-DDTHH:MM:SS#uuid` | calories, meal_type, description |
| `jarbis-reminders` | `user_id` | `remind_at#schedule_name` | message, sent, remind_at |
| `jarbis-preferences` | `user_id` | `key` | value |
| `jarbis-conversations` | `user_id` | `timestamp ISO8601` | role, content (TTL: 24h) |

---

## Setup completo desde cero

### Requisitos previos
- Cuenta AWS con CLI configurado (`aws configure`)
- Cuenta Anthropic con API key
- Bot de Telegram creado con @BotFather
- Proyecto Google Cloud con Calendar API habilitada
- Docker Desktop instalado (para build Linux de Lambda)
- Python 3.12, Node.js 18+

---

### 1. Clonar el repo

```bash
git clone https://github.com/tu-usuario/jarbis.git
cd jarbis
```

---

### 2. DynamoDB — crear tablas

```bash
# Repetir para cada tabla con sus parámetros
aws dynamodb create-table \
  --table-name jarbis-expenses \
  --attribute-definitions AttributeName=user_id,AttributeType=S AttributeName=sk,AttributeType=S \
  --key-schema AttributeName=user_id,KeyType=HASH AttributeName=sk,KeyType=RANGE \
  --billing-mode PAY_PER_REQUEST \
  --region us-east-1

# Repetir para: jarbis-meals, jarbis-reminders, jarbis-preferences, jarbis-conversations
# (misma estructura de PK/SK)

# Habilitar TTL en tablas que lo necesitan
aws dynamodb update-time-to-live \
  --table-name jarbis-conversations \
  --time-to-live-specification Enabled=true,AttributeName=expires_at \
  --region us-east-1
# Repetir TTL para: jarbis-expenses, jarbis-meals, jarbis-reminders
```

---

### 3. Google Calendar — OAuth2

```bash
cd agent

# 1. Crear proyecto en Google Cloud Console
# 2. Habilitar Calendar API
# 3. Crear credenciales OAuth2 (tipo: Desktop app)
# 4. Descargar credentials.json al directorio agent/

python auth_calendar.py
# Abre navegador → autoriza → genera token.json

# Encodear token.json para env var de Lambda
python -c "import base64, open; print(base64.b64encode(open('token.json','rb').read()).decode())"
# Guardar el output como GOOGLE_CALENDAR_CREDENTIALS
```

---

### 4. Lambdas — crear funciones

```bash
# Crear rol IAM con permisos: DynamoDB, Lambda:InvokeFunction, scheduler:CreateSchedule, CloudWatch Logs
# Nombre sugerido: jarbis-lambda-role

# Crear las tres funciones (primero con código vacío, deploy.sh actualizará)
aws lambda create-function \
  --function-name jarbis-handler \
  --runtime python3.12 \
  --role arn:aws:iam::TU_ACCOUNT_ID:role/jarbis-lambda-role \
  --handler handler.lambda_handler \
  --zip-file fileb://placeholder.zip \
  --timeout 10 \
  --memory-size 128 \
  --region us-east-1

aws lambda create-function \
  --function-name jarbis-agent \
  --runtime python3.12 \
  --role arn:aws:iam::TU_ACCOUNT_ID:role/jarbis-lambda-role \
  --handler agent_runner.lambda_handler \
  --zip-file fileb://placeholder.zip \
  --timeout 120 \
  --memory-size 256 \
  --region us-east-1

aws lambda create-function \
  --function-name jarbis-reminder-dispatcher \
  --runtime python3.12 \
  --role arn:aws:iam::TU_ACCOUNT_ID:role/jarbis-lambda-role \
  --handler reminder_dispatcher.lambda_handler \
  --zip-file fileb://placeholder.zip \
  --timeout 30 \
  --memory-size 128 \
  --region us-east-1
```

**Variables de entorno para `jarbis-handler` y `jarbis-agent`:**

```
ANTHROPIC_API_KEY=sk-ant-...
TELEGRAM_BOT_TOKEN=...
TELEGRAM_CHAT_ID=tu_chat_id_numerico
TELEGRAM_SECRET_TOKEN=cadena_aleatoria_segura
AGENT_LAMBDA_NAME=jarbis-agent
DYNAMODB_TABLE_EXPENSES=jarbis-expenses
DYNAMODB_TABLE_MEALS=jarbis-meals
DYNAMODB_TABLE_REMINDERS=jarbis-reminders
DYNAMODB_TABLE_PREFERENCES=jarbis-preferences
DYNAMODB_TABLE_CONVERSATIONS=jarbis-conversations
AWS_REGION=us-east-1
GOOGLE_CALENDAR_CREDENTIALS=<base64 del token.json>
GOOGLE_CALENDAR_ID=primary
EVENTBRIDGE_ROLE_ARN=arn:aws:iam::TU_ACCOUNT_ID:role/jarbis-lambda-role
DISPATCHER_LAMBDA_ARN=arn:aws:lambda:us-east-1:TU_ACCOUNT_ID:function:jarbis-reminder-dispatcher
```

---

### 5. API Gateway — webhook Telegram

```bash
# Crear HTTP API en API Gateway apuntando a jarbis-handler
# Obtener la URL: https://xxxx.execute-api.us-east-1.amazonaws.com/

# Registrar webhook en Telegram
curl "https://api.telegram.org/bot<TOKEN>/setWebhook" \
  -d "url=https://xxxx.execute-api.us-east-1.amazonaws.com/" \
  -d "secret_token=TU_TELEGRAM_SECRET_TOKEN"
```

---

### 6. Deploy del agente

```bash
cd agent
bash deploy.sh
# Requiere Docker corriendo — build con imagen Linux de Lambda
```

---

### 7. Dashboard backend (Render)

1. Crear nuevo Web Service en Render apuntando al repo, directorio `dashboard/backend`
2. Build command: `pip install -r requirements.txt`
3. Start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
4. Variables de entorno en Render:
```
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
AWS_REGION=us-east-1
DYNAMODB_TABLE_EXPENSES=jarbis-expenses
DYNAMODB_TABLE_MEALS=jarbis-meals
DYNAMODB_TABLE_REMINDERS=jarbis-reminders
DYNAMODB_TABLE_PREFERENCES=jarbis-preferences
GOOGLE_CALENDAR_CREDENTIALS=<base64 del token.json>
GOOGLE_CALENDAR_ID=primary
DASHBOARD_ACCESS_TOKEN=token_secreto_del_dashboard
CORS_ALLOWED_ORIGINS=https://tu-app.vercel.app
```
5. Para mantener Render activo (free tier): configurar UptimeRobot con ping HEAD a `https://tu-app.onrender.com/health` cada 5 minutos.

---

### 8. Dashboard frontend (Vercel)

```bash
cd dashboard/frontend
npm install
```

Crear `.env.production`:
```
VITE_API_URL=https://tu-app.onrender.com
```

Deploy en Vercel:
```bash
npx vercel --prod
```

O conectar el repo en vercel.com con root directory `dashboard/frontend`.

---

### 9. PWA en iOS (opcional)

1. Abrir el dashboard en Safari
2. Compartir → Agregar a pantalla de inicio
3. El Service Worker (`public/sw.js`) desactiva el caché para que siempre cargue la versión más reciente

---

## Variables de entorno — resumen

### Agent (Lambda)
| Variable | Descripción |
|---|---|
| `ANTHROPIC_API_KEY` | API key de Anthropic |
| `TELEGRAM_BOT_TOKEN` | Token del bot de Telegram |
| `TELEGRAM_CHAT_ID` | Chat ID numérico autorizado |
| `TELEGRAM_SECRET_TOKEN` | Secret para validar webhook (requerido) |
| `AGENT_LAMBDA_NAME` | Nombre de la función jarbis-agent |
| `DYNAMODB_TABLE_*` | Nombres de las tablas DynamoDB |
| `AWS_REGION` | Región AWS |
| `GOOGLE_CALENDAR_CREDENTIALS` | token.json en base64 |
| `GOOGLE_CALENDAR_ID` | ID del calendario (`primary` o específico) |
| `EVENTBRIDGE_ROLE_ARN` | ARN del rol para EventBridge Scheduler |
| `DISPATCHER_LAMBDA_ARN` | ARN de jarbis-reminder-dispatcher |

### Dashboard backend (Render)
| Variable | Descripción |
|---|---|
| `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` | Credenciales IAM |
| `AWS_REGION` | Región AWS |
| `DYNAMODB_TABLE_*` | Nombres de las tablas |
| `GOOGLE_CALENDAR_CREDENTIALS` | token.json en base64 |
| `GOOGLE_CALENDAR_ID` | ID del calendario |
| `DASHBOARD_ACCESS_TOKEN` | Token de acceso al dashboard |
| `CORS_ALLOWED_ORIGINS` | Dominio del frontend (ej: `https://jarbis.vercel.app`) |

### Dashboard frontend (Vercel)
| Variable | Descripción |
|---|---|
| `VITE_API_URL` | URL del backend en Render |

---

## Ejemplos de uso

```
"gasté 15,000 won en ramen"
"desayuné avena con fruta, unas 400 calorías"
"crea un evento el viernes a las 7pm, cena con amigos"
"recuérdame llamar al doctor mañana a las 9am"
"cuánto gasté este mes?"
"cómo voy con las calorías hoy?"
"qué tengo esta semana?"
"cambia mi presupuesto mensual a 800,000 won"
"corrige el almuerzo de hoy, fueron 650 calorías no 400"
"borra el gasto de transporte del lunes"
```
