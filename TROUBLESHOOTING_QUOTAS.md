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

### 2️⃣ Cambiar modelo de Gemini a 1.5 Flash

Agrega o modifica en tu `.env`:

```bash
GEMINI_MODEL=gemini-1.5-flash
```

**Efecto:** Cambia a Gemini 1.5 Flash que tiene mayor cuota gratuita.

**Cuotas comparadas:**

- `gemini-2.0-flash` (nuevo) - Límite bajo en free tier
- `gemini-1.5-flash` (estable) - Límite alto: **15 RPM, 1M TPM, 1500 RPD**

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
# Usar Gemini 1.5 Flash (mayor cuota)
GEMINI_MODEL=gemini-1.5-flash

# Desactivar ElevenLabs si no necesitas calidad premium
ENABLE_ELEVENLABS=false

# O mantener ElevenLabs si tienes plan pagado
ENABLE_ELEVENLABS=true
```

---

## 📊 Configuración recomendada para DESARROLLO

En tu `.env`:

```bash
# Gemini 1.5 Flash para desarrollo (más generoso)
GEMINI_MODEL=gemini-1.5-flash

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
🤖 Usando modelo: gemini-1.5-flash
⚠️ ElevenLabs desactivado - Saltando pre-warming de audios
```
