"""
Crea tus tablas de hábitos en Notion automáticamente (todas las fases).

Úsalo UNA sola vez. Crea 4 bases de datos dentro de la página que le indiques:
  1) Día          → hábitos diarios (Fase 1, la que usa el bot HOY)
  2) Finanzas     → movimientos de dinero (Fase 2)
  3) Aprendizajes → lecturas, cursos, clientes (Fase 3)
  4) Diario       → reflexiones (Fase 4)

Necesitas:
  1) NOTION_TOKEN en tu .env (el "Internal Integration Secret").
  2) El ID de una página de Notion donde vivirán las tablas, y haber
     "conectado" tu integración a esa página (··· → Conexiones).

Ejecuta:  python setup_notion.py <id_de_pagina>
Al terminar te imprime los IDs que debes pegar en tu .env.
"""

import sys

from notion_client import Client

import config

# Puedes pegar aquí el ID de la página padre, o pasarlo como argumento.
PAGINA_PADRE = ""


# --- Ayudas para describir columnas de forma legible ---
def titulo():
    return {"title": {}}


def texto():
    return {"rich_text": {}}


def numero():
    return {"number": {"format": "number"}}


def fecha():
    return {"date": {}}


def casilla():
    return {"checkbox": {}}


def seleccion(*opciones):
    colores = ["green", "yellow", "red", "blue", "purple", "orange", "pink", "gray"]
    return {
        "select": {
            "options": [
                {"name": nombre, "color": colores[i % len(colores)]}
                for i, nombre in enumerate(opciones)
            ]
        }
    }


def _crear(notion, padre, nombre, propiedades):
    db = notion.databases.create(
        parent={"type": "page_id", "page_id": padre},
        title=[{"type": "text", "text": {"content": nombre}}],
        properties=propiedades,
    )
    return db["id"]


def main() -> None:
    pagina_padre = sys.argv[1] if len(sys.argv) > 1 else PAGINA_PADRE
    if not config.NOTION_TOKEN:
        raise SystemExit("Falta NOTION_TOKEN en tu .env.")
    if not pagina_padre:
        raise SystemExit(
            "Falta el ID de la página padre. Ejecútalo así:\n"
            "  python setup_notion.py <id_de_pagina>"
        )

    notion = Client(auth=config.NOTION_TOKEN)
    F, A, D = config.PROP_FINANZAS, config.PROP_APRENDIZAJES, config.PROP_DIARIO
    P = config.PROP

    # 1) Día (Fase 1) — la que usa el bot hoy
    id_dia = _crear(notion, pagina_padre, "Día", {
        P["fecha"]: titulo(),
        P["levantarse"]: texto(),
        P["ejercicio"]: numero(),
        P["alimentacion"]: seleccion("Buena", "Regular", "Mala"),
        P["clientes"]: numero(),
        P["finanzas"]: casilla(),
        P["crecimiento"]: casilla(),
        P["animo"]: seleccion("Bien", "Neutral", "Mal"),
        P["puntaje"]: numero(),
        P["notas"]: texto(),
    })

    # 2) Finanzas (Fase 2)
    id_fin = _crear(notion, pagina_padre, "Finanzas", {
        F["concepto"]: titulo(),
        F["fecha"]: fecha(),
        F["tipo"]: seleccion("Gasto", "Ingreso", "Ahorro"),
        F["monto"]: numero(),
        F["categoria"]: seleccion(
            "Comida", "Transporte", "Salud", "Negocio", "Ocio", "Hogar", "Otro"
        ),
        F["nota"]: texto(),
    })

    # 3) Aprendizajes (Fase 3 — mente + negocio)
    id_apr = _crear(notion, pagina_padre, "Aprendizajes", {
        A["titulo"]: titulo(),
        A["fecha"]: fecha(),
        A["area"]: seleccion("Lectura", "Curso", "Cliente", "Prospecto", "Hábito"),
        A["detalle"]: texto(),
        A["avance"]: texto(),
        A["nota"]: texto(),
    })

    # 4) Diario (Fase 4)
    id_dia_rio = _crear(notion, pagina_padre, "Diario", {
        D["fecha"]: titulo(),
        D["animo"]: seleccion("Bien", "Neutral", "Mal"),
        D["entrada"]: texto(),
        D["tema"]: seleccion("Emociones", "Gratitud", "Reto", "Logro", "Reflexión"),
        D["aprendizaje"]: texto(),
    })

    print("\n✅ ¡Tus 4 tablas fueron creadas en Notion!\n")
    print("Pega esto en tu archivo .env:\n")
    print("# --- Fase 1 (la que usa el bot ahora) ---")
    print(f"NOTION_DATABASE_ID={id_dia}\n")
    print("# --- Fases futuras: guárdalos, se usarán más adelante ---")
    print(f"NOTION_DB_FINANZAS={id_fin}")
    print(f"NOTION_DB_APRENDIZAJES={id_apr}")
    print(f"NOTION_DB_DIARIO={id_dia_rio}\n")


if __name__ == "__main__":
    main()
