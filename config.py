"""
Configuración central del agente de hábitos.

Aquí defines TUS hábitos, tus metas y las horas de recordatorio.
Cambia los valores de este archivo para adaptar el agente a tu vida.
No hace falta tocar el resto del código para ajustar metas.
"""

import os
from dotenv import load_dotenv

load_dotenv()  # lee las variables secretas del archivo .env

# ---------------------------------------------------------------------------
# Claves y secretos (se leen del archivo .env, NUNCA se escriben aquí)
# ---------------------------------------------------------------------------
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "")
NOTION_TOKEN = os.getenv("NOTION_TOKEN", "")
NOTION_DATABASE_ID = os.getenv("NOTION_DATABASE_ID", "")
# La API de Claude toma la clave de ANTHROPIC_API_KEY automáticamente.

# Modelo del "coach". Opus 5 es el más capaz y empático.
# Si quieres gastar menos, puedes cambiarlo en tu .env a:
#   COACH_MODEL=claude-haiku-4-5   (más barato y rápido)
#   COACH_MODEL=claude-sonnet-5    (punto medio)
COACH_MODEL = os.getenv("COACH_MODEL", "claude-opus-5")

# ---------------------------------------------------------------------------
# Webhook para Apple Watch (Atajos de Apple)
# ---------------------------------------------------------------------------
# Si defines WEBHOOK_TOKEN en tu .env, el bot abrirá un "buzón" web para recibir
# los datos que tu iPhone le mande (sueño, ejercicio...). Debe ser una palabra
# secreta que tú inventes; la misma que pondrás en el Atajo de tu iPhone.
WEBHOOK_TOKEN = os.getenv("WEBHOOK_TOKEN", "")
# Puerto donde escucha el buzón. En hostings como Railway/Render se usa PORT.
WEBHOOK_PORT = int(os.getenv("PORT", os.getenv("WEBHOOK_PORT", "8080")))

# ---------------------------------------------------------------------------
# Horas de recordatorio (formato 24h, hora local del servidor donde corre)
# ---------------------------------------------------------------------------
HORA_RECORDATORIO_MANANA = os.getenv("HORA_MANANA", "07:00")
HORA_RECORDATORIO_NOCHE = os.getenv("HORA_NOCHE", "21:00")

# ---------------------------------------------------------------------------
# TUS HÁBITOS Y METAS
# ---------------------------------------------------------------------------
# Cada hábito tiene:
#   - nombre: cómo se muestra
#   - peso:   cuántos puntos (de 100) vale ese hábito en tu "puntaje del día"
# Ajusta los pesos según lo que más te importe. Deben sumar ~100.
METAS = {
    # Hora máxima a la que quieres levantarte (si te levantas a esta hora o
    # antes, cuenta como cumplido).
    "levantarse_antes_de": os.getenv("META_LEVANTARSE", "07:00"),

    # Minutos mínimos de ejercicio para contar el día como cumplido.
    "ejercicio_min": int(os.getenv("META_EJERCICIO_MIN", "20")),

    # Cuántos clientes/prospectos nuevos quieres contactar al día.
    "clientes_por_dia": int(os.getenv("META_CLIENTES", "3")),
}

# Pesos del puntaje diario (0 a 100). Personalízalos.
PESOS = {
    "levantarse": 20,
    "ejercicio": 20,
    "alimentacion": 20,
    "clientes": 20,
    "finanzas": 10,
    "crecimiento": 10,
}

# ---------------------------------------------------------------------------
# Nombres de las columnas en tu base de datos de Notion.
# Deben coincidir EXACTAMENTE con las propiedades de tu base.
# El script setup_notion.py crea la base con estos nombres automáticamente.
# ---------------------------------------------------------------------------
PROP = {
    "fecha": "Fecha",             # título (texto con la fecha, ej. 2026-08-28)
    "levantarse": "Levantarse",   # texto, ej. "07:10"
    "ejercicio": "Ejercicio (min)",  # número
    "alimentacion": "Alimentación",  # select: Buena / Regular / Mala
    "clientes": "Clientes",       # número
    "finanzas": "Finanzas",       # checkbox
    "crecimiento": "Crecimiento", # checkbox
    "animo": "Ánimo",             # select: Bien / Neutral / Mal
    "puntaje": "Puntaje",         # número 0-100
    "notas": "Notas",             # texto
}
