"""
Repara las tablas de Notion que quedaron con columnas incompletas.

Si creaste las tablas con notion-client 3.x, la API nueva ignoró las columnas
y solo dejó la de título ("Name"). Este script les agrega las columnas
correctas y renombra el título, usando los IDs de tu .env. No borra nada ni
crea tablas nuevas: repara las que ya tienes.

Ejecuta (una vez):  py arreglar_tablas.py
"""

import config
from notion_client import Client

if not config.NOTION_TOKEN:
    raise SystemExit("Falta NOTION_TOKEN en tu .env.")

notion = Client(auth=config.NOTION_TOKEN)


def sel(*opciones):
    colores = ["green", "yellow", "red", "blue", "purple", "orange", "pink", "gray"]
    return {
        "select": {
            "options": [
                {"name": n, "color": colores[i % len(colores)]}
                for i, n in enumerate(opciones)
            ]
        }
    }


def numero():
    return {"number": {"format": "number"}}


def actualizar(db_id: str, titulo: str, columnas: dict) -> bool:
    """Renombra la columna de título a `titulo` y agrega/asegura `columnas`."""
    if not db_id:
        return False
    actual = notion.databases.retrieve(database_id=db_id)
    props = dict(columnas)
    for nombre, p in actual["properties"].items():
        if p["type"] == "title" and nombre != titulo:
            props[nombre] = {"name": titulo}  # renombra el título por defecto
    notion.databases.update(database_id=db_id, properties=props)
    return True


P, F, A, D = (
    config.PROP,
    config.PROP_FINANZAS,
    config.PROP_APRENDIZAJES,
    config.PROP_DIARIO,
)

hechas = []

if actualizar(config.NOTION_DATABASE_ID, P["fecha"], {
    P["levantarse"]: {"rich_text": {}},
    P["ejercicio"]: numero(),
    P["alimentacion"]: sel("Buena", "Regular", "Mala"),
    P["clientes"]: numero(),
    P["finanzas"]: {"checkbox": {}},
    P["crecimiento"]: {"checkbox": {}},
    P["animo"]: sel("Bien", "Neutral", "Mal"),
    P["puntaje"]: numero(),
    P["notas"]: {"rich_text": {}},
}):
    hechas.append("Día")

if actualizar(config.NOTION_DB_FINANZAS, F["concepto"], {
    F["fecha"]: {"date": {}},
    F["tipo"]: sel("Gasto", "Ingreso", "Ahorro"),
    F["monto"]: numero(),
    F["categoria"]: sel("Comida", "Transporte", "Salud", "Negocio", "Ocio", "Hogar", "Otro"),
    F["nota"]: {"rich_text": {}},
}):
    hechas.append("Finanzas")

if actualizar(config.NOTION_DB_APRENDIZAJES, A["titulo"], {
    A["fecha"]: {"date": {}},
    A["area"]: sel("Lectura", "Curso", "Cliente", "Prospecto", "Hábito"),
    A["detalle"]: {"rich_text": {}},
    A["avance"]: {"rich_text": {}},
    A["nota"]: {"rich_text": {}},
}):
    hechas.append("Aprendizajes")

if actualizar(config.NOTION_DB_DIARIO, D["fecha"], {
    D["animo"]: sel("Bien", "Neutral", "Mal"),
    D["entrada"]: {"rich_text": {}},
    D["tema"]: sel("Emociones", "Gratitud", "Reto", "Logro", "Reflexión"),
    D["aprendizaje"]: {"rich_text": {}},
}):
    hechas.append("Diario")

print("\n✅ Tablas reparadas:", ", ".join(hechas) if hechas else "ninguna")
print("Ahora enciende el bot con:  py bot.py\n")
