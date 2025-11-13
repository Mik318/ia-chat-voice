from typing import Optional

import os
from fastapi import FastAPI, Request
from fastapi.responses import Response, FileResponse
from fastapi.staticfiles import StaticFiles
from twilio.twiml.voice_response import VoiceResponse
import google.generativeai as genai
from elevenlabs import ElevenLabs, VoiceSettings
from dotenv import load_dotenv
import hashlib
import time

load_dotenv()

# Configurar Gemini
genai.configure(
    api_key=os.getenv("GEMINI_API_KEY"),
    transport="rest"
)

# Configurar ElevenLabs
elevenlabs_client = ElevenLabs(
    api_key=os.getenv("ELEVENLABS_API_KEY")
)

app = FastAPI()

# Crear carpeta para archivos de audio
AUDIO_DIR = "audio_files"
os.makedirs(AUDIO_DIR, exist_ok=True)

# Montar carpeta estática
app.mount("/audio", StaticFiles(directory=AUDIO_DIR), name="audio")


def generar_audio(texto: str, request: Request) -> Optional[str]:
    """Genera audio con ElevenLabs (voces de alta calidad)"""
    try:
        texto_hash = hashlib.md5(texto.encode()).hexdigest()
        filename = f"{texto_hash}_{int(time.time())}.mp3"
        filepath = os.path.join(AUDIO_DIR, filename)

        # Generar audio con ElevenLabs
        # Usando la voz por defecto (puedes cambiarla por otra vía env var)
        audio_generator = elevenlabs_client.text_to_speech.convert(
            text=texto,
            voice_id=os.getenv("ELEVEN_VOICE_ID", "7QQzpAyzlKTVrRzQJmTE"),
            model_id="eleven_multilingual_v2",
            voice_settings=VoiceSettings(
                stability=0.5,
                similarity_boost=0.75,
                style=0.0,
                use_speaker_boost=True
            )
        )

        # Guardar el audio
        with open(filepath, "wb") as f:
            for chunk in audio_generator:
                f.write(chunk)

        # Construir URL pública
        base_url = str(request.base_url).rstrip('/')
        return f"{base_url}/audio/{filename}"
    except Exception as e:
        print(f"❌ Error generando audio: {e}")
        return None


def limpiar_archivos_antiguos():
    """Limpia archivos de audio antiguos (más de 1 hora)"""
    try:
        now = time.time()
        for filename in os.listdir(AUDIO_DIR):
            filepath = os.path.join(AUDIO_DIR, filename)
            if os.path.isfile(filepath) and now - os.path.getmtime(filepath) > 3600:
                os.unlink(filepath)
    except Exception as e:
        print(f"⚠️ Error limpiando archivos: {e}")


@app.post("/inicio")
async def inicio(request: Request):
    """Endpoint para cuando comienza la llamada"""
    limpiar_archivos_antiguos()

    vr = VoiceResponse()
    texto = "¡Hola! Soy tu asistente virtual. ¿En qué puedo ayudarte hoy?"

    audio_url = generar_audio(texto, request)

    if audio_url:
        vr.play(audio_url)
    else:
        vr.say(texto, voice="Polly.Mia", language="es-MX")

    # Configuración MEJORADA para mejor reconocimiento
    # Usamos attempt=1 para controlar reintentos si la confianza es baja
    vr.gather(
        input="speech",
        action="/voice?attempt=1",
        method="POST",
        language="es-MX",
        speechTimeout="auto",  # Detección automática de pausas
        timeout=30,  # Más tiempo para hablar
        profanityFilter=False,  # No filtrar palabras
        enhanced=True,  # Modelo de reconocimiento mejorado
        speechModel="phone_call",  # Modelo optimizado para llamadas
        hints="ayuda información horario precio servicio consulta pregunta reserva cita atención cliente soporte venta inicio sesión contraseña"
    )

    return Response(content=str(vr), media_type="application/xml")


