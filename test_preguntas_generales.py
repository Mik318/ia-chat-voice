"""
Script de prueba para verificar que las preguntas generales funcionan correctamente
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

def buscar_contexto_relevante(pregunta: str, top_k: int = 3) -> str:
    """Busca los chunks más relevantes del contexto usando RAG"""
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
        return contexto_relevante
        
    except Exception as e:
        print(f"⚠️ Error en RAG: {e}")
        return ""

# Probar preguntas generales
print("🧪 Probando preguntas generales:\n")

preguntas_generales = [
    "¿Qué ofreces?",
    "¿Qué productos tienes?",
    "¿Cuál es tu producto?",
    "¿De qué trata esto?"
]

for pregunta in preguntas_generales:
    print(f"❓ {pregunta}")
    
    # Simular la lógica del main.py
    preguntas_generales_check = ["qué ofreces", "que ofreces", "qué productos", "que productos", 
                                   "qué vendes", "que vendes", "cuál es tu producto", "cual es tu producto",
                                   "de qué trata", "de que trata", "qué es esto", "que es esto"]
    
    es_pregunta_general = any(pg in pregunta.lower() for pg in preguntas_generales_check)
    
    if es_pregunta_general:
        print("  ✅ Detectada como pregunta general")
        contexto = buscar_contexto_relevante("descripción general ORISOD Enzyme producto", top_k=2)
    else:
        print("  ❌ NO detectada como pregunta general")
        contexto = buscar_contexto_relevante(pregunta, top_k=3)
    
    print(f"  📄 Contexto recuperado: {contexto[:150]}...\n")
