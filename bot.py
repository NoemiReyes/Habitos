"""
El bot de Telegram: es la "voz" del agente en tu teléfono.

Qué hace:
  - /start   → te registra y agenda tus recordatorios diarios.
  - /resumen → te muestra tus rachas y constancia.
  - /ayuda   → explica cómo usarlo.
  - Cualquier texto normal → lo interpreta como el registro de tu día, lo
    guarda en Notion y te responde como tu coach.
  - Te escribe solo en la mañana y en la noche para acompañarte.

Para que los recordatorios funcionen, este programa debe estar CORRIENDO
(en tu compu encendida o en un hosting gratis). Ver el README.
"""

from __future__ import annotations

import asyncio
import datetime as dt
import json
import logging
from pathlib import Path

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

import coach
import config
import notion_store

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
log = logging.getLogger("habitos")

# Guardamos aquí el chat_id de quien usa el bot, para poder escribirle solo.
_ARCHIVO_CHATS = Path(__file__).parent / "suscriptores.json"


def _cargar_chats() -> set[int]:
    if _ARCHIVO_CHATS.exists():
        return set(json.loads(_ARCHIVO_CHATS.read_text()))
    return set()


def _guardar_chat(chat_id: int) -> None:
    chats = _cargar_chats()
    chats.add(chat_id)
    _ARCHIVO_CHATS.write_text(json.dumps(sorted(chats)))


# ---------------------------------------------------------------------------
# Comandos
# ---------------------------------------------------------------------------
async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    _guardar_chat(chat_id)
    _agendar_recordatorios(ctx.application, chat_id)
    await update.message.reply_text(
        "¡Hola! 🌱 Soy tu coach de hábitos.\n\n"
        "Cada día cuéntame cómo te fue con un mensaje normal, por ejemplo:\n"
        "_«Me levanté 7:10, desayuné avena, 20 min de caminata, contacté 2 "
        "clientes y aparté para ahorro»_\n\n"
        "Yo lo registro en Notion, llevo tus rachas y te acompaño. "
        "Te escribiré en la mañana y en la noche.\n\n"
        "Comandos: /resumen para ver tu constancia · /ayuda",
        parse_mode=ParseMode.MARKDOWN,
    )


async def cmd_ayuda(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Escríbeme en lenguaje normal lo que hiciste hoy y yo lo registro.\n\n"
        "Llevo el seguimiento de:\n"
        "⏰ Hora de levantarte\n🥗 Alimentación\n🏃 Ejercicio\n"
        "🤝 Clientes contactados\n💰 Finanzas\n📚 Crecimiento personal/profesional\n\n"
        "Puedes registrar por partes: mándame cosas en la mañana y completar en la "
        "noche; junto todo en el mismo día.\n\n"
        "/resumen → tus rachas y % de constancia."
    )


async def cmd_resumen(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    await ctx.bot.send_chat_action(update.effective_chat.id, "typing")
    stats = await asyncio.to_thread(notion_store.calcular_estadisticas)
    await update.message.reply_text(
        coach.resumen_constancia(stats), parse_mode=ParseMode.MARKDOWN
    )


# ---------------------------------------------------------------------------
# Mensaje normal = registro del día
# ---------------------------------------------------------------------------
async def registrar(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    _guardar_chat(chat_id)
    await ctx.bot.send_chat_action(chat_id, "typing")

    mensaje = update.message.text
    fecha = dt.date.today().isoformat()

    try:
        datos = await asyncio.to_thread(coach.interpretar_mensaje, mensaje, fecha)
        guardado = await asyncio.to_thread(notion_store.guardar_dia, fecha, datos)
        stats = await asyncio.to_thread(notion_store.calcular_estadisticas)
        respuesta = await asyncio.to_thread(coach.responder, mensaje, guardado, stats)
    except Exception as e:  # noqa: BLE001 — mostramos un error amable
        log.exception("Error al registrar")
        await update.message.reply_text(
            "Uy, algo falló al guardar tu registro 😔. "
            f"Revisa la configuración (Notion / claves).\n\nDetalle técnico: {e}"
        )
        return

    await update.message.reply_text(respuesta)


# ---------------------------------------------------------------------------
# Recordatorios automáticos (mañana y noche)
# ---------------------------------------------------------------------------
async def _recordatorio_manana(ctx: ContextTypes.DEFAULT_TYPE) -> None:
    await ctx.bot.send_message(
        ctx.job.chat_id,
        "Buenos días 🌅 ¿A qué hora te levantaste y cómo amaneciste? "
        "Cuéntame tu plan para hoy.",
    )


async def _recordatorio_noche(ctx: ContextTypes.DEFAULT_TYPE) -> None:
    await ctx.bot.send_message(
        ctx.job.chat_id,
        "Cierre del día 🌙 ¿Cómo te fue? Cuéntame de tu alimentación, ejercicio, "
        "clientes, finanzas y si avanzaste en algo tuyo.",
    )


def _hora(texto: str) -> dt.time:
    h, m = texto.split(":")
    return dt.time(hour=int(h), minute=int(m))


def _agendar_recordatorios(app: Application, chat_id: int) -> None:
    """Agenda (o reagenda) los dos recordatorios diarios para un chat."""
    jq = app.job_queue
    for nombre in (f"manana_{chat_id}", f"noche_{chat_id}"):
        for job in jq.get_jobs_by_name(nombre):
            job.schedule_removal()
    jq.run_daily(
        _recordatorio_manana,
        time=_hora(config.HORA_RECORDATORIO_MANANA),
        chat_id=chat_id,
        name=f"manana_{chat_id}",
    )
    jq.run_daily(
        _recordatorio_noche,
        time=_hora(config.HORA_RECORDATORIO_NOCHE),
        chat_id=chat_id,
        name=f"noche_{chat_id}",
    )


async def _al_iniciar(app: Application) -> None:
    """Reagenda recordatorios para todos los suscriptores al arrancar."""
    for chat_id in _cargar_chats():
        _agendar_recordatorios(app, chat_id)
    log.info("Recordatorios reagendados para los suscriptores existentes.")


# ---------------------------------------------------------------------------
# Arranque
# ---------------------------------------------------------------------------
def main() -> None:
    faltantes = [
        n
        for n, v in {
            "TELEGRAM_TOKEN": config.TELEGRAM_TOKEN,
            "NOTION_TOKEN": config.NOTION_TOKEN,
            "NOTION_DATABASE_ID": config.NOTION_DATABASE_ID,
        }.items()
        if not v
    ]
    if faltantes:
        raise SystemExit(
            "Faltan variables de entorno: "
            + ", ".join(faltantes)
            + ".\nCopia .env.example a .env y complétalas. Ver README.md."
        )

    app = (
        Application.builder()
        .token(config.TELEGRAM_TOKEN)
        .post_init(_al_iniciar)
        .build()
    )
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("ayuda", cmd_ayuda))
    app.add_handler(CommandHandler("resumen", cmd_resumen))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, registrar))

    # Si configuraste el webhook, enciende el buzón para tu Apple Watch.
    if config.WEBHOOK_TOKEN:
        import webhook

        webhook.iniciar_en_hilo()
        log.info("Buzón de Apple Watch activo en el puerto %s.", config.WEBHOOK_PORT)

    log.info("Bot en marcha. Abre Telegram y escribe /start a tu bot.")
    app.run_polling()


if __name__ == "__main__":
    main()
