"""
Script para vectorizar el contexto de ORISOD Enzyme usando Gemini Embeddings y ChromaDB
"""
import os
import chromadb
from chromadb.config import Settings
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

# Configurar Gemini
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Leer el contexto
with open("contexto_orisod.txt", "r", encoding="utf-8") as f:
    contenido = f.read()

# Dividir en chunks por secciones
# Usamos los títulos numerados como separadores
chunks = []
current_chunk = ""
current_title = ""

for line in contenido.split('\n'):
    # Detectar títulos principales (números al inicio)
    if line.strip() and (line[0].isdigit() or line.startswith('##')):
        if current_chunk:
            chunks.append({
                "title": current_title,
                "content": current_chunk.strip()
            })
        current_title = line.strip()
        current_chunk = line + "\n"
    else:
        current_chunk += line + "\n"

# Agregar el último chunk
if current_chunk:
    chunks.append({
        "title": current_title,
        "content": current_chunk.strip()
    })

print(f"📚 Dividido en {len(chunks)} chunks")

# Crear cliente de ChromaDB
client = chromadb.PersistentClient(path="./chroma_db")

# Crear o resetear la colección
try:
    client.delete_collection("orisod_knowledge")
except:
    pass

collection = client.create_collection(
    name="orisod_knowledge",
    metadata={"description": "Conocimiento sobre ORISOD Enzyme"}
)

# Generar embeddings con Gemini y agregar a ChromaDB
print("⚡ Generando embeddings con Gemini...")
for i, chunk in enumerate(chunks):
    # Gemini genera embeddings automáticamente si usamos el modelo de embeddings
    result = genai.embed_content(
        model="models/text-embedding-004",
        content=chunk["content"],
        task_type="retrieval_document"
    )
    
    embedding = result['embedding']
    
    collection.add(
        ids=[f"chunk_{i}"],
        embeddings=[embedding],
        documents=[chunk["content"]],
        metadatas=[{"title": chunk["title"]}]
    )
    print(f"  ✓ Chunk {i+1}/{len(chunks)}: {chunk['title'][:50]}...")

print("✅ Vectorización completada!")
print(f"📊 Base de datos guardada en ./chroma_db")
print(f"📝 Total de chunks: {len(chunks)}")
