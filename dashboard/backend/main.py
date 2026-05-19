import os
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv

load_dotenv()

from routers import expenses, nutrition, calendar, reminders, summary

app = FastAPI(title="Jarbis Dashboard API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
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

@app.get("/health")
def health():
    return {"status": "ok"}
