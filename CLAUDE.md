# Jarbis — Contexto del Proyecto

## ¿Qué es Jarbis?

Asistente personal 100% agentic compuesto de dos partes:

1. **Agente Telegram** — recibe mensajes en lenguaje natural, decide qué tools llamar, y ejecuta acciones reales
2. **Dashboard web** — visualiza toda la data registrada por el agente (gastos, nutrición, agenda, recordatorios)

El objetivo es reemplazar apps como Notion, Google Keep, MyFitnessPal, y Splitwise con un solo asistente conversacional + un dashboard propio.

---

## Arquitectura completa

```
Usuario (Telegram)
  → mensaje en lenguaje natural
    → API Gateway
      → Lambda handler (responde 200 inmediatamente a Telegram)
        → invoca Lambda agente async
          → Claude Haiku 3.5 (decide qué tools usar)
            → Tools:
                save_expense          → DynamoDB
                get_expense_summary   → DynamoDB
                log_meal              → DynamoDB
                get_nutrition_summary → DynamoDB
                create_calendar_event → Google Calendar API
                list_events           → Google Calendar API
                set_reminder          → DynamoDB + EventBridge Scheduler
            → recupera historial conversacional de DynamoDB
            → responde al usuario por Telegram

Dashboard (React)
  → FastAPI (Render)
    → DynamoDB (gastos, comidas, recordatorios)
    → Google Calendar API (eventos)
```

### Patrón async para evitar timeout de Telegram

Telegram espera respuesta del webhook en ~5 segundos. El flujo es:

1. `handler.py` (Lambda A) recibe el webhook, responde `200 OK` a API Gateway de inmediato
2. `handler.py` invoca de forma async (InvocationType=Event) a `agent_runner.py` (Lambda B)
3. `agent_runner.py` ejecuta el loop agentic completo sin presión de tiempo
4. `agent_runner.py` envía la respuesta final al usuario por Telegram Bot API

---

## Stack

| Componente | Servicio | Costo |
|---|---|---|
| Interfaz conversacional | Telegram Bot API | Gratis |
| Trigger | AWS API Gateway | Free tier |
| Runtime agente | AWS Lambda Python 3.12 | Free tier |
| LLM | Claude Haiku 3.5 (Anthropic) | ~$0.80/1M tokens |
| Persistencia | AWS DynamoDB | Free tier |
| Calendario | Google Calendar API | Gratis |
| Recordatorios scheduler | AWS EventBridge Scheduler | Free tier |
| Backend dashboard | FastAPI en Render | Free tier |
| Frontend dashboard | React + Vite + Tailwind en Vercel | Gratis |

**Costo total estimado: ~$0-1/mes** (según volumen de mensajes; uso personal = centavos)

---

## Estructura de archivos

```
jarbis/
├── CLAUDE.md                      # este archivo
├── agent/                         # agente Telegram + Lambda
│   ├── handler.py                 # Lambda A — responde 200, invoca agente async
│   ├── agent_runner.py            # Lambda B — loop agentic completo
│   ├── agent.py                   # lógica del loop: llama Claude, ejecuta tools, itera
│   ├── conversation.py            # lectura/escritura de historial conversacional
│   ├── scheduler.py               # creación de EventBridge Schedules para reminders
│   ├── tools/
│   │   ├── expenses.py            # save_expense, get_expense_summary
│   │   ├── nutrition.py           # log_meal, get_nutrition_summary
│   │   ├── calendar.py            # create_calendar_event, list_events
│   │   └── reminders.py          # set_reminder
│   ├── storage.py                 # operaciones DynamoDB
│   ├── telegram.py                # send_message helper
│   ├── deploy.sh                  # deploy a Lambda
│   ├── requirements.txt
│   └── .env.example
└── dashboard/                     # dashboard web
    ├── backend/                   # FastAPI
    │   ├── main.py
    │   ├── routers/
    │   │   ├── expenses.py
    │   │   ├── nutrition.py
    │   │   └── calendar.py
    │   └── requirements.txt
    └── frontend/                  # React + Vite
        ├── src/
        │   ├── components/
        │   │   ├── BudgetCard.jsx
        │   │   ├── ExpenseChart.jsx
        │   │   ├── NutritionSummary.jsx
        │   │   └── AgendaWidget.jsx
        │   └── pages/
        │       └── Dashboard.jsx
        └── package.json
```

---

## Tools del agente

### Gastos
- `save_expense(amount, category, description, currency)` — guarda un gasto
- `get_expense_summary(start_date, end_date)` — resume gastos en un rango de fechas (ISO8601: "2026-05-01"). Claude calcula las fechas desde el lenguaje natural ("últimas 2 semanas", "este mes", "hoy")