@app.post("/voice")
async def voice(request: Request):
    form = await request.form()
    user_input = form.get("SpeechResult", "")
    confidence_raw = form.get("Confidence", "0")

    # Obtener attempt desde query params (si viene de gather)
    attempt = 1
    try:
        attempt = int(request.query_params.get("attempt", "1"))
    except Exception:
        attempt = 1

    # Parseo seguro de la confianza
    try:
        confidence = float(confidence_raw)
    except Exception:
        confidence = 0.0

    # Log de confianza para debugging
    print(f"📊 Intento={attempt} - Confianza del reconocimiento: {confidence} - Texto reconocido: '{user_input}'")

    # Si no detectó voz o la confianza es baja, permitimos hasta 3 intentos
    MIN_CONFIDENCE = float(os.getenv("MIN_ASR_CONFIDENCE", "0.60"))
    MAX_ATTEMPTS = int(os.getenv("MAX_ASR_ATTEMPTS", "3"))

    if (not user_input or user_input.strip() == "") or confidence < MIN_CONFIDENCE:
        if attempt < MAX_ATTEMPTS:
            vr = VoiceResponse()
            texto = "No te escuché bien o no estoy seguro. Por favor, repite tu pregunta con calma."
            audio_url = generar_audio(texto, request)

            if audio_url:
                vr.play(audio_url)
            else:
                vr.say(texto, voice="Polly.Mia", language="es-MX")

            # Re-gather con attempt incrementado
            vr.gather(
                input="speech",
                action=f"/voice?attempt={attempt+1}",
                method="POST",
                language="es-MX",
                speechTimeout="auto",
                timeout=30,
                profanityFilter=False,
                enhanced=True,
                speechModel="phone_call",
                hints="sí no ayuda información pregunta consulta repetir"
            )
            return Response(content=str(vr), media_type="application/xml")
        else:
            # Después de MAX_ATTEMPTS ofrecemos dejar un mensaje grabado
            vr = VoiceResponse()
            texto = "Siento las molestias. Puedes dejar un mensaje después del tono y te responderemos por correo o llamada."
            audio_url = generar_audio(texto, request)

            if audio_url:
                vr.play(audio_url)
            else:
                vr.say(texto, voice="Polly.Mia", language="es-MX")

            # Iniciar grabación y notificar a /recording cuando termine
            vr.record(action="/recording", method="POST", maxLength=120, playBeep=True, trim="trim-silence")
            vr.hangup()

            return Response(content=str(vr), media_type="application/xml")

    print(f"🎤 Usuario dijo: {user_input}")

    # Prompt mejorado para conversación natural
    prompt = f"""Eres un asistente telefónico amable y profesional. 
Responde de forma breve (máximo 2-3 oraciones) y natural.
Si el usuario quiere terminar la llamada, despídete cordialmente.

Usuario: {user_input}
Asistente:"""

    try:
        model = genai.GenerativeModel("gemini-2.0-flash")
        result = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.7,
                max_output_tokens=150,
            )
        )
        respuesta = result.text.strip()
        print(f"🤖 IA responde: {respuesta}")
    except Exception as e:
        print(f"❌ Error al generar respuesta: {e}")
        respuesta = "Lo siento, estoy teniendo un problema técnico. ¿Puedes repetir tu pregunta?"

    vr = VoiceResponse()
    audio_url = generar_audio(respuesta, request)

    if audio_url:
        vr.play(audio_url)
    else:
        vr.say(respuesta, voice="Polly.Mia", language="es-MX")

    palabras_despedida = ["adiós", "adios", "chao", "hasta luego", "colgar", "terminar", "gracias adiós"]
    if any(palabra in user_input.lower() for palabra in palabras_despedida):
        texto_despedida = "¡Que tengas un excelente día! Hasta pronto."
        audio_url = generar_audio(texto_despedida, request)

        if audio_url:
            vr.play(audio_url)
        else:
            vr.say(texto_despedida, voice="Polly.Mia", language="es-MX")

        vr.hangup()
    else:
        # Continuar escuchando con configuración mejorada
        vr.gather(
            input="speech",
            action="/voice?attempt=1",
            method="POST",
            language="es-MX",
            speechTimeout="auto",
            timeout=30,
            profanityFilter=False,
            enhanced=True,
            speechModel="phone_call",
            hints="sí si no ayuda más otra pregunta información horario precio"
        )

        texto_continuar = "¿Hay algo más en lo que pueda ayudarte?"
        audio_url = generar_audio(texto_continuar, request)

        if audio_url:
            vr.play(audio_url)
        else:
            vr.say(texto_continuar, voice="Polly.Mia", language="es-MX")

    return Response(content=str(vr), media_type="application/xml")


@app.post("/recording")
async def recording(request: Request):
    """Endpoint que recibe el callback de la grabación de Twilio.
    Twilio enviará RecordingUrl y otros metadatos.
    Aquí simplemente confirmamos la recepción y agradecemos al usuario.
    En un siguiente paso podríamos descargar la grabación y transcribirla con un servicio ASR externo.
    """
    form = await request.form()
    recording_url = form.get("RecordingUrl") or form.get("RecordingUrl0")
    recording_sid = form.get("RecordingSid")
    print(f"📩 Grabación recibida: SID={recording_sid} URL={recording_url}")

    vr = VoiceResponse()
    texto = "Gracias. Hemos recibido tu mensaje y nos pondremos en contacto pronto."
    # Nota: Request base_url no está disponible en este callback de Twilio de forma confiable
    # así que usamos say como fallback
    vr.say(texto, language="es-MX")
    vr.hangup()

    return Response(content=str(vr), media_type="application/xml")


@app.get("/")
def root():
    return {"message": "Servidor IA Telefónica con reconocimiento mejorado 🚀"}


@app.get("/audio/{filename}")
async def serve_audio(filename: str):
    """Endpoint para servir archivos de audio"""
    filepath = os.path.join(AUDIO_DIR, filename)
    if os.path.exists(filepath):
        return FileResponse(filepath, media_type="audio/mpeg")
    return {"error": "Archivo no encontrado"}