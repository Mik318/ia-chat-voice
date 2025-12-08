# 🔧 Solución de Problemas de Cuotas API

## 🚨 Problema: Error 429 - Quota Exceeded

Si ves estos errores en los logs:

### Error de ElevenLabs:

```
❌ Error generando audio: quota_exceeded
You have 9 credits remaining, while 34 credits are required
```

### Error de Gemini:

```
❌ Error al generar respuesta: 429 POST
You exceeded your current quota for gemini-2.0-flash
```

## ✅ Soluciones

### 1️⃣ Desactivar ElevenLabs (TTS de voz)

Agrega a tu `.env`:

```bash
ENABLE_ELEVENLABS=false
```

**Efecto:** Usará Twilio TTS (Amazon Polly) sin costo adicional.

---

### 2️⃣ Cambiar modelo de Gemini a uno estable

Agrega o modifica en tu `.env`:

```bash
GEMINI_MODEL=gemini-pro
```

**Efecto:** Cambia a Gemini Pro que es el modelo más estable y compatible.

**Errores comunes y soluciones:**

| Error                   | Causa                           | Solución                           |
| ----------------------- | ------------------------------- | ---------------------------------- |
| **429** Quota exceeded  | Límite de requests excedido     | Usar `gemini-pro` o esperar reset  |
| **404** Model not found | Nombre incorrecto o SDK antiguo | Usar `gemini-pro` (más compatible) |

**Cuotas comparadas (Free Tier):**

- `gemini-2.0-flash-lite` (recomendado) - **Eficiente y disponible**
- `gemini-2.0-flash` (potente) - Puede tener límites más estrictos
- `gemini-2.5-flash` (nuevo) - Experimental

**Nota:** Modelos antiguos como `gemini-pro` o `gemini-1.5-flash` NO están disponibles en tu cuenta actual.

---

### 3️⃣ Usar una API key diferente de Gemini

Si tienes múltiples cuentas de Google:

```bash
GEMINI_API_KEY=tu_otra_api_key_aqui
```

Obtén una nueva en: https://makersuite.google.com/app/apikey

---

### 4️⃣ Esperar a que se resetee la cuota

Las cuotas de Gemini se resetean:

- **Por minuto:** Cada 60 segundos
- **Por día:** A medianoche (hora del Pacífico)

Verás en el error:

```
Please retry in 35.678458329s
```

---

## 🎯 Configuración recomendada para PRODUCCIÓN

En tu `.env`:

```bash
# Usar Gemini 2.0 Flash Lite (disponible y eficiente)
GEMINI_MODEL=gemini-2.0-flash-lite

# Desactivar ElevenLabs si no necesitas calidad premium
ENABLE_ELEVENLABS=false

# O mantener ElevenLabs si tienes plan pagado
ENABLE_ELEVENLABS=true
```

---

## 📊 Configuración recomendada para DESARROLLO

En tu `.env`:

```bash
# Gemini 2.0 Flash Lite para desarrollo
GEMINI_MODEL=gemini-2.0-flash-lite

# ElevenLabs desactivado para ahorrar créditos
ENABLE_ELEVENLABS=false
```

---

## 🔄 Aplicar cambios

Después de modificar el `.env`:

```bash
# Reinicia el servidor
# Ctrl+C para detener
source .venv/bin/activate
uvicorn main:app --reload
```

---

## 💡 Comportamiento de Fallback Automático

Incluso sin configurar nada, el sistema tiene fallbacks:

1. **Si ElevenLabs falla** → Usa Twilio TTS
2. **Si Gemini falla por 429** → Muestra mensaje amigable pidiendo contacto
3. **Si Gemini falla por otro error** → Pide repetir la pregunta

---

## 🆘 Última opción: Upgrade a planes pagados

### Gemini Paid Tier

- 🔗 https://ai.google.dev/pricing
- 1000 requests/minute
- $0.075 / 1M tokens (input)

### ElevenLabs Paid Plan

- 🔗 https://elevenlabs.io/pricing
- Desde $5/mes
- 30,000 caracteres/mes

---

## ✅ Verificar estado actual

Ejecuta:

```bash
./check_elevenlabs.sh
```

Y revisa los logs al iniciar el servidor para ver qué modelo se está usando:

```
🤖 Gemini configurado - Modelo: gemini-2.0-flash-lite
⚠️ ElevenLabs desactivado - Saltando pre-warming de audios
```
