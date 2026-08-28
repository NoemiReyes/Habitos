"""
El "buzón" web que recibe los datos de tu Apple Watch.

Tu iPhone (con un Atajo de Apple) envía cada día tu sueño y tu ejercicio a este
buzón, y aquí se guardan en Notion como parte del registro del día. Como
`guardar_dia` combina registros parciales, estos datos se juntan con lo que tú
escribas por Telegram.

Se enciende solo junto con el bot (si defines WEBHOOK_TOKEN en tu .env).
También puedes correrlo aparte para probar:  python webhook.py
"""

from __future__ import annotations

import datetime as dt
import json
import threading
import urllib.parse
import urllib.request
from pathlib import Path

from flask import Flask, jsonify, request

import config
import notion_store

_ARCHIVO_CHATS = Path(__file__).parent / "suscriptores.json"


def _a_entero(valor):
    """Convierte '25', 25.0 o 25 a 25; devuelve None si no se puede."""
    if valor in (None, ""):
        return None
    try:
        return int(round(float(valor)))
    except (TypeError, ValueError):
        return None


def _normaliza_hora(valor):
    """Deja la hora en formato HH:MM (acepta '7:5', '07:05', '7:05 AM'...)."""
    if not valor:
        return None
    texto = str(valor).strip().upper().replace("A. M.", "AM").replace("P. M.", "PM")
    ampm = "AM" if "AM" in texto else ("PM" if "PM" in texto else "")
    texto = texto.replace("AM", "").replace("PM", "").strip()
    try:
        h, m = texto.split(":")[:2]
        h, m = int(h), int(m)
    except (ValueError, IndexError):
        return None
    if ampm == "PM" and h < 12:
        h += 12
    if ampm == "AM" and h == 12:
        h = 0
    return f"{h:02d}:{m:02d}"


def _notificar_telegram(texto: str) -> None:
    """Avisa por Telegram a los suscriptores que llegaron datos del reloj."""
    if not (config.TELEGRAM_TOKEN and _ARCHIVO_CHATS.exists()):
        return
    try:
        chats = json.loads(_ARCHIVO_CHATS.read_text())
    except (ValueError, OSError):
        return
    url = f"https://api.telegram.org/bot{config.TELEGRAM_TOKEN}/sendMessage"
    for chat_id in chats:
        try:
            datos = urllib.parse.urlencode({"chat_id": chat_id, "text": texto}).encode()
            urllib.request.urlopen(urllib.request.Request(url, data=datos), timeout=10)
        except Exception:  # noqa: BLE001 — un aviso fallido no debe tumbar el buzón
            pass


def crear_app() -> Flask:
    app = Flask(__name__)

    @app.get("/")
    def salud():
        return "Buzón de Hábitos activo ✅"

    @app.post("/apple")
    def apple():
        entrada = request.get_json(force=True, silent=True) or {}

        # Seguridad: la palabra secreta debe coincidir.
        if not config.WEBHOOK_TOKEN or entrada.get("token") != config.WEBHOOK_TOKEN:
            return jsonify({"error": "token inválido"}), 401

        fecha = dt.date.today().isoformat()
        levantarse = _normaliza_hora(entrada.get("levantarse_hora"))
        ejercicio = _a_entero(entrada.get("ejercicio_min"))
        pasos = _a_entero(entrada.get("pasos"))

        notas = []
        if pasos is not None:
            notas.append(f"{pasos} pasos")
        datos = {
            "levantarse_hora": levantarse,
            "ejercicio_min": ejercicio,
            "notas": ("⌚ Apple Watch: " + ", ".join(notas)) if notas else None,
        }

        try:
            guardado = notion_store.guardar_dia(fecha, datos)
        except Exception as e:  # noqa: BLE001
            return jsonify({"error": str(e)}), 500

        # Aviso amable por Telegram con lo que llegó del reloj.
        partes = []
        if levantarse:
            partes.append(f"despertaste {levantarse}")
        if ejercicio is not None:
            partes.append(f"{ejercicio} min de ejercicio")
        if pasos is not None:
            partes.append(f"{pasos} pasos")
        if partes:
            _notificar_telegram("⌚ Recibí de tu Apple Watch: " + ", ".join(partes) + ".")

        return jsonify({"ok": True, "puntaje": guardado["puntaje"]})

    return app


def iniciar_en_hilo() -> None:
    """Arranca el buzón en segundo plano, junto al bot (un solo proceso)."""
    app = crear_app()
    hilo = threading.Thread(
        target=lambda: app.run(host="0.0.0.0", port=config.WEBHOOK_PORT),
        daemon=True,
    )
    hilo.start()


if __name__ == "__main__":
    crear_app().run(host="0.0.0.0", port=config.WEBHOOK_PORT)
