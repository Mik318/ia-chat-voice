import os
from fastapi import FastAPI, Request
from fastapi.responses import Response, FileResponse
from fastapi.staticfiles import StaticFiles
from twilio.twiml.voice_response import VoiceResponse
import google.generativeai as genai
from gtts import gTTS
from dotenv import load_dotenv
import hashlib
import time

load_dotenv()

# Configurar Gemini
genai.configure(
    api_key=os.getenv("GEMINI_API_KEY"),
    transport="rest"
)

app = FastAPI()

# Crear carpeta para archivos de audio
AUDIO_DIR = "audio_files"
os.makedirs(AUDIO_DIR, exist_ok=True)

# Montar carpeta estática
app.mount("/audio", StaticFiles(directory=AUDIO_DIR), name="audio")


def generar_audio(texto: str, request: Request) -> str:
    """Genera audio con gTTS (Google Text-to-Speech gratis)"""
    try:
        texto_hash = hashlib.md5(texto.encode()).hexdigest()
        filename = f"{texto_hash}_{int(time.time())}.mp3"
        filepath = os.path.join(AUDIO_DIR, filename)

        # Generar audio con gTTS
        tts = gTTS(text=texto, lang="es", tld="com.mx", slow=False)
        tts.save(filepath)

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
    vr.gather(
        input="speech",
        action="/voice",
        method="POST",
        language="es-MX",
        speechTimeout="auto",  # Detección automática de pausas
        timeout=15,  # Más tiempo para hablar
        profanityFilter=False,  # No filtrar palabras
        enhanced=True,  # Modelo de reconocimiento mejorado
        speechModel="phone_call",  # Modelo optimizado para llamadas
        hints="ayuda información horario precio servicio consulta pregunta reserva cita atención cliente"
    )

    return Response(content=str(vr), media_type="application/xml")


@app.post("/voice")
async def voice(request: Request):
    form = await request.form()
    user_input = form.get("SpeechResult", "")
    confidence = form.get("Confidence", "0")

    # Log de confianza para debugging
    print(f"📊 Confianza del reconocimiento: {confidence}")

    if not user_input or user_input.strip() == "":
        vr = VoiceResponse()
        texto = "No te escuché bien. Por favor, habla claro y di tu pregunta."
        audio_url = generar_audio(texto, request)

        if audio_url:
            vr.play(audio_url)
        else:
            vr.say(texto, voice="Polly.Mia", language="es-MX")

        vr.gather(
            input="speech",
            action="/voice",
            method="POST",
            language="es-MX",
            speechTimeout="auto",
            timeout=15,
            profanityFilter=False,
            enhanced=True,
            speechModel="phone_call",
            hints="sí no ayuda información pregunta consulta"
        )
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
            action="/voice",
            method="POST",
            language="es-MX",
            speechTimeout="auto",
            timeout=15,
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