### Nutrición
- `log_meal(description, calories, meal_type)` — registra una comida
- `get_nutrition_summary(start_date, end_date)` — calorías y comidas en un rango de fechas

### Calendario
- `create_calendar_event(title, datetime, description)` — crea evento en Google Calendar
- `list_events(days_ahead)` — lista próximos eventos

### Recordatorios
- `set_reminder(message, datetime)` — guarda en `jarbis-reminders` + crea un EventBridge Schedule que invoca el Lambda dispatcher en la fecha/hora indicada

---

## DynamoDB — diseño de tablas

### Tabla: `jarbis-expenses`
- PK: `user_id` (string)
- SK: `timestamp#uuid` (string)
- Atributos: `amount`, `category`, `description`, `currency`, `expires_at`
- TTL: 1 año

### Tabla: `jarbis-meals`
- PK: `user_id` (string)
- SK: `timestamp#uuid` (string)
- Atributos: `description`, `calories`, `meal_type`, `expires_at`
- TTL: 1 año

### Tabla: `jarbis-reminders`
- PK: `user_id` (string)
- SK: `remind_at#uuid` (string)
- Atributos: `message`, `sent`, `expires_at`
- TTL: automático al enviarse

### Tabla: `jarbis-conversations`
- PK: `user_id` (string)
- SK: `timestamp` (string ISO8601)
- Atributos: `role` (user/assistant), `content`
- TTL: 24 horas
- Uso: contexto conversacional — se recuperan los últimos N mensajes al inicio de cada loop

---

## Flujo de recordatorios

```
set_reminder(message, datetime)
  → guarda en jarbis-reminders (DynamoDB)
  → llama scheduler.py → crea EventBridge Schedule one-time
      → target: Lambda dispatcher (agent_runner o lambda dedicado)
      → payload: { user_id, message }
  → en la fecha/hora: EventBridge invoca Lambda
      → Lambda envía mensaje por Telegram Bot API
      → marca reminder como sent=true en DynamoDB
```

---

## Contexto conversacional

Al inicio de cada invocación de `agent.py`:
1. Consultar `jarbis-conversations` con `user_id`, ordenado por SK, últimos 10 items
2. Pasar ese historial como `messages` a Claude (antes del mensaje nuevo)
3. Al terminar, guardar el mensaje del usuario y la respuesta del asistente en la tabla

Esto permite flujos multi-turno como:
```
"¿cuánto gasté hoy?" → "Gastaste 45,000 won"
"¿y la semana pasada?"  → Claude tiene contexto, sabe a qué se refiere
```

---

## Google Calendar — OAuth2

Google Calendar personal requiere OAuth2 (no service account). El flujo de setup es:

1. Crear proyecto en Google Cloud Console, habilitar Calendar API
2. Crear OAuth2 credentials (Desktop app)
3. Correr script local de autorización una sola vez → genera `token.json` con `refresh_token`
4. Encodear `token.json` en base64 y guardar en env vars del Lambda
5. El Lambda usa el `refresh_token` para obtener access tokens en cada ejecución

El `GOOGLE_CALENDAR_CREDENTIALS` es el `token.json` (con refresh_token), **no** el `credentials.json` del proyecto GCP.

---

## Dashboard — vistas

### Vista principal
- Resumen del día: calorías consumidas, gastos del día, próximo evento
- Budget del mes: barra de progreso gastado vs restante
- Próximos 3 eventos de Google Calendar

### Sección gastos
- Gráfica de dona por categoría (Recharts)
- Historial de transacciones del mes
- Comparativa semana a semana (LineChart)

### Sección nutrición
- Calorías del día vs meta diaria
- Breakdown de comidas registradas hoy
- Progreso calórico semanal (BarChart)

### Sección agenda
- Vista de próximos 7 días
- Eventos de Google Calendar integrados
- Recordatorios pendientes

### Autenticación del dashboard
- Basic auth via header validado en FastAPI (simple para uso personal)
- Token de acceso fijo en variable de entorno, enviado desde el frontend

---

## Variables de entorno

### Agent (Lambda)
```
ANTHROPIC_API_KEY=
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=                  # solo este chat_id puede interactuar con el bot
DYNAMODB_TABLE_EXPENSES=jarbis-expenses
DYNAMODB_TABLE_MEALS=jarbis-meals
DYNAMODB_TABLE_REMINDERS=jarbis-reminders
DYNAMODB_TABLE_CONVERSATIONS=jarbis-conversations
AWS_REGION=us-east-1
GOOGLE_CALENDAR_CREDENTIALS=       # token.json completo, base64 encoded
GOOGLE_CALENDAR_ID=
AGENT_LAMBDA_NAME=                 # nombre del Lambda B (agent_runner) para invocación async
```

