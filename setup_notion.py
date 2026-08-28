"""
Crea tu base de datos de hábitos en Notion automáticamente.

Úsalo UNA sola vez. Necesitas:
  1) NOTION_TOKEN en tu .env (el "Internal Integration Secret").
  2) El ID de una página de Notion donde vivirá la base (PAGINA_PADRE abajo),
     y haber "conectado" tu integración a esa página (··· → Conexiones).

Al terminar, te imprime el NOTION_DATABASE_ID que debes pegar en tu .env.
"""

import sys

from notion_client import Client

import config

# Pega aquí el ID de la página de Notion donde quieres que se cree la base.
# Es la parte final de la URL de la página (32 caracteres), o pásalo como
# argumento:  python setup_notion.py <id_de_pagina>
PAGINA_PADRE = ""

P = config.PROP


def main() -> None:
    pagina_padre = sys.argv[1] if len(sys.argv) > 1 else PAGINA_PADRE
    if not config.NOTION_TOKEN:
        raise SystemExit("Falta NOTION_TOKEN en tu .env.")
    if not pagina_padre:
        raise SystemExit(
            "Falta el ID de la página padre. Edita PAGINA_PADRE en este archivo "
            "o ejecútalo así:\n  python setup_notion.py <id_de_pagina>"
        )

    notion = Client(auth=config.NOTION_TOKEN)
    db = notion.databases.create(
        parent={"type": "page_id", "page_id": pagina_padre},
        title=[{"type": "text", "text": {"content": "Hábitos Diarios"}}],
        properties={
            P["fecha"]: {"title": {}},
            P["levantarse"]: {"rich_text": {}},
            P["ejercicio"]: {"number": {}},
            P["alimentacion"]: {
                "select": {
                    "options": [
                        {"name": "Buena", "color": "green"},
                        {"name": "Regular", "color": "yellow"},
                        {"name": "Mala", "color": "red"},
                    ]
                }
            },
            P["clientes"]: {"number": {}},
            P["finanzas"]: {"checkbox": {}},
            P["crecimiento"]: {"checkbox": {}},
            P["animo"]: {
                "select": {
                    "options": [
                        {"name": "Bien", "color": "green"},
                        {"name": "Neutral", "color": "gray"},
                        {"name": "Mal", "color": "red"},
                    ]
                }
            },
            P["puntaje"]: {"number": {"format": "number"}},
            P["notas"]: {"rich_text": {}},
        },
    )

    print("\n✅ ¡Base de datos creada!\n")
    print("Pega esta línea en tu archivo .env:\n")
    print(f"NOTION_DATABASE_ID={db['id']}\n")


if __name__ == "__main__":
    main()
