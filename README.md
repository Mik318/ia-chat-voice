# Asistente de Voz con IA

Este proyecto es un asistente virtual de voz inteligente diseñado para responder preguntas sobre productos y servicios de manera automatizada. Utiliza tecnologías avanzadas de IA para ofrecer una experiencia de conversación natural y rápida.

## Tecnologías

- **FastAPI**: Framework web moderno y rápido.
- **Twilio**: Manejo de llamadas telefónicas y reconocimiento de voz.
- **Google Gemini 2.0 Flash**: Modelo de IA para generación de respuestas y embeddings.
- **ElevenLabs**: Síntesis de voz ultra-realista y rápida (Modelo Turbo).
- **ChromaDB**: Base de datos vectorial para RAG (Retrieval-Augmented Generation).
- **PostgreSQL**: Base de datos relacional para el registro de llamadas.
- **SQLAlchemy**: ORM para interactuar con la base de datos.

## Características

- **Interacción por Voz**: Conversación fluida y natural en español.
- **Contexto Inteligente (RAG)**: Responde basándose exclusivamente en la documentación proporcionada.
- **Baja Latencia**: Optimizado para respuestas rápidas (<2s) con streaming y prompts concisos.
- **Registro de Llamadas**: Almacenamiento detallado de interacciones en PostgreSQL.
- **Seguridad**: Manejo de variables de entorno para claves API.
- **Cache Inteligente**: Sistema de cache para audios frecuentes.

## Instalación

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

4. **Configurar Base de Datos (PostgreSQL):**
   Puedes usar Docker para levantar una instancia rápidamente:

   ```bash
   docker-compose up -d
   ```

   O instalar PostgreSQL localmente y crear una base de datos.

5. **Configurar variables de entorno:**
   Crea un archivo `.env` basado en el ejemplo y agrega tus claves:

   ```env
   TWILIO_ACCOUNT_SID=tu_sid
   TWILIO_AUTH_TOKEN=tu_token
   GEMINI_API_KEY=tu_api_key
   ELEVENLABS_API_KEY=tu_api_key
   BASE_URL=tu_url_ngrok
   DATABASE_URL=postgresql://usuario:password@localhost:5432/nombre_db
   ```

6. **Vectorizar el contexto:**
   Asegúrate de tener tu archivo de contexto (`contexto.txt`) listo y ejecuta:
   ```bash
   python vectorize_context.py
   ```

## Ejecución

1. **Iniciar el servidor:**

   ```bash
   uvicorn main:app --reload
   ```

2. **Exponer puerto (si usas Twilio):**

   ```bash
   ngrok http 8000
   ```

3. **Inspeccionar registros de llamadas:**
   Puedes ver el historial de conversaciones ejecutando:
   ```bash
   python inspect_db.py
   ```

## Estructura del Proyecto

- `main.py`: Lógica principal de la aplicación y endpoints.
- `database.py`: Configuración de conexión a PostgreSQL.
- `models.py`: Modelos de datos (SQLAlchemy).
- `inspect_db.py`: Script para visualizar el historial de llamadas.
- `contexto_orisod.txt`: Base de conocimiento (puedes renombrarlo).
- `vectorize_context.py`: Script para generar la base de datos vectorial.
- `requirements.txt`: Dependencias del proyecto.
