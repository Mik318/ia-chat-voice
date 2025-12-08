from typing import Optional

import os
from fastapi import FastAPI, Request
from fastapi.responses import Response, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from twilio.twiml.voice_response import VoiceResponse
import google.generativeai as genai
from elevenlabs import ElevenLabs, VoiceSettings
from dotenv import load_dotenv
import hashlib
import time
import asyncio
from contextlib import asynccontextmanager
import chromadb
from sqlalchemy.orm import Session
from database import SessionLocal, engine, get_db
import models
from fastapi import Depends
from routers import api

# Crear tablas
models.Base.metadata.create_all(bind=engine)

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

# Crear carpeta para archivos de audio
AUDIO_DIR = "audio_files"
os.makedirs(AUDIO_DIR, exist_ok=True)

# Cache de audios en memoria para respuesta instantánea
audio_cache: dict[str, str] = {}

# Mensajes comunes para pre-generar
COMMON_MESSAGES = [
    "¡Hola! Soy tu asistente de ORISOD Enzyme. ¿En qué puedo ayudarte hoy?",
    "No te escuché bien o no estoy seguro. Por favor, repite tu pregunta con calma.",
    "Siento las molestias. Puedes dejar un mensaje después del tono y te responderemos por correo o llamada.",
    "Lo siento, estoy teniendo un problema técnico. ¿Puedes repetir tu pregunta?",
    "¿Hay algo más en lo que pueda ayudarte?",
    "¡Que tengas un excelente día! Hasta pronto."
]

# Inicializar ChromaDB para RAG
try:
    chroma_client = chromadb.PersistentClient(path="./chroma_db")
    knowledge_collection = chroma_client.get_collection("orisod_knowledge")
    print("✅ ChromaDB cargado - RAG activado")
    RAG_ENABLED = True
except Exception as e:
    print(f"⚠️ ChromaDB no disponible, usando contexto completo: {e}")
    # Fallback: cargar contexto completo
    try:
        with open("contexto_orisod.txt", "r", encoding="utf-8") as f:
            CONTEXTO_ORISOD = f.read()
    except Exception as e2:
        print(f"⚠️ Error cargando contexto: {e2}")
        CONTEXTO_ORISOD = ""
    RAG_ENABLED = False


def buscar_contexto_relevante(pregunta: str, top_k: int = 3) -> str:
    """Busca los chunks más relevantes del contexto usando RAG"""
    if not RAG_ENABLED:
        return CONTEXTO_ORISOD
    
    try:
        # Generar embedding de la pregunta
        result = genai.embed_content(
            model="models/text-embedding-004",
            content=pregunta,
            task_type="retrieval_query"
        )
        query_embedding = result['embedding']
        
        # Buscar chunks más similares
        results = knowledge_collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k
        )
        
        # Combinar los chunks relevantes
        contexto_relevante = "\n\n".join(results['documents'][0])
        print(f"🔍 RAG: Recuperados {len(results['documents'][0])} chunks relevantes")
        return contexto_relevante
        
    except Exception as e:
        print(f"⚠️ Error en RAG, usando contexto completo: {e}")
        return CONTEXTO_ORISOD if 'CONTEXTO_ORISOD' in globals() else ""



