"""
Muestra las tablas de Notion que ve tu integración, con su ID.

Sirve para saber exactamente qué poner en NOTION_DATABASE_ID (y en los demás
NOTION_DB_*) dentro de tu .env, sin tener que adivinar desde la URL.

Ejecuta:  py mostrar_ids.py
"""

import config
from notion_client import Client

if not config.NOTION_TOKEN:
    raise SystemExit("Falta NOTION_TOKEN en tu .env.")

notion = Client(auth=config.NOTION_TOKEN)
resultado = notion.search(filter={"property": "object", "value": "database"})
tablas = resultado.get("results", [])

if not tablas:
    print(
        "\nNo encontré ninguna tabla. Revisa que hayas conectado tu integración "
        "a la página de Notion (··· → Conexiones).\n"
    )
else:
    print("\nTus tablas y sus IDs:\n")
    for d in tablas:
        nombre = "".join(t["plain_text"] for t in d.get("title", [])) or "(sin título)"
        print(f"  {nombre:<16} =>  {d['id']}")
    print(
        "\n👉 Copia el ID de la tabla 'Día' y ponlo en NOTION_DATABASE_ID de tu .env.\n"
        "   (Finanzas → NOTION_DB_FINANZAS, Aprendizajes → NOTION_DB_APRENDIZAJES,\n"
        "    Diario → NOTION_DB_DIARIO.)\n"
    )