### Dashboard backend (FastAPI)
```
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
AWS_REGION=us-east-1
DYNAMODB_TABLE_EXPENSES=jarbis-expenses
DYNAMODB_TABLE_MEALS=jarbis-meals
DYNAMODB_TABLE_REMINDERS=jarbis-reminders
GOOGLE_CALENDAR_CREDENTIALS=
GOOGLE_CALENDAR_ID=
DASHBOARD_ACCESS_TOKEN=            # token fijo para basic auth del dashboard
```

---

## Cómo funciona el loop agentic

1. Usuario manda mensaje por Telegram
2. API Gateway dispara Lambda A (`handler.py`)
3. `handler.py` responde `200 OK` inmediatamente (evita timeout de Telegram)
4. `handler.py` invoca Lambda B (`agent_runner.py`) de forma async (InvocationType=Event)
5. `agent_runner.py` llama a `agent.py`
6. `agent.py` recupera historial de `jarbis-conversations`
7. `agent.py` manda historial + mensaje nuevo + definiciones de tools a Claude Haiku
8. Claude responde con tool_use o texto final
9. Si tool_use: ejecuta la tool, agrega resultado al contexto, vuelve al paso 7
10. Cuando Claude responde con texto (sin tool_use): es la respuesta final
11. `agent.py` guarda el turno en `jarbis-conversations`
12. Lambda B envía la respuesta al usuario por Telegram Bot API

---

## Seguridad

- Validar que el `chat_id` del webhook coincide con `TELEGRAM_CHAT_ID` (rechazar cualquier otro)
- Configurar `secret_token` en el webhook de Telegram (`setWebhook`) y validarlo en `handler.py`
- El dashboard requiere `DASHBOARD_ACCESS_TOKEN` en cada request

---

## Ejemplos de uso esperado

```
"gasté 15,000 won en ramen"
→ save_expense(amount=15000, category="comida", currency="KRW")

"desayuné avena con fruta, unas 400 calorías"
→ log_meal(description="avena con fruta", calories=400, meal_type="desayuno")

"recuérdame llamar a mamá mañana a las 7pm"
→ set_reminder(message="Llamar a mamá", datetime="mañana 7pm")

"cómo voy con el budget este mes?"
→ get_expense_summary(start_date="2026-05-01", end_date="2026-05-31")

"cuánto gasté las últimas 2 semanas?"
→ get_expense_summary(start_date="2026-05-05", end_date="2026-05-19")

"qué tengo mañana?"
→ list_events(days_ahead=1)

"hoy fui al gym, dormí 7 horas, gasté 30,000 won y comí bien"
→ múltiples tools en secuencia (Claude hace varios tool_use en el mismo loop)
```

---

## Orden de desarrollo

1. **Agente base en modo polling local** — sin Lambda, sin API Gateway; correr `python agent.py` localmente con Telegram polling para iterar rápido
2. **Tool: gastos** — save_expense + get_expense_summary + DynamoDB
3. **Tool: nutrición** — log_meal + get_nutrition_summary
4. **Contexto conversacional** — agregar jarbis-conversations antes de añadir más tools
5. **Migrar a Lambda + API Gateway** — wrappear lo que ya funciona; implementar patrón async (Lambda A → Lambda B)
6. **Tool: calendario** — Google Calendar OAuth2 setup + create_calendar_event + list_events
7. **Tool: recordatorios** — set_reminder + EventBridge Scheduler + Lambda dispatcher
8. **Dashboard backend** — FastAPI leyendo DynamoDB
9. **Dashboard frontend** — React + Recharts
10. **Deploy completo** — Vercel + Render + Lambda en producción

---

## Decisiones de diseño

- **Claude Haiku 3.5 sobre LLaMA** — tool calling más confiable, especialmente con input en español; costo mínimo para uso personal
- **DynamoDB sobre PostgreSQL** — serverless, no necesita conexión persistente desde Lambda, free tier generoso
- **Dos Lambdas (handler + agent_runner)** — para responder a Telegram en <5s y procesar sin timeout
- **EventBridge Scheduler sobre cron Lambda** — más limpio para reminders one-shot; no gasta invocaciones innecesarias
- **Lambda sobre servidor siempre encendido** — el trigger es el mensaje de Telegram, no necesita estar corriendo 24/7
- **FastAPI separado del agente** — el dashboard lee data, no necesita el LLM, separar concerns
- **Vercel + Render** — ya conocidos del stack de XchangeBusan
- **Una tabla por entidad** — más simple de queryar por tipo de dato que Single Table Design para este caso
- **Polling local para desarrollo** — ciclo de iteración mucho más rápido que deploy a Lambda en cada cambio