async def generar_audio(texto: str, request: Request) -> Optional[str]:
    """Genera audio con ElevenLabs con cache y modelo turbo para máxima velocidad"""
    try:
        # Hash simple del texto para cache permanente
        texto_hash = hashlib.md5(texto.encode()).hexdigest()

        # Verificar cache en memoria primero (instantáneo)
        if texto_hash in audio_cache:
            print(f"✓ Audio desde cache (memoria): {texto[:30]}...")
            print(f"  URL: {audio_cache[texto_hash]}")
            return audio_cache[texto_hash]

        # Verificar si existe en disco
        filename = f"{texto_hash}.mp3"
        filepath = os.path.join(AUDIO_DIR, filename)

        if os.path.exists(filepath):
            # Usar BASE_URL del .env si está disponible (para ngrok)
            base_url = os.getenv("BASE_URL")
            if not base_url:
                base_url = str(request.base_url).rstrip('/')
            url = f"{base_url}/audio/{filename}"
            audio_cache[texto_hash] = url
            print(f"✓ Audio desde disco: {texto[:30]}...")
            print(f"  URL generada: {url}")
            return url

        # Generar nuevo audio con modelo TURBO
        print(f"⚡ Generando audio turbo: {texto[:30]}...")

        def _generate():
            audio_generator = elevenlabs_client.text_to_speech.convert(
                text=texto,
                voice_id=os.getenv("ELEVEN_VOICE_ID", "7QQzpAyzlKTVrRzQJmTE"),
                model_id="eleven_turbo_v2_5",  # TURBO para velocidad 2-3x
                voice_settings=VoiceSettings(
                    stability=0.3,  # Menor estabilidad = más rápido
                    similarity_boost=0.5,
                    style=0.0,
                    use_speaker_boost=False  # Desactivar para menor latencia
                )
            )

            # Escribir inmediatamente para minimizar latencia
            with open(filepath, "wb") as f:
                for chunk in audio_generator:
                    f.write(chunk)

        # Ejecutar en thread para no bloquear
        await asyncio.to_thread(_generate)

        # Guardar en cache y retornar
        # Usar BASE_URL del .env si está disponible (para ngrok)
        base_url = os.getenv("BASE_URL")
        if not base_url:
            base_url = str(request.base_url).rstrip('/')
        url = f"{base_url}/audio/{filename}"
        audio_cache[texto_hash] = url
        print(f"✓ Audio generado: {texto[:30]}...")
        print(f"  URL: {url}")
        return url

    except Exception as e:
        print(f"❌ Error generando audio: {e}")
        return None


def limpiar_archivos_antiguos():
    """Limpia archivos de audio antiguos (más de 24 horas)"""
    try:
        now = time.time()
        for filename in os.listdir(AUDIO_DIR):
            filepath = os.path.join(AUDIO_DIR, filename)
            if os.path.isfile(filepath) and now - os.path.getmtime(filepath) > 86400:
                os.unlink(filepath)
    except Exception as e:
        print(f"⚠️ Error limpiando archivos: {e}")


@asynccontextmanager
async def lifespan(app_instance: FastAPI):
    """Pre-generar audios comunes al iniciar para respuesta instantánea"""

    # Función de pre-warming que se ejecuta completamente en background
    async def prewarm():
        print("⚡ Pre-generando audios comunes en background...")
        class MockRequest:
            def __init__(self):
                self.base_url = type('obj', (object,), {
                    '__str__': lambda x: os.getenv("BASE_URL", "http://localhost:8000")
                })()

        mock_req = MockRequest()
        for msg in COMMON_MESSAGES:
            try:
                await generar_audio(msg, mock_req)
            except Exception as e:
                print(f"  ✗ Error: {msg[:30]}... - {e}")
        print("✅ Pre-warming completado")

    # Lanzar en background SIN esperar
    asyncio.create_task(prewarm())

    yield
    # No necesitamos cleanup porque la tarea se completa sola


app = FastAPI(lifespan=lifespan)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200", "https://mik318.github.io", "https://call-asist.sistems-mik3.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Montar carpeta estática
app.mount("/audio", StaticFiles(directory=AUDIO_DIR), name="audio")

# Incluir routers
app.include_router(api.router)

