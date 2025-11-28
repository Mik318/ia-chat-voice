"""
Script de prueba para verificar que RAG funciona correctamente
"""
import os
import chromadb
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

# Configurar Gemini
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Cargar ChromaDB
chroma_client = chromadb.PersistentClient(path="./chroma_db")
knowledge_collection = chroma_client.get_collection("orisod_knowledge")

print("✅ ChromaDB cargado correctamente")
print(f"📊 Total de documentos: {knowledge_collection.count()}")

# Probar búsqueda
preguntas_prueba = [
    "¿Qué beneficios tiene para el corazón?",
    "¿Cuáles son los ingredientes?",
    "¿Cómo funciona la tecnología ADS?",
    "¿Qué precio tiene?"
]

for pregunta in preguntas_prueba:
    print(f"\n❓ Pregunta: {pregunta}")
    
    # Generar embedding
    result = genai.embed_content(
        model="models/text-embedding-004",
        content=pregunta,
        task_type="retrieval_query"
    )
    query_embedding = result['embedding']
    
    # Buscar
    results = knowledge_collection.query(
        query_embeddings=[query_embedding],
        n_results=2
    )
    
    print(f"🔍 Resultados encontrados: {len(results['documents'][0])}")
    for i, doc in enumerate(results['documents'][0]):
        print(f"  {i+1}. {doc[:100]}...")
