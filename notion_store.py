"""
Guardado y lectura de hábitos en Notion, y cálculo de tu constancia (rachas).

Este módulo es el "cuaderno" del agente: cada día se escribe una fila en tu
base de datos de Notion, y desde ahí se calculan tus rachas y porcentajes de
cumplimiento.
"""

from __future__ import annotations

import datetime as dt

from notion_client import Client

import config

_notion = Client(auth=config.NOTION_TOKEN) if config.NOTION_TOKEN else None
P = config.PROP


# ---------------------------------------------------------------------------
# Utilidades internas para leer/escribir propiedades de Notion
# ---------------------------------------------------------------------------
def _texto(valor: str) -> dict:
    return {"rich_text": [{"text": {"content": valor or ""}}]}


def _titulo(valor: str) -> dict:
    return {"title": [{"text": {"content": valor}}]}


def _leer_prop(page: dict, nombre: str):
    """Extrae el valor plano de una propiedad de una página de Notion."""
    prop = page.get("properties", {}).get(nombre)
    if not prop:
        return None
    tipo = prop["type"]
    if tipo == "number":
        return prop["number"]
    if tipo == "checkbox":
        return prop["checkbox"]
    if tipo == "select":
        return prop["select"]["name"] if prop["select"] else None
    if tipo in ("rich_text", "title"):
        partes = prop[tipo]
        return partes[0]["plain_text"] if partes else ""
    return None


def _map_alimentacion(valor: str | None) -> str | None:
    m = {"buena": "Buena", "regular": "Regular", "mala": "Mala"}
    return m.get((valor or "").lower())


def _map_animo(valor: str | None) -> str | None:
    m = {"bien": "Bien", "neutral": "Neutral", "mal": "Mal"}
    return m.get((valor or "").lower())


# ---------------------------------------------------------------------------
# Puntaje del día
# ---------------------------------------------------------------------------
def calcular_puntaje(datos: dict) -> int:
    """Convierte los hábitos del día en un puntaje 0-100 según los pesos."""
    pesos = config.PESOS
    metas = config.METAS
    puntos = 0

    hora = datos.get("levantarse_hora")
    if hora and hora <= metas["levantarse_antes_de"]:
        puntos += pesos["levantarse"]

    ej = datos.get("ejercicio_min")
    if ej is not None and ej >= metas["ejercicio_min"]:
        puntos += pesos["ejercicio"]

    alim = (datos.get("alimentacion") or "").lower()
    if alim == "buena":
        puntos += pesos["alimentacion"]
    elif alim == "regular":
        puntos += pesos["alimentacion"] // 2

    cli = datos.get("clientes_contactados")
    if cli is not None and cli >= metas["clientes_por_dia"]:
        puntos += pesos["clientes"]
    elif cli:  # contactó a alguien aunque no llegue a la meta
        puntos += pesos["clientes"] // 2

    if datos.get("finanzas_registrado"):
        puntos += pesos["finanzas"]
    if datos.get("crecimiento"):
        puntos += pesos["crecimiento"]

    return min(puntos, 100)


# ---------------------------------------------------------------------------
# Guardar / actualizar el registro de un día
# ---------------------------------------------------------------------------
def _buscar_pagina_del_dia(fecha: str) -> dict | None:
    r = _notion.databases.query(
        database_id=config.NOTION_DATABASE_ID,
        filter={"property": P["fecha"], "title": {"equals": fecha}},
    )
    res = r.get("results", [])
    return res[0] if res else None


def guardar_dia(fecha: str, datos: dict) -> dict:
    """
    Crea o actualiza la fila del día. `datos` son los campos ya interpretados
    del mensaje del usuario. Solo se sobreescriben los campos que vengan con
    valor (así puedes registrar por partes durante el día).
    Devuelve un resumen con el puntaje calculado.
    """
    existente = _buscar_pagina_del_dia(fecha)

    def previo(nombre):
        """Valor que ya estaba guardado hoy (o None si es un día nuevo)."""
        return _leer_prop(existente, nombre) if existente else None

    def elegir(nuevo, nombre, vacios=(None,)):
        """Usa el dato nuevo si vino con valor; si no, conserva el anterior."""
        return nuevo if nuevo not in vacios else previo(nombre)

    # Combinar lo que ya había con lo nuevo, para no borrar registros parciales.
    combinado = {
        "levantarse_hora": elegir(datos.get("levantarse_hora"), P["levantarse"]),
        "ejercicio_min": elegir(datos.get("ejercicio_min"), P["ejercicio"]),
        "alimentacion": elegir(
            datos.get("alimentacion"), P["alimentacion"], vacios=(None, "no_mencionado")
        ),
        "clientes_contactados": elegir(datos.get("clientes_contactados"), P["clientes"]),
        "finanzas_registrado": datos.get("finanzas_registrado") or previo(P["finanzas"]) or False,
        "crecimiento": datos.get("crecimiento") or previo(P["crecimiento"]) or False,
        "animo": elegir(datos.get("animo"), P["animo"], vacios=(None, "no_mencionado")),
    }

    puntaje = calcular_puntaje(combinado)

    # Construir las propiedades para Notion (solo las que tienen valor).
    propiedades: dict = {P["fecha"]: _titulo(fecha), P["puntaje"]: {"number": puntaje}}
    if combinado["levantarse_hora"]:
        propiedades[P["levantarse"]] = _texto(combinado["levantarse_hora"])
    if combinado["ejercicio_min"] is not None:
        propiedades[P["ejercicio"]] = {"number": combinado["ejercicio_min"]}
    alim = _map_alimentacion(combinado["alimentacion"])
    if alim:
        propiedades[P["alimentacion"]] = {"select": {"name": alim}}
    if combinado["clientes_contactados"] is not None:
        propiedades[P["clientes"]] = {"number": combinado["clientes_contactados"]}
    propiedades[P["finanzas"]] = {"checkbox": bool(combinado["finanzas_registrado"])}
    propiedades[P["crecimiento"]] = {"checkbox": bool(combinado["crecimiento"])}
    animo = _map_animo(combinado["animo"])
    if animo:
        propiedades[P["animo"]] = {"select": {"name": animo}}
    notas = datos.get("notas")
    if notas:
        propiedades[P["notas"]] = _texto(notas)

    if existente:
        _notion.pages.update(page_id=existente["id"], properties=propiedades)
    else:
        _notion.pages.create(
            parent={"database_id": config.NOTION_DATABASE_ID}, properties=propiedades
        )

    combinado["puntaje"] = puntaje
    return combinado


