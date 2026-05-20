# Jarbis — Contexto del Proyecto

## ¿Qué es Jarbis?

Asistente personal 100% agentic compuesto de dos partes:

1. **Agente Telegram** — recibe mensajes en lenguaje natural, decide qué tools llamar, y ejecuta acciones reales
2. **Dashboard web** — visualiza toda la data registrada por el agente (gastos, nutrición, agenda, recordatorios)

El objetivo es reemplazar apps como Notion, Google Keep, MyFitnessPal y Splitwise con un solo asistente conversacional + un dashboard propio.

---

## Arquitectura completa

```
Usuario (Telegram)
  → mensaje en lenguaje natural
    → API Gateway (AWS)
      → Lambda A: jarbis-handler
          · responde 200 a Telegram inmediato (evita timeout 5s)
          · valida secret_token del webhook y chat_id autorizado
          · invoca Lambda B async (InvocationType=Event)
        → Lambda B: jarbis-agent
            · recupera historial conversacional de DynamoDB (últimos 10 mensajes)
            · llama Claude Haiku 3.5 con definiciones de tools
            · loop agentic: Claude decide qué tools llamar
            · ejecuta tools, verifica resultados (anti-alucinación)
            · guarda turno en jarbis-conversations
            · envía respuesta al usuario por Telegram Bot API

Reminders one-shot
  → EventBridge Scheduler
    → Lambda C: jarbis-reminder-dispatcher
        · envía mensaje por Telegram
        · marca reminder como sent=true en DynamoDB

Dashboard
  → React + Vite (Vercel)
    → FastAPI (Render)
      → DynamoDB (expenses, meals, reminders, preferences)
      → Google Calendar API
```

### Patrón async para evitar timeout de Telegram

Telegram espera respuesta del webhook en ~5 segundos. El flujo es:

1. `handler.py` (Lambda A) recibe el webhook, responde `200 OK` inmediatamente
2. `handler.py` invoca async (InvocationType=Event) a `agent_runner.py` (Lambda B)
3. `agent_runner.py` ejecuta el loop agentic sin presión de tiempo
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

**Costo total estimado: ~$0-1/mes** (uso personal).

---

## Estructura de archivos (estado actual)

```
jarbis/
├── CLAUDE.md
├── README.md
├── agent/
│   ├── handler.py              # Lambda A — webhook → invoca agente async
│   ├── agent_runner.py         # Lambda B — runtime del loop
│   ├── agent.py                # Loop agentic: Claude + tools + history + verificación
│   ├── conversation.py         # Lectura/escritura de jarbis-conversations
│   ├── scheduler.py            # Crea EventBridge Schedules para reminders
│   ├── reminder_dispatcher.py  # Lambda C — dispara reminders en su hora
│   ├── storage.py              # Operaciones DynamoDB
│   ├── telegram.py             # send_message, send_typing
│   ├── google_calendar.py      # Wrapper Google Calendar API
│   ├── auth_calendar.py        # Script OAuth2 local (correr una vez)
│   ├── main.py                 # Entry local (polling) para desarrollo
│   ├── deploy.sh               # Build Docker Linux + zip + deploy
│   ├── requirements.txt
│   └── tools/
│       ├── __init__.py         # TOOLS + execute_tool()
│       ├── expenses.py         # save, get_summary, get_recent, update, delete, delete_bulk
│       ├── nutrition.py        # log, get_summary, get_recent, update, delete, delete_bulk
│       ├── calendar.py         # create, list, update, delete (con verificación post-acción)
│       ├── reminders.py        # set_reminder, list_reminders, cancel_reminder
│       └── preferences.py      # save_preference, get_preference
└── dashboard/
    ├── backend/                # FastAPI
    │   ├── main.py             # App, CORS, auth Bearer
    │   ├── db.py               # Recurso DynamoDB + helpers
    │   ├── requirements.txt
    │   └── routers/
    │       ├── summary.py      # GET /api/summary
    │       ├── expenses.py     # GET /api/expenses, /today, /weekly
    │       ├── nutrition.py    # GET /api/nutrition, /today, /weekly
    │       ├── calendar.py     # GET /api/calendar
    │       └── reminders.py    # GET /api/reminders
    └── frontend/               # React + Vite + Tailwind
        ├── src/
        │   ├── App.jsx
        │   ├── main.jsx
        │   ├── lib/
        │   │   ├── api.js      # Fetch wrapper con Bearer token
        │   │   └── utils.js    # formatKRW, formatDate, categoryColor, etc.
        │   ├── components/
        │   │   ├── Layout.jsx
        │   │   ├── StatCard.jsx
        │   │   └── Skeleton.jsx
        │   └── pages/
        │       ├── Home.jsx        # Inicio: resumen del día + mes + próximos eventos
        │       ├── Daily.jsx       # Vista por día: date picker + donut + comidas
        │       ├── Expenses.jsx    # Historial de gastos
        │       ├── Nutrition.jsx   # Calorías y comidas
        │       ├── Agenda.jsx      # Calendario + reminders
        │       └── Login.jsx
        └── public/
            └── sw.js           # Service Worker no-cache (PWA iOS)
```

