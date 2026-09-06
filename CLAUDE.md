# Arquitectura del proyecto — Hábitos

Guía para entender el código y hacerlo crecer sin romperlo. Léela antes de
agregar funcionalidad.

## La idea: un coach, muchas facetas

Es **un solo agente** (un bot de Telegram, un cerebro de Claude, una base de
Notion) que crece por **áreas/facetas**: salud, finanzas, mente, negocio y
diario. No son bots separados: comparten contexto para poder "conectar los
puntos" entre áreas.

El estado actual es la **Fase 1**: solo la faceta **salud** está activa. Las
demás existen como comandos que responden "próximamente".

## Piezas

| Archivo | Responsabilidad |
|---|---|
| `config.py` | Ajustes, metas, pesos del puntaje y el registro de `AREAS`. |
| `coach.py` | Claude: interpreta el mensaje libre y genera la respuesta del coach. |
| `notion_store.py` | Escribe en Notion y calcula constancia/rachas. |
| `bot.py` | Telegram: comandos, mensajes, recordatorios. Punto de arranque. |
| `webhook.py` | Buzón HTTP que recibe datos del Apple Watch (Atajos de Apple). |
| `setup_notion.py` | Crea la base de datos de Notion (una sola vez). |
| `test_habitos.py` | Pruebas de la lógica pura (puntaje, rachas, webhook, áreas). |

## Reglas de diseño

- **La lógica pura se separa de la I/O.** Lo que se puede probar sin red vive en
  funciones puras (ej. `notion_store.estadisticas_desde_filas`,
  `notion_store.calcular_puntaje`, `webhook._normaliza_hora`). Al agregar
  lógica, hazla pura y cúbrela en `test_habitos.py`.
- **Notion se accede por nombre de propiedad**, definido en `config.PROP`. Si
  renombras una columna en Notion, actualiza `config.PROP`.
- **Registros parciales:** `guardar_dia` combina lo nuevo con lo ya guardado del
  día, para poder registrar por partes (mañana + noche + Apple Watch).
- **Nunca** subir `.env` ni `suscriptores.json` (ya están en `.gitignore`).

## Verificar antes de subir cambios

```bash
python -m pytest -q            # todas las pruebas en verde
python -m py_compile *.py      # sin errores de sintaxis
```

## Cómo agregar una faceta nueva (Fases 2+)

Cuando construyamos, por ejemplo, **finanzas**:

1. **Activa el área** en `config.py`: en `AREAS`, cambia `"activa": True` para
   `finanzas`.
2. **Tabla en Notion:** crea su base (ej. movimientos) y añade su creación a
   `setup_notion.py`. Define sus nombres de propiedad en un `PROP_FINANZAS`.
3. **Guardado:** crea `finanzas_store.py` (espejo de `notion_store.py`) con su
   función de guardar y sus consultas; mantén la lógica de cálculo **pura**.
4. **Interpretación:** en `coach.py`, agrega una herramienta de extracción para
   esa área (ej. `registrar_movimiento`) y un enrutador que elija el área según
   el mensaje o el foco activo (`ctx.user_data["area"]`).
5. **Enrutar el mensaje:** en `bot.py`, `registrar` decide a qué store va según
   el área activa. Hoy siempre va a salud; ahí es donde se ramifica.
6. **Pruebas:** agrega casos a `test_habitos.py` para la lógica pura nueva.
7. **Documenta** la faceta en el `README.md`.

Mantén cada faceta con la misma forma (interpretar → guardar → responder) para
que el patrón sea predecible.

## Roadmap

- **Fase 1 (actual):** Salud + Apple Watch. ✅
- **Fase 2:** Finanzas personales.
- **Fase 3:** Mentalidad/crecimiento y Negocio/clientes.
- **Fase 4:** Diario/reflexión + reporte semanal (une todas las áreas).
