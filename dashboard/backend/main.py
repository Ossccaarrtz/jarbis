import os
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv

load_dotenv()

from routers import expenses, nutrition, calendar, reminders, summary

app = FastAPI(title="Jarbis Dashboard API")

ALLOWED_ORIGINS = [o.strip() for o in os.environ.get(
    "CORS_ALLOWED_ORIGINS",
    "https://jarbis-sand.vercel.app"
).split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)

security = HTTPBearer()

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = os.environ.get("DASHBOARD_ACCESS_TOKEN", "")
    if not token or credentials.credentials != token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    return credentials.credentials

app.include_router(expenses.router,   prefix="/api/expenses",   tags=["expenses"],   dependencies=[Depends(verify_token)])
app.include_router(nutrition.router,  prefix="/api/nutrition",  tags=["nutrition"],  dependencies=[Depends(verify_token)])
app.include_router(calendar.router,   prefix="/api/calendar",   tags=["calendar"],   dependencies=[Depends(verify_token)])
app.include_router(reminders.router,  prefix="/api/reminders",  tags=["reminders"],  dependencies=[Depends(verify_token)])
app.include_router(summary.router,    prefix="/api/summary",    tags=["summary"],    dependencies=[Depends(verify_token)])

@app.api_route("/health", methods=["GET", "HEAD"])
def health():
    return {"status": "ok"}