---

## Tools del agente (estado actual)

### Gastos (`tools/expenses.py`)
- `save_expense(amount, category, description, currency)` — guarda un gasto
- `get_expense_summary(start_date, end_date)` — resume gastos en un rango ISO8601
- `get_recent_expenses(limit)` — lista los últimos gastos para identificar IDs
- `update_expense(sk, ...)` — edita un gasto existente
- `delete_expense(sk)` — borra un gasto por su SK
- `delete_expenses_bulk(sks)` — borra varios en lote

### Nutrición (`tools/nutrition.py`)
- `log_meal(description, calories, meal_type)` — registra una comida
- `get_nutrition_summary(start_date, end_date)` — calorías + comidas en rango
- `get_recent_meals(limit)` — últimas comidas con sus SKs
- `update_meal(sk, ...)` — edita una comida
- `delete_meal(sk)` — borra una comida
- `delete_meals_bulk(sks)` — borra varias en lote

### Calendario (`tools/calendar.py`)
- `create_calendar_event(title, datetime, description, location, duration_minutes)`
- `list_events(days_ahead)` — próximos eventos
- `update_calendar_event(event_id, ...)` — edita un evento
- `delete_calendar_event(event_id)` — borra (con verificación post-acción)

### Recordatorios (`tools/reminders.py`)
- `set_reminder(message, datetime)` — guarda en DynamoDB + crea EventBridge Schedule
- `list_reminders()` — lista pendientes
- `cancel_reminder(sk)` — borra reminder + Schedule asociado

### Preferencias (`tools/preferences.py`)
- `save_preference(key, value)` — guarda budget mensual/semanal, meta calórica, timezone, etc.
- `get_preference(key)` — lee una preferencia
- Internamente existe `get_all_preferences()` (no expuesta como tool) usada para inyectar contexto en el system prompt y para el dashboard

---

## Anti-alucinación

El agente verifica cada operación de escritura/borrado antes de confirmarla al usuario:
- Después de `create_calendar_event` / `update_calendar_event` / `delete_calendar_event`, se vuelve a consultar el evento para confirmar el cambio
- En operaciones de DynamoDB, los handlers devuelven el item afectado para que Claude lo cite explícitamente
- Si una verificación falla, el agente reporta el error en lugar de afirmar el éxito

---

## DynamoDB — diseño de tablas

| Tabla | PK | SK | Atributos clave | TTL |
|---|---|---|---|---|
| `jarbis-expenses` | `user_id` | `YYYY-MM-DDTHH:MM:SS#uuid` | amount, category, currency, description | 1 año |
| `jarbis-meals` | `user_id` | `YYYY-MM-DDTHH:MM:SS#uuid` | calories, meal_type, description | 1 año |
| `jarbis-reminders` | `user_id` | `remind_at#schedule_name` | message, sent, remind_at | al enviarse |
| `jarbis-preferences` | `user_id` | `key` | value | — |
| `jarbis-conversations` | `user_id` | `ISO8601 timestamp` | role, content | 24 horas |

---

## Flujo de recordatorios

```
set_reminder(message, datetime)
  → guarda en jarbis-reminders (DynamoDB) con sent=false
  → scheduler.py crea EventBridge Schedule one-shot
      → target: jarbis-reminder-dispatcher (Lambda C)
      → payload: { user_id, sk, message }
  → en la fecha/hora: EventBridge invoca Lambda C
      → envía mensaje por Telegram Bot API
      → marca reminder como sent=true en DynamoDB
```

`cancel_reminder` también borra el Schedule de EventBridge para que no se dispare.

---

## Contexto conversacional

Al inicio de cada invocación de `agent.py`:
1. Consultar `jarbis-conversations` con `user_id`, ordenado por SK, últimos N items
2. Pasar ese historial como `messages` a Claude (antes del mensaje nuevo)
3. Al terminar, guardar el mensaje del usuario y la respuesta del asistente en la tabla

Permite flujos multi-turno:
```
"¿cuánto gasté hoy?" → "Gastaste 45,000 won"
"¿y la semana pasada?" → Claude tiene contexto
```

Además, las preferencias del usuario (budget, meta calórica, timezone) se inyectan en el system prompt al inicio del loop.

---

## Google Calendar — OAuth2

Calendar personal requiere OAuth2 (no service account):

1. Crear proyecto en Google Cloud Console, habilitar Calendar API
2. Crear OAuth2 credentials (Desktop app), descargar `credentials.json`
3. Correr `python auth_calendar.py` localmente → genera `token.json`
4. Encodear `token.json` en base64 → `GOOGLE_CALENDAR_CREDENTIALS`
5. El Lambda usa el `refresh_token` para obtener access tokens en cada ejecución

---

## Dashboard — vistas implementadas

### Home (`/`)
- Stat cards: gastado hoy, calorías hoy, próximo evento
- Barra de progreso calórico vs meta diaria
- Donut de gastos del mes por categoría + leyenda
- Barra de progreso budget mensual
- Próximos 3 eventos

### Día (`/daily`)
- Date picker (no permite fechas futuras, botón "Hoy")
- Stat cards: total gastado y nº transacciones; calorías totales y nº comidas
- Donut de gastos por categoría con leyenda + lista de transacciones del día
- Comidas agrupadas por tipo (desayuno/almuerzo/cena/snack) con hora, descripción y kcal

### Gastos (`/expenses`)
- Historial filtrable por rango
- Gráficas por categoría y semana

### Nutrición (`/nutrition`)
- Calorías del día vs meta
- Breakdown de comidas
- Progreso calórico semanal

### Agenda (`/agenda`)
- Próximos 14 días de Google Calendar
- Recordatorios pendientes

### Autenticación
- Bearer token validado en FastAPI (`DASHBOARD_ACCESS_TOKEN`)
- Guardado en localStorage del frontend

---

## Variables de entorno

### Agent (Lambda)
```
ANTHROPIC_API_KEY=
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=                  # solo este chat_id puede interactuar
TELEGRAM_SECRET_TOKEN=             # validado contra el header del webhook
AGENT_LAMBDA_NAME=jarbis-agent
DYNAMODB_TABLE_EXPENSES=jarbis-expenses
DYNAMODB_TABLE_MEALS=jarbis-meals
DYNAMODB_TABLE_REMINDERS=jarbis-reminders
DYNAMODB_TABLE_PREFERENCES=jarbis-preferences
DYNAMODB_TABLE_CONVERSATIONS=jarbis-conversations
AWS_REGION=us-east-1
GOOGLE_CALENDAR_CREDENTIALS=       # token.json en base64
GOOGLE_CALENDAR_ID=primary
EVENTBRIDGE_ROLE_ARN=
DISPATCHER_LAMBDA_ARN=
```

