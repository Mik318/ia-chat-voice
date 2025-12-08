# 🎛️ Guía de Control de ElevenLabs TTS

## ¿Cuándo desactivar ElevenLabs?

1. **Cuota excedida** - Cuando te quedas sin créditos
2. **Costo** - Para ahorrar dinero en desarrollo/pruebas
3. **Debugging** - Para simplificar el stack durante desarrollo
4. **Problemas de API** - Cuando ElevenLabs tiene downtime

## 🔧 Cómo desactivar ElevenLabs

### Opción 1: Variable de entorno en `.env`

Agrega o modifica en tu archivo `.env`:

```bash
ENABLE_ELEVENLABS=false
```

Luego reinicia tu servidor:

```bash
uvicorn main:app --reload
```

### Opción 2: Variable temporal (solo para la sesión actual)

En Linux/Mac:

```bash
export ENABLE_ELEVENLABS=false
uvicorn main:app --reload
```

En Windows (PowerShell):

```powershell
$env:ENABLE_ELEVENLABS="false"
uvicorn main:app --reload
```

## ✅ Cómo reactivar ElevenLabs

En tu archivo `.env`, cambia a:

```bash
ENABLE_ELEVENLABS=true
```

O simplemente comenta/elimina la línea (por defecto está activado).

## 🎯 Comportamiento esperado

### Con ElevenLabs **activado** (`ENABLE_ELEVENLABS=true`):

```
⚡ Pre-generando audios comunes en background...
✓ Audio generado: ¡Hola! Soy tu asistente...
✅ Pre-warming completado
```

### Con ElevenLabs **desactivado** (`ENABLE_ELEVENLABS=false`):

```
⚠️ ElevenLabs desactivado - Saltando pre-warming de audios

Durante llamadas:
⚠️ ElevenLabs desactivado, usando Twilio TTS fallback
```

## 📞 ¿Qué TTS se usa cuando está desactivado?

Cuando ElevenLabs está desactivado, todas las llamadas usan **Polly.Mia** de Amazon Polly (integrado en Twilio), que:

- ✅ Es gratis (incluido con Twilio)
- ✅ Tiene buena calidad en español
- ⚠️ Es menos natural que ElevenLabs
- ⚠️ Puede tener latencia mayor en la primera respuesta

## 🚀 Para Producción (Dokploy)

En Dokploy, configura las variables de entorno en:

1. Ve a tu aplicación
2. Settings → Environment Variables
3. Agrega: `ENABLE_ELEVENLABS=false` (o `true`)
4. Redeploy

## 📊 Monitoreo

Puedes ver en los logs qué TTS se está usando:

```bash
# ElevenLabs activo
✓ Audio generado: texto...

# ElevenLabs desactivado
⚠️ ElevenLabs desactivado, usando Twilio TTS fallback
```

## 💡 Recomendaciones

- **Desarrollo local**: Usa `ENABLE_ELEVENLABS=false` para ahorrar créditos
- **Testing**: Usa `ENABLE_ELEVENLABS=true` y límites bajos de créditos
- **Producción**: Usa `ENABLE_ELEVENLABS=true` con plan adecuado
- **Emergencia**: Si se excede cuota en producción, cambia a `false` temporalmente

## 🔄 Fallback automático

Incluso con `ENABLE_ELEVENLABS=true`, si ocurre un error (como quota excedida), el sistema automáticamente usará Twilio TTS como respaldo. No se caerán las llamadas.
