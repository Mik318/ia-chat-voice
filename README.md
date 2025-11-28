# Asistente de Voz ORISOD Enzyme® 🤖💊

Este proyecto es un asistente virtual de voz inteligente diseñado para responder preguntas sobre **ORISOD Enzyme®**. Utiliza tecnologías avanzadas de IA para ofrecer una experiencia de conversación natural y rápida.

## 🚀 Tecnologías

- **FastAPI**: Framework web moderno y rápido.
- **Twilio**: Manejo de llamadas telefónicas y reconocimiento de voz.
- **Google Gemini 2.0 Flash**: Modelo de IA para generación de respuestas y embeddings.
- **ElevenLabs**: Síntesis de voz ultra-realista y rápida (Modelo Turbo).
- **ChromaDB**: Base de datos vectorial para RAG (Retrieval-Augmented Generation).

## Características

- **Interacción por Voz**: Conversación fluida y natural en español.
- **Contexto Inteligente (RAG)**: Responde basándose exclusivamente en la documentación oficial del producto.
- **Baja Latencia**: Optimizado para respuestas rápidas (<2s).
- **Seguridad**: Manejo de variables de entorno para claves API.
- **Cache Inteligente**: Sistema de cache para audios frecuentes.

## 🛠️ Instalación

1. **Clonar el repositorio:**

   ```bash
   git clone <tu-repo-url>
   cd FastAPIProject
   ```

2. **Crear entorno virtual:**

   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Instalar dependencias:**

   ```bash
   pip install -r requirements.txt
   ```

4. **Configurar variables de entorno:**
   Crea un archivo `.env` basado en el ejemplo y agrega tus claves:

   ```env
   TWILIO_ACCOUNT_SID=tu_sid
   TWILIO_AUTH_TOKEN=tu_token
   GEMINI_API_KEY=tu_api_key
   ELEVENLABS_API_KEY=tu_api_key
   BASE_URL=tu_url_ngrok
   ```

5. **Vectorizar el contexto:**
   ```bash
   python vectorize_context.py
   ```

## ▶️ Ejecución

1. **Iniciar el servidor:**

   ```bash
   uvicorn main:app --reload
   ```

2. **Exponer puerto (si usas Twilio):**
   ```bash
   ngrok http 8000
   ```

## 📄 Estructura del Proyecto

- `main.py`: Lógica principal de la aplicación.
- `contexto_orisod.txt`: Base de conocimiento del producto.
- `vectorize_context.py`: Script para generar la base de datos vectorial.
- `requirements.txt`: Dependencias del proyecto.

---
