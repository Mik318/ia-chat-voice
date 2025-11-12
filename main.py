import os
from fastapi import FastAPI, Request
from fastapi.responses import Response
from twilio.twiml.voice_response import VoiceResponse
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

# Configurar Gemini (API de Google Generative AI)
genai.configure(
    api_key=os.getenv("GEMINI_API_KEY"),
    transport="rest"
)

app = FastAPI()

# Configuración de voz mejorada
# Voces de Amazon Polly disponibles en español:
# - Polly.Mia-Neural (mujer, español mexicano, muy natural)
# - Polly.Lupe-Neural (mujer, español mexicano)
# - Polly.Pedro-Neural (hombre, español mexicano)
# - Polly.Lucia-Neural (mujer, español español)
# - Polly.Sergio-Neural (hombre, español español)

VOICE_CONFIG = {
    "voice": "Polly.Mia-Neural",  # Voz neural más natural
    "language": "es-MX"
}


@app.post("/inicio")
async def inicio():
    """Endpoint para cuando comienza la llamada"""
    vr = VoiceResponse()
    vr.say(
        "¡Hola! Soy tu asistente virtual. ¿En qué puedo ayudarte hoy?",
        voice=VOICE_CONFIG["voice"],
        language=VOICE_CONFIG["language"]
    )

    # Comenzar a escuchar
    vr.gather(
        input="speech",
        action="/voice",
        method="POST",
        language=VOICE_CONFIG["language"],
        speechTimeout="auto",
        timeout=10,
        hints="ayuda, información, horario, precio, servicio"
    )

    return Response(content=str(vr), media_type="application/xml")


@app.post("/voice")
async def voice(request: Request):
    form = await request.form()
    user_input = form.get("SpeechResult", "")

    # Si no se detectó habla, pedir que repita
    if not user_input or user_input.strip() == "":
        vr = VoiceResponse()
        vr.say(
            "No te escuché bien. ¿Puedes repetir?",
            voice=VOICE_CONFIG["voice"],
            language=VOICE_CONFIG["language"]
        )
        vr.gather(
            input="speech",
            action="/voice",
            method="POST",
            language=VOICE_CONFIG["language"],
            speechTimeout="auto",
            timeout=5
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

    # Crear respuesta de voz para Twilio
    vr = VoiceResponse()
    vr.say(
        respuesta,
        voice=VOICE_CONFIG["voice"],
        language=VOICE_CONFIG["language"]
    )

    # Detectar si el usuario quiere terminar la llamada
    palabras_despedida = ["adiós", "adios", "chao", "hasta luego", "colgar", "terminar"]
    if any(palabra in user_input.lower() for palabra in palabras_despedida):
        vr.say(
            "¡Que tengas un excelente día! Hasta pronto.",
            voice=VOICE_CONFIG["voice"],
            language=VOICE_CONFIG["language"]
        )
        vr.hangup()
    else:
        # Continuar escuchando
        vr.gather(
            input="speech",
            action="/voice",
            method="POST",
            language=VOICE_CONFIG["language"],
            speechTimeout="auto",
            timeout=10,
            hints="sí, no, ayuda, información, horario, precio"
        )
        vr.say(
            "¿Hay algo más en lo que pueda ayudarte?",
            voice=VOICE_CONFIG["voice"],
            language=VOICE_CONFIG["language"]
        )

    return Response(content=str(vr), media_type="application/xml")


@app.get("/")
def root():
    return {"message": "Servidor IA Telefónica con Gemini activo 🚀"}