"""
Script de autorización OAuth2 para Google Calendar.
Ejecutar UNA SOLA VEZ localmente para generar token.json.

Uso:
    python auth_calendar.py

Requiere credentials.json en el mismo directorio.
"""

from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ["https://www.googleapis.com/auth/calendar"]

flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
creds = flow.run_local_server(port=0)

with open("token.json", "w") as f:
    f.write(creds.to_json())

print("token.json guardado correctamente.")
print("\nPara usar en Lambda, encodea con:")
print('  python -c "import base64; print(base64.b64encode(open(\'token.json\',\'rb\').read()).decode())"')
