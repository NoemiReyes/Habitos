# 🚀 Subir tu bot a la nube (Railway)

Para que tu coach te escriba **solo cada día** y reciba los datos de tu **Apple
Watch**, tiene que vivir en un servidor encendido 24/7, no en tu computadora.
Esta guía usa **Railway**, que es de lo más sencillo.

> 💡 **Sobre el costo:** un bot que está siempre despierto no cabe en los planes
> gratis que "se duermen" (ahí no te llegarían los recordatorios). Railway tiene
> un plan **Hobby (~5 USD/mes)** que lo mantiene vivo. Es el precio de tenerlo
> siempre disponible.

---

## Paso 1 — Ten tu código en GitHub

Ya está: tu proyecto vive en tu repositorio de GitHub. Solo asegúrate de que tus
últimos cambios estén subidos.

> Tu archivo `.env` **no** se sube (así debe ser: contiene tus claves). En
> Railway las volverás a escribir como "Variables".

## Paso 2 — Crea el proyecto en Railway

1. Entra a <https://railway.app/> y crea una cuenta (puedes usar tu GitHub).
2. **New Project** → **Deploy from GitHub repo**.
3. Autoriza a Railway y elige tu repositorio **Habitos**.
4. En la rama, elige `claude/habits-tracking-agent-hoqv4s` (o `main` si ya lo
   fusionaste).

Railway detecta que es Python y empieza a construirlo solo.

## Paso 3 — Escribe tus claves (Variables)

En tu servicio, entra a la pestaña **Variables** y agrega una por una
(los mismos valores de tu `.env`):

| Variable | Qué es |
|---|---|
| `TELEGRAM_TOKEN` | El token de tu bot (de @BotFather) |
| `NOTION_TOKEN` | El secreto de tu integración de Notion |
| `NOTION_DATABASE_ID` | El ID de tu base de datos |
| `ANTHROPIC_API_KEY` | Tu clave de Claude |
| `WEBHOOK_TOKEN` | Tu palabra secreta para el Apple Watch |
| `COACH_MODEL` | *(opcional)* `claude-opus-5`, `claude-sonnet-5` o `claude-haiku-4-5` |
| `HORA_MANANA` / `HORA_NOCHE` | *(opcional)* horas de recordatorio |
| `META_LEVANTARSE` / `META_EJERCICIO_MIN` / `META_CLIENTES` | *(opcional)* tus metas |

> ⏰ **Importante con las horas:** el servidor de Railway usa hora **UTC**. Si
> quieres el recordatorio a las 7:00 de tu zona, ajusta el número. Ejemplo: en
> México central (UTC−6) las 7:00 locales son las `13:00` UTC → pon `HORA_MANANA=13:00`.
> O agrega la variable `TZ` con tu zona (ej. `TZ=America/Mexico_City`) y usa tu
> hora local directamente.

## Paso 4 — Dale una dirección pública

1. En el servicio, ve a **Settings** → **Networking**.
2. Toca **Generate Domain**.
3. Railway te da una URL como `https://habitos-production.up.railway.app`.

Esa dirección **+ `/apple`** es la que va en tu Atajo del iPhone:
```
https://habitos-production.up.railway.app/apple
```

## Paso 5 — Revisa que arrancó

En la pestaña **Deployments** → **Logs**, deberías ver:
```
Buzón activo en el puerto ...
Bot en marcha. Abre Telegram y escribe /start a tu bot.
```
Abre Telegram, mándale **/start** a tu bot y ¡listo! 🎉

Cada vez que subas cambios a GitHub, Railway vuelve a desplegar solo.

---

## ¿Y la base de datos de Notion?

El script `setup_notion.py` (que crea la tabla) solo se corre **una vez** y puedes
hacerlo desde tu computadora antes de desplegar. No es parte del servidor.

## Alternativa: Render

[Render](https://render.com/) también funciona (lee el `Procfile` igual). Ojo:
su plan gratis **se duerme** tras un rato de inactividad, y entonces los
recordatorios no se disparan. Para un bot siempre activo, elige un plan de pago
(igual que en Railway).