@app.post("/inicio")
async def inicio(request: Request, db: Session = Depends(get_db)):
    """Endpoint para cuando comienza la llamada"""
    limpiar_archivos_antiguos()
    
    # Obtener datos de la llamada
    form = await request.form()
    call_sid = form.get("CallSid")
    from_number = form.get("From")
    
    # Crear registro de llamada
    new_call = models.CallLog(
        call_sid=call_sid,
        user_phone=from_number,
        interaction_log=[]
    )
    db.add(new_call)
    db.commit()

    vr = VoiceResponse()
    texto = "¡Hola! Soy tu asistente de ORISOD Enzyme. ¿En qué puedo ayudarte hoy?"

    audio_url = await generar_audio(texto, request)

    # Gather con configuración mejorada para español
    gather = vr.gather(
        input="speech",
        action="/voice?attempt=1",
        method="POST",
        language="es-ES",  # Cambiado de es-MX a es-ES (mejor
        speechTimeout="1",  # Detecta MUY rápido (1 seg de silencio)
        timeout=25,
        profanityFilter=False,
        enhanced=True,
        speechModel="experimental_conversations",  # Modelo experimental más preciso
        hints="ORISOD Enzyme, qué ofreces, qué productos, beneficios, precio, ingredientes, cómo funciona, antioxidante, romero, olivo"
    )

    if audio_url:
        gather.play(audio_url)
    else:
        gather.say(texto, voice="Polly.Mia", language="es-MX")

    return Response(content=str(vr), media_type="application/xml")





