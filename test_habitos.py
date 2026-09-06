"""
Pruebas automáticas de la lógica del agente (no tocan Notion ni Telegram).

Ejecútalas con:   python -m pytest -q
Sirven para asegurar que el puntaje, las rachas y la lectura de datos del
Apple Watch siguen funcionando aunque cambiemos el código más adelante.
"""

import datetime as dt

import config
import notion_store as ns
import webhook as wh


# --------------------------------------------------------------------------- #
# Puntaje del día
# --------------------------------------------------------------------------- #
def test_puntaje_dia_perfecto():
    datos = dict(
        levantarse_hora="06:50", ejercicio_min=30, alimentacion="buena",
        clientes_contactados=3, finanzas_registrado=True, crecimiento=True,
    )
    assert ns.calcular_puntaje(datos) == 100


def test_puntaje_dia_flojo():
    # Alimentación regular (10) + 1 cliente aunque no llegue a la meta (10) = 20
    datos = dict(
        levantarse_hora="08:30", ejercicio_min=0, alimentacion="regular",
        clientes_contactados=1, finanzas_registrado=False, crecimiento=False,
    )
    assert ns.calcular_puntaje(datos) == 20


def test_puntaje_dia_vacio():
    assert ns.calcular_puntaje({}) == 0


# --------------------------------------------------------------------------- #
# Mapeo de valores a las opciones de Notion
# --------------------------------------------------------------------------- #
def test_map_alimentacion():
    assert ns._map_alimentacion("buena") == "Buena"
    assert ns._map_alimentacion("no_mencionado") is None
    assert ns._map_alimentacion(None) is None


def test_map_animo():
    assert ns._map_animo("mal") == "Mal"
    assert ns._map_animo("") is None


# --------------------------------------------------------------------------- #
# Constancia / rachas (lógica pura)
# --------------------------------------------------------------------------- #
def _fila(fecha, levantarse, ejercicio, alimentacion, clientes, fin, crec, punt):
    return dict(fecha=fecha, levantarse=levantarse, ejercicio=ejercicio,
                alimentacion=alimentacion, clientes=clientes, finanzas=fin,
                crecimiento=crec, puntaje=punt)


def test_estadisticas_rachas_y_cumplimiento():
    hoy = dt.date(2026, 9, 6)
    filas = [
        _fila("2026-09-06", "06:50", 30, "Buena", 3, True, True, 100),
        _fila("2026-09-05", "06:55", 0, "Regular", 0, False, False, 30),
        _fila("2026-09-04", "08:00", 25, "Mala", 5, True, False, 50),
    ]
    st = ns.estadisticas_desde_filas(filas, hoy=hoy)

    assert st["racha_registro"] == 3          # 3 días seguidos con registro
    assert st["racha_levantarse"] == 2        # hoy y ayer a tiempo; antier no
    assert st["promedio_puntaje_7d"] == 60    # (100+30+50)/3
    assert st["dias_registrados_total"] == 3

    c = st["cumplimiento_7d"]
    assert c["levantarse"] == 67   # 2 de 3
    assert c["ejercicio"] == 67    # 2 de 3 (30 y 25 min)
    assert c["clientes"] == 67     # 2 de 3 (3 y 5)
    assert c["crecimiento"] == 33  # 1 de 3


def test_estadisticas_sin_datos():
    st = ns.estadisticas_desde_filas([], hoy=dt.date(2026, 9, 6))
    assert st["racha_registro"] == 0
    assert st["dias_registrados_total"] == 0
    assert st["promedio_puntaje_7d"] == 0


# --------------------------------------------------------------------------- #
# Webhook del Apple Watch: normalización de hora y números
# --------------------------------------------------------------------------- #
def test_normaliza_hora():
    assert wh._normaliza_hora("7:5") == "07:05"
    assert wh._normaliza_hora("7:05 AM") == "07:05"
    assert wh._normaliza_hora("9:30 PM") == "21:30"
    assert wh._normaliza_hora("12:00 AM") == "00:00"
    assert wh._normaliza_hora("") is None
    assert wh._normaliza_hora("cualquier cosa") is None


def test_a_entero():
    assert wh._a_entero("25.0") == 25
    assert wh._a_entero(30) == 30
    assert wh._a_entero("") is None
    assert wh._a_entero(None) is None
    assert wh._a_entero("hola") is None


# --------------------------------------------------------------------------- #
# Diseño modular: registro de áreas
# --------------------------------------------------------------------------- #
def test_areas_configuradas():
    claves = {a["clave"] for a in config.AREAS}
    assert {"salud", "finanzas", "mente", "negocio", "diario"} <= claves
    salud = config.area_por_clave("salud")
    assert salud and salud["activa"] is True          # Fase 1 activa
    assert config.area_por_clave("finanzas")["activa"] is False
    assert config.area_por_clave("inexistente") is None