# ---------------------------------------------------------------------------
# Leer historial y calcular rachas / constancia
# ---------------------------------------------------------------------------
def _todas_las_paginas() -> list[dict]:
    paginas, cursor = [], None
    while True:
        r = _notion.databases.query(
            database_id=config.NOTION_DATABASE_ID,
            start_cursor=cursor,
            page_size=100,
        )
        paginas.extend(r["results"])
        if not r.get("has_more"):
            break
        cursor = r["next_start_cursor"] if "next_start_cursor" in r else r.get("next_cursor")
    return paginas


def _fila(page: dict) -> dict:
    return {
        "fecha": _leer_prop(page, P["fecha"]),
        "levantarse": _leer_prop(page, P["levantarse"]),
        "ejercicio": _leer_prop(page, P["ejercicio"]),
        "alimentacion": _leer_prop(page, P["alimentacion"]),
        "clientes": _leer_prop(page, P["clientes"]),
        "finanzas": _leer_prop(page, P["finanzas"]),
        "crecimiento": _leer_prop(page, P["crecimiento"]),
        "puntaje": _leer_prop(page, P["puntaje"]),
    }


def calcular_estadisticas() -> dict:
    """
    Devuelve un diccionario con la constancia del usuario:
      - racha_registro: días seguidos (hasta hoy) que registró algo
      - racha_levantarse: días seguidos cumpliendo la meta de levantarse
      - cumplimiento_7d: % de días (de los últimos 7) que cumplió cada hábito
      - promedio_puntaje_7d: puntaje promedio de la última semana
    """
    filas = [_fila(p) for p in _todas_las_paginas()]
    filas = [f for f in filas if f["fecha"]]
    por_fecha = {f["fecha"]: f for f in filas}

    hoy = dt.date.today()
    metas = config.METAS

    def cumple_levantarse(f):
        return bool(f["levantarse"]) and f["levantarse"] <= metas["levantarse_antes_de"]

    def cumple_ejercicio(f):
        return (f["ejercicio"] or 0) >= metas["ejercicio_min"]

    def cumple_clientes(f):
        return (f["clientes"] or 0) >= metas["clientes_por_dia"]

    # Rachas: contar hacia atrás desde hoy mientras se cumpla.
    racha_registro = 0
    d = hoy
    while por_fecha.get(d.isoformat()):
        racha_registro += 1
        d -= dt.timedelta(days=1)

    racha_levantarse = 0
    d = hoy
    while True:
        f = por_fecha.get(d.isoformat())
        if f and cumple_levantarse(f):
            racha_levantarse += 1
            d -= dt.timedelta(days=1)
        else:
            break

    # Cumplimiento de los últimos 7 días.
    ultimos7 = [por_fecha.get((hoy - dt.timedelta(days=i)).isoformat()) for i in range(7)]
    ultimos7 = [f for f in ultimos7 if f]
    n = max(len(ultimos7), 1)

    def pct(cond):
        return round(100 * sum(1 for f in ultimos7 if cond(f)) / n)

    cumplimiento_7d = {
        "levantarse": pct(cumple_levantarse),
        "ejercicio": pct(cumple_ejercicio),
        "alimentacion": pct(lambda f: (f["alimentacion"] or "") in ("Buena", "Regular")),
        "clientes": pct(cumple_clientes),
        "finanzas": pct(lambda f: bool(f["finanzas"])),
        "crecimiento": pct(lambda f: bool(f["crecimiento"])),
    }
    promedio = round(sum(f["puntaje"] or 0 for f in ultimos7) / n)

    return {
        "racha_registro": racha_registro,
        "racha_levantarse": racha_levantarse,
        "cumplimiento_7d": cumplimiento_7d,
        "promedio_puntaje_7d": promedio,
        "dias_registrados_total": len(filas),
    }