### Dashboard backend (FastAPI / Render)
```
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
AWS_REGION=us-east-1
DYNAMODB_TABLE_EXPENSES=jarbis-expenses
DYNAMODB_TABLE_MEALS=jarbis-meals
DYNAMODB_TABLE_REMINDERS=jarbis-reminders
DYNAMODB_TABLE_PREFERENCES=jarbis-preferences
GOOGLE_CALENDAR_CREDENTIALS=
GOOGLE_CALENDAR_ID=primary
DASHBOARD_ACCESS_TOKEN=
CORS_ALLOWED_ORIGINS=https://jarbis-sand.vercel.app
```

### Dashboard frontend (Vite / Vercel)
```
VITE_API_URL=https://your-backend.onrender.com
```

---

## Cómo funciona el loop agentic

1. Usuario manda mensaje por Telegram
2. API Gateway dispara Lambda A (`handler.py`)
3. `handler.py` valida `secret_token` y `chat_id`, responde `200 OK`
4. `handler.py` invoca Lambda B async
5. `agent.py` inyecta preferencias + historial conversacional en el contexto
6. Loop: Claude responde con tool_use o texto final
7. Si tool_use: `execute_tool` ejecuta el handler, agrega resultado al contexto, vuelve a 6
8. Cuando Claude responde con texto sin tool_use: respuesta final
9. `agent.py` guarda el turno en `jarbis-conversations`
10. Lambda B envía la respuesta al usuario por Telegram Bot API

---

## Seguridad

- `chat_id` del webhook validado contra `TELEGRAM_CHAT_ID` (rechaza cualquier otro)
- `secret_token` del webhook validado en `handler.py` — el arranque falla si la env var no está
- CORS del dashboard restringido a los orígenes en `CORS_ALLOWED_ORIGINS`
- Dashboard requiere `DASHBOARD_ACCESS_TOKEN` (Bearer) en cada request
- `credentials.json` y `token.json` están en `.gitignore`

---

## Ejemplos de uso

```
"gasté 15,000 won en ramen"
→ save_expense(amount=15000, category="comida", currency="KRW")

"desayuné avena con fruta, unas 400 calorías"
→ log_meal(description="avena con fruta", calories=400, meal_type="desayuno")

"recuérdame llamar a mamá mañana a las 7pm"
→ set_reminder(message="Llamar a mamá", datetime="...")

"cómo voy con el budget este mes?"
→ get_expense_summary(start_date=..., end_date=...) + get_preference("budget_monthly_KRW")

"qué tengo mañana?"
→ list_events(days_ahead=1)

"borra el gasto de transporte del lunes"
→ get_recent_expenses → delete_expense(sk=...)

"corrige el almuerzo de hoy, eran 650 calorías no 400"
→ get_recent_meals → update_meal(sk=..., calories=650)

"hoy fui al gym, dormí 7 horas, gasté 30,000 won y comí bien"
→ múltiples tools en el mismo loop
```

---

## Decisiones de diseño

- **Claude Haiku 3.5 sobre LLaMA** — tool calling más confiable con input en español; costo mínimo
- **DynamoDB sobre PostgreSQL** — serverless, sin conexión persistente, free tier generoso
- **Dos Lambdas (handler + agent_runner)** — responder a Telegram en <5s y procesar sin timeout
- **Lambda dispatcher separado para reminders** — EventBridge invoca solo cuando toca; no consume invocaciones extra
- **EventBridge Scheduler sobre cron Lambda** — limpio para reminders one-shot
- **FastAPI separado del agente** — el dashboard lee data, no necesita el LLM
- **Una tabla por entidad** — más simple de queryar que single-table design para este caso
- **Polling local (`main.py`) para desarrollo** — ciclo de iteración rápido sin re-deployar Lambda
- **Verificación post-acción** — el agente vuelve a leer el recurso después de escribir/borrar para no alucinar éxitos
- **Vercel + Render** — ya conocidos del stack previo
