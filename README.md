# 🌱 Hábitos — tu coach personal en Telegram

Un agente que cada día te pregunta cómo vas, registra tus hábitos en **Notion**
y te acompaña con una personalidad **comprensiva pero firme** (_"mas no barco"_):
no te regaña, pero tampoco te deja pasar todo. Mide tu **constancia** (rachas y
% de cumplimiento), no la perfección.

Sigue estos hábitos, y puedes cambiarlos en `config.py`:

- ⏰ Levantarte a tu hora
- 🥗 Alimentación
- 🏃 Ejercicio
- 🤝 Buscar clientes propios
- 💰 Finanzas
- 📚 Crecimiento personal y profesional

Lo bonito: le escribes en lenguaje normal (_"me levanté 7:10, desayuné avena,
20 min de caminata, contacté 2 clientes"_) y él lo interpreta, lo guarda y te
responde.

---

## 🧩 Cómo funciona (las 3 piezas)

1. **Telegram** — donde hablas con él desde tu celular.
2. **Notion** — donde se guarda tu tracking y se ven tus rachas.
3. **Claude (Anthropic)** — el "cerebro" que interpreta tus mensajes y hace de coach.

```
Tú (Telegram)  →  Claude interpreta  →  Notion guarda  →  Claude te responde como coach
```

---

## 🚀 Instalación paso a paso

No necesitas ser programadora. Sigue esto con calma; es de una sola vez.

### 0) Instala Python y las librerías

Necesitas [Python 3.10+](https://www.python.org/downloads/). Luego, en la
terminal, dentro de esta carpeta:

```bash
pip install -r requirements.txt
```

### 1) Crea tu bot de Telegram

1. En Telegram, busca a **@BotFather**.
2. Envía `/newbot` y sigue las instrucciones (nombre y usuario del bot).
3. Te dará un **token** como `123456:ABC-DEF...`. Guárdalo.

### 2) Crea tu clave de Claude

1. Entra a <https://console.anthropic.com/> y crea una cuenta.
2. En **API Keys**, crea una clave nueva y cópiala.

### 3) Conecta Notion

1. Ve a <https://www.notion.so/my-integrations> → **New integration**.
2. Ponle nombre (ej. "Hábitos"), créala y copia el **Internal Integration Secret**.
3. Abre (o crea) una página en Notion donde vivirá tu tabla. En esa página, haz
   clic en **···** (arriba a la derecha) → **Conexiones** → agrega tu integración.
4. Copia el **ID de esa página**: es la parte final de su URL (32 caracteres).

### 4) Rellena tus claves

Copia el archivo de ejemplo y edítalo con tus datos:

```bash
cp .env.example .env
```

Abre `.env` y pega tu `TELEGRAM_TOKEN`, `NOTION_TOKEN` y `ANTHROPIC_API_KEY`.
(El `NOTION_DATABASE_ID` lo obtienes en el siguiente paso.)

### 5) Crea la tabla en Notion automáticamente

```bash
python setup_notion.py <ID_de_tu_pagina>
```

Te imprimirá una línea `NOTION_DATABASE_ID=...`. **Cópiala y pégala en tu `.env`.**

### 6) ¡Enciende el bot!

```bash
python bot.py
```

Abre Telegram, busca tu bot y envíale **/start**. Listo 🎉

---

## 💬 Cómo se usa el día a día

- **Registrar:** escríbele normal lo que hiciste. Puedes hacerlo por partes
  (algo en la mañana, completar en la noche): junta todo en el mismo día.
- **/resumen:** te muestra tus rachas y % de constancia de la semana.
- **/ayuda:** recordatorio de qué puede hacer.
- Él te escribe solo en la **mañana** y en la **noche** (horas configurables).

---

## ⚙️ Personalización

Casi todo se ajusta sin tocar el código, en `.env` o en `config.py`:

| Qué | Dónde | Ejemplo |
|---|---|---|
| Horas de recordatorio | `.env` → `HORA_MANANA`, `HORA_NOCHE` | `06:30`, `22:00` |
| Tus metas | `.env` → `META_LEVANTARSE`, `META_EJERCICIO_MIN`, `META_CLIENTES` | `07:00`, `30`, `5` |
| Peso de cada hábito en el puntaje | `config.py` → `PESOS` | — |
| Personalidad del coach | `coach.py` → `PERSONALIDAD` | — |
| Modelo (costo) | `.env` → `COACH_MODEL` | `claude-haiku-4-5` (más barato) |

Empieza con pocos hábitos si quieres: no tienes que cumplir todo de golpe. El
agente mide **constancia**, no perfección.

---

## ⏰ Para que los recordatorios funcionen 24/7

Los recordatorios solo llegan mientras `python bot.py` esté **corriendo**. Opciones:

- **Fácil de probar:** déjalo corriendo en tu computadora (mientras esté encendida).
- **Siempre activo (recomendado):** súbelo a un hosting gratuito como
  [Railway](https://railway.app/), [Render](https://render.com/) o
  [PythonAnywhere](https://www.pythonanywhere.com/). Ahí configuras las mismas
  variables del `.env` y el bot vive en la nube.

---

## 🔒 Privacidad

Tus claves viven solo en tu archivo `.env` (que **no** se sube a internet gracias
al `.gitignore`). Tus registros viven en **tu** Notion. Los mensajes se procesan
con la API de Claude para interpretarlos y responderte.

---

## 🛠️ Estructura del proyecto

| Archivo | Qué hace |
|---|---|
| `bot.py` | El bot de Telegram y los recordatorios. **Este es el que ejecutas.** |
| `coach.py` | Interpreta tus mensajes y genera las respuestas del coach (Claude). |
| `notion_store.py` | Guarda en Notion y calcula tus rachas/constancia. |
| `config.py` | Tus hábitos, metas y ajustes. |
| `setup_notion.py` | Crea la tabla de Notion (se usa una sola vez). |
| `.env` | Tus claves secretas (lo creas tú, no se sube a internet). |
