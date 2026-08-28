"""
El "coach": interpreta lo que escribes y te responde.

Tiene dos trabajos:
  1) interpretar_mensaje(): convierte tu texto libre ("me levanté 7:10,
     desayuné avena, 0 ejercicio, contacté 2 clientes") en datos estructurados.
  2) responder(): te da un mensaje de acompañamiento con una personalidad
     comprensiva pero firme ("mas no barco"), tomando en cuenta tus rachas.

Usa la API de Claude (SDK oficial `anthropic`).
"""

from __future__ import annotations

import datetime as dt
import json

import anthropic

import config

_client = anthropic.Anthropic()  # toma la clave de ANTHROPIC_API_KEY


# Personalidad del coach. Este es el "corazón" del agente: ajústalo a tu gusto.
PERSONALIDAD = """\
Eres el coach personal de hábitos de la persona con la que hablas. Tu estilo es
COMPRENSIVO PERO NO BARCO (no eres permisivo): cálido, humano y sin culpa, pero
firme y honesto. No regañas, tampoco dejas pasar todo.

Principios:
- Celebra la constancia y las rachas: son la métrica que más importa, más que la
  perfección de un solo día.
- Si falló un hábito, no lo minimices ni lo dramatices: pregunta con curiosidad
  qué se atravesó y ayuda a definir el siguiente paso pequeño y concreto.
- Recuérdale sus metas y sus rachas activas para motivar sin presionar de más.
- Un mal día no rompe el proceso; dos o tres seguidos sí merecen una conversación
  honesta. Sé directo cuando veas una tendencia a la baja.
- Habla en español, en segunda persona (tú), breve (2-5 frases). Usa como mucho
  1 o 2 emojis. Nada de listas largas ni sermones.
- Nunca inventes datos: usa solo las cifras que te doy.
"""

# Herramienta que Claude usa para "leer" el mensaje y devolver datos limpios.
HERRAMIENTA_REGISTRO = {
    "name": "registrar_dia",
    "description": (
        "Extrae los hábitos que la persona menciona en su mensaje. "
        "Si un dato no se menciona, deja null (o 'no_mencionado' donde aplique). "
        "No inventes valores."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "levantarse_hora": {
                "type": ["string", "null"],
                "description": "Hora a la que se levantó, formato 24h HH:MM (ej. '07:10').",
            },
            "ejercicio_min": {
                "type": ["integer", "null"],
                "description": "Minutos de ejercicio. 0 si dice explícitamente que no hizo.",
            },
            "alimentacion": {
                "type": "string",
                "enum": ["buena", "regular", "mala", "no_mencionado"],
                "description": "Calidad general de su alimentación hoy.",
            },
            "clientes_contactados": {
                "type": ["integer", "null"],
                "description": "Cuántos clientes o prospectos nuevos contactó.",
            },
            "finanzas_registrado": {
                "type": "boolean",
                "description": "Si registró/revisó gastos, ahorro o finanzas hoy.",
            },
            "crecimiento": {
                "type": "boolean",
                "description": "Si hizo alguna acción de crecimiento personal o profesional (leer, curso, práctica, aprender algo).",
            },
            "animo": {
                "type": "string",
                "enum": ["bien", "neutral", "mal", "no_mencionado"],
                "description": "Estado de ánimo que transmite el mensaje.",
            },
            "notas": {
                "type": "string",
                "description": "Resumen muy breve del contexto, obstáculos o logros que cuente.",
            },
        },
        "required": [
            "levantarse_hora",
            "ejercicio_min",
            "alimentacion",
            "clientes_contactados",
            "finanzas_registrado",
            "crecimiento",
            "animo",
            "notas",
        ],
    },
}


def interpretar_mensaje(mensaje: str, fecha: str | None = None) -> dict:
    """Convierte el texto libre del usuario en un diccionario de hábitos."""
    fecha = fecha or dt.date.today().isoformat()
    respuesta = _client.messages.create(
        model=config.COACH_MODEL,
        max_tokens=1024,
        output_config={"effort": "low"},  # tarea sencilla: gastamos poco
        system=(
            f"Hoy es {fecha}. Extrae los hábitos del mensaje usando la herramienta. "
            "Interpreta lenguaje natural en español (ej. 'me paré 7 y media' = 07:30)."
        ),
        tools=[HERRAMIENTA_REGISTRO],
        tool_choice={"type": "tool", "name": "registrar_dia"},
        messages=[{"role": "user", "content": mensaje}],
    )
    for bloque in respuesta.content:
        if bloque.type == "tool_use" and bloque.name == "registrar_dia":
            return bloque.input
    return {}


def responder(mensaje: str, datos: dict, stats: dict) -> str:
    """Genera el mensaje de acompañamiento del coach."""
    contexto = {
        "lo_que_registro_hoy": datos,
        "constancia": stats,
        "metas": config.METAS,
    }
    respuesta = _client.messages.create(
        model=config.COACH_MODEL,
        max_tokens=600,
        output_config={"effort": "medium"},
        system=PERSONALIDAD,
        messages=[
            {
                "role": "user",
                "content": (
                    f"Este es el mensaje que te escribí:\n\"{mensaje}\"\n\n"
                    "Y estos son mis datos de hoy y mi constancia (en JSON):\n"
                    f"{json.dumps(contexto, ensure_ascii=False, indent=2)}\n\n"
                    "Respóndeme como mi coach."
                ),
            }
        ],
    )
    return "".join(b.text for b in respuesta.content if b.type == "text").strip()


def resumen_constancia(stats: dict) -> str:
    """Un texto corto con las rachas, para el comando /resumen."""
    c = stats["cumplimiento_7d"]
    return (
        f"📊 *Tu constancia*\n\n"
        f"🔥 Racha registrando: *{stats['racha_registro']} días*\n"
        f"⏰ Racha levantándote a tiempo: *{stats['racha_levantarse']} días*\n"
        f"⭐ Puntaje promedio (7 días): *{stats['promedio_puntaje_7d']}/100*\n\n"
        f"Cumplimiento últimos 7 días:\n"
        f"• Levantarse: {c['levantarse']}%\n"
        f"• Ejercicio: {c['ejercicio']}%\n"
        f"• Alimentación: {c['alimentacion']}%\n"
        f"• Clientes: {c['clientes']}%\n"
        f"• Finanzas: {c['finanzas']}%\n"
        f"• Crecimiento: {c['crecimiento']}%\n\n"
        f"Total de días registrados: {stats['dias_registrados_total']}"
    )