@app.post("/voice")
async def voice(request: Request, db: Session = Depends(get_db)):
    form = await request.form()
    call_sid = form.get("CallSid")
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
    # IMPORTANTE: Si tiene texto, lo aceptamos incluso con confianza 0.0
    MIN_CONFIDENCE = float(os.getenv("MIN_ASR_CONFIDENCE", "0.50"))
    MAX_ATTEMPTS = int(os.getenv("MAX_ASR_ATTEMPTS", "3"))

    # Priorizar texto reconocido sobre confianza
    tiene_texto = user_input and user_input.strip() != ""
    confianza_baja = confidence < MIN_CONFIDENCE
    
    if not tiene_texto or (confianza_baja and not tiene_texto):
        if attempt < MAX_ATTEMPTS:
            vr = VoiceResponse()
            texto = "No te escuché bien o no estoy seguro. Por favor, repite tu pregunta con calma."
            audio_url = await generar_audio(texto, request)

            gather = vr.gather(
                input="speech",
                action=f"/voice?attempt={attempt+1}",
                method="POST",
                language="es-ES",
                speechTimeout="1",
                timeout=25,
                profanityFilter=False,
                enhanced=True,
                speechModel="experimental_conversations",
                hints="sí no ORISOD Enzyme, qué ofreces, qué productos, beneficios, precio, ingredientes, cómo funciona, antioxidante, romero, olivo, ayuda, información, pregunta, consulta, repetir, adiós, terminar, colgar"
            )

            if audio_url:
                gather.play(audio_url)
            else:
                gather.say(texto, voice="Polly.Mia", language="es-MX")

            return Response(content=str(vr), media_type="application/xml")
        else:
            # Después de MAX_ATTEMPTS ofrecemos dejar un mensaje grabado
            vr = VoiceResponse()
            texto = "Siento las molestias. Puedes dejar un mensaje después del tono y te responderemos por correo o llamada."
            audio_url = await generar_audio(texto, request)

            if audio_url:
                vr.play(audio_url)
            else:
                vr.say(texto, voice="Polly.Mia", language="es-MX")

            # Iniciar grabación y notificar a /recording cuando termine
            vr.record(action="/recording", method="POST", maxLength=120, playBeep=True, trim="trim-silence")
            vr.hangup()
        return Response(content=str(vr), media_type="application/xml")

    print(f"🎤 Usuario dijo: {user_input}")

    # Detectar preguntas generales sobre productos/ofertas
    preguntas_generales = ["qué ofreces", "que ofreces", "qué productos", "que productos", 
                           "qué vendes", "que vendes", "cuál es tu producto", "cual es tu producto",
                           "de qué trata", "de que trata", "qué es esto", "que es esto"]
    
    es_pregunta_general = any(pg in user_input.lower() for pg in preguntas_generales)
    
    if es_pregunta_general:
        # Para preguntas generales, usar la descripción general completa
        contexto_relevante = buscar_contexto_relevante("descripción general ORISOD Enzyme producto", top_k=2)
    else:
        # Para preguntas específicas, buscar contexto relevante
        contexto_relevante = buscar_contexto_relevante(user_input, top_k=3)

    # Prompt mejorado para conversación natural con contexto ORISOD
    prompt = f"""Eres un asistente virtual experto en ORISOD Enzyme®. Responde SOLO sobre este producto usando el contexto.
Sé breve y directo: máximo 2 oraciones. 
Si preguntan qué ofreces o cuál es tu producto, responde que ofreces ORISOD Enzyme® y explica brevemente qué es.
Si no está en el contexto, di que no tienes esa información.

Contexto:
{contexto_relevante}

Usuario: {user_input}
Asistente:"""

    try:
        model = genai.GenerativeModel("gemini-2.0-flash")
        result = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.7,
                max_output_tokens=100,  # Reducido de 150 a 100 para respuestas más rápidas y concisas
            )
        )
        respuesta = result.text.strip()
        print(f"🤖 IA responde: {respuesta}")
    except Exception as e:
        print(f"❌ Error al generar respuesta: {e}")
        respuesta = "Lo siento, estoy teniendo un problema técnico. ¿Puedes repetir tu pregunta?"

    # Guardar interacción en DB
    try:
        call_log = db.query(models.CallLog).filter(models.CallLog.call_sid == call_sid).first()
        if call_log:
            # Actualizar log
            current_log = list(call_log.interaction_log) if call_log.interaction_log else []
            current_log.append({
                "user": user_input,
                "ai": respuesta,
                "timestamp": time.time()
            })
            # Forzar actualización en SQLAlchemy (a veces no detecta cambios en JSON)
            call_log.interaction_log = current_log
            # flag_modified(call_log, "interaction_log") # Si fuera necesario
            db.commit()
    except Exception as e:
        print(f"⚠️ Error guardando en DB: {e}")

    vr = VoiceResponse()
    audio_url = await generar_audio(respuesta, request)

    if audio_url:
        vr.play(audio_url)
    else:
        vr.say(respuesta, voice="Polly.Mia", language="es-MX")

    # Verificar despedida (Lógica MUY estricta)
    # Solo aceptamos frases completas o palabras inequívocas de despedida
    frases_cierre_exactas = [
        "adiós", "adios", "bye", "chao", "bai", "nos vemos", "hasta luego", 
        "hasta pronto", "colgar", "terminar llamada", "eso es todo", "ya es todo",
        "muchas gracias adiós", "gracias adiós", "gracias bye", "a dios"
    ]
    
    input_lower = user_input.lower().strip().replace(".", "").replace(",", "").replace("!", "")
    
    es_despedida = False
    
    # 1. Coincidencia exacta o frase contenida (pero segura)
    if input_lower in frases_cierre_exactas:
        es_despedida = True
    
    # 2. Si la frase termina con "adiós" o "bye"
    elif input_lower.endswith("adiós") or input_lower.endswith("adios") or input_lower.endswith("bye"):
        es_despedida = True
        
    # 3. Si la frase es SOLO "gracias" (opcional, a veces la gente cuelga así)
    elif input_lower == "gracias" or input_lower == "muchas gracias":
        # Podríamos preguntar "¿Algo más?" en lugar de colgar, pero por ahora asumimos cierre si es seco
        pass 

    if es_despedida:
        texto_despedida = "¡Que tengas un excelente día! Hasta pronto."
        audio_url = await generar_audio(texto_despedida, request)

        if audio_url:
            vr.play(audio_url)
        else:
            vr.say(texto_despedida, voice="Polly.Mia", language="es-MX")

        vr.hangup()
    else:
        gather = vr.gather(
            input="speech",
            action="/voice?attempt=1",
            method="POST",
            language="es-ES",
            speechTimeout="1",
            timeout=25,
            profanityFilter=False,
            enhanced=True,
            speechModel="experimental_conversations",
            hints="sí no ORISOD Enzyme, qué ofreces, qué productos, beneficios, precio, ingredientes, cómo funciona, antioxidante, romero, olivo, ayuda, más, otra pregunta, información, adiós, terminar, colgar"
        )

        texto_continuar = "¿Hay algo más en lo que pueda ayudarte?"
        audio_url = await generar_audio(texto_continuar, request)

        if audio_url:
            gather.play(audio_url)
        else:
            gather.say(texto_continuar, voice="Polly.Mia", language="es-MX")

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