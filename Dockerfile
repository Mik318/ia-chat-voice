# Usa una imagen ligera de Python
FROM python:3.11-slim

# Instala dependencias del sistema (útil para audio/voz si usas ffmpeg, etc.)
RUN apt-get update && apt-get install -y \
    gcc \
    libffi-dev \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Directorio de trabajo
WORKDIR /app

# Copia los requerimientos e instala
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia el código
COPY . .

# Expone el puerto (FastAPI usa 8000 por defecto)
EXPOSE 8000

# Comando para arrancar (ajusta 'main:app' al nombre de tu archivo principal)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
