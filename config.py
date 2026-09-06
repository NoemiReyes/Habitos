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
NOTION_DATABASE_ID = os.getenv("NOTION_DATABASE_ID", "")  # tabla "Día" (Fase 1)
# IDs de las tablas de fases futuras (opcionales por ahora, se usarán después).
NOTION_DB_FINANZAS = os.getenv("NOTION_DB_FINANZAS", "")
NOTION_DB_APRENDIZAJES = os.getenv("NOTION_DB_APRENDIZAJES", "")
NOTION_DB_DIARIO = os.getenv("NOTION_DB_DIARIO", "")
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
# ÁREAS (facetas) del coach — el diseño modular.
# ---------------------------------------------------------------------------
# El agente es UN solo coach con varias facetas. Cada área tiene su comando
# (/salud, /finanzas...). Hoy solo "salud" está activa (Fase 1); las demás
# responden un mensaje de "próximamente" hasta que las construyamos.
# Para activar una faceta en el futuro: pon "activa": True y sigue la guía de
# CLAUDE.md ("Cómo agregar una faceta nueva").
AREAS = [
    {"clave": "salud",    "nombre": "Salud y alimentación",       "emoji": "🥗", "comando": "salud",    "fase": 1, "activa": True},
    {"clave": "finanzas", "nombre": "Finanzas personales",        "emoji": "💰", "comando": "finanzas", "fase": 2, "activa": False},
    {"clave": "mente",    "nombre": "Mentalidad y crecimiento",   "emoji": "🧠", "comando": "mente",    "fase": 3, "activa": False},
    {"clave": "negocio",  "nombre": "Negocio y clientes",         "emoji": "🤝", "comando": "negocio",  "fase": 3, "activa": False},
    {"clave": "diario",   "nombre": "Diario y reflexión",         "emoji": "📖", "comando": "diario",   "fase": 4, "activa": False},
]

# Área por defecto cuando escribes sin elegir foco.
AREA_POR_DEFECTO = "salud"


def area_por_clave(clave: str) -> dict | None:
    return next((a for a in AREAS if a["clave"] == clave), None)

# ---------------------------------------------------------------------------
# Nombres de las columnas en tu base de datos de Notion.
# Deben coincidir EXACTAMENTE con las propiedades de tu base.
# El script setup_notion.py crea la base con estos nombres automáticamente.
# ---------------------------------------------------------------------------
# --- Tabla "Día" (Fase 1 — la que usa el bot HOY) ---
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

# ---------------------------------------------------------------------------
# Tablas de las FASES FUTURAS (estructura inicial; se afinará al construir
# cada fase). setup_notion.py las crea todas de una vez para dejar tu Notion
# completo, aunque el bot todavía solo escribe en la tabla "Día".
# ---------------------------------------------------------------------------

# --- Tabla "Finanzas" (Fase 2) — una fila por movimiento ---
PROP_FINANZAS = {
    "concepto": "Concepto",   # título, ej. "Súper"
    "fecha": "Fecha",         # fecha
    "tipo": "Tipo",           # select: Gasto / Ingreso / Ahorro
    "monto": "Monto",         # número
    "categoria": "Categoría", # select
    "nota": "Nota",           # texto
}

# --- Tabla "Aprendizajes" (Fase 3 — mente + negocio) — una fila por entrada ---
PROP_APRENDIZAJES = {
    "titulo": "Título",       # título, ej. "Cap. 3 de Hábitos Atómicos"
    "fecha": "Fecha",         # fecha
    "area": "Área",           # select: Lectura / Curso / Cliente / Prospecto / Hábito
    "detalle": "Detalle",     # texto
    "avance": "Avance",       # texto, ej. "20 páginas"
    "nota": "Nota",           # texto
}

# --- Tabla "Diario" (Fase 4) — una fila por día/reflexión ---
PROP_DIARIO = {
    "fecha": "Fecha",             # título (texto con la fecha)
    "animo": "Ánimo",             # select: Bien / Neutral / Mal
    "entrada": "Entrada",         # texto: lo que escribiste
    "tema": "Tema",               # select: Emociones / Gratitud / Reto / Logro / Reflexión
    "aprendizaje": "Aprendizaje", # texto
}
