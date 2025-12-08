import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
model_name = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

print(f"🧪 Testing Gemini Model: {model_name}")

if not api_key:
    print("❌ No GEMINI_API_KEY found")
    exit(1)

genai.configure(api_key=api_key)

# Contexto simulado (vacío o corto como en el error)
contexto_relevante = "ORISOD Enzyme es un suplemento antioxidante derivado del romero y olivo."
user_input = "Hola, qué productos ofrece?"

prompt = f"""Eres un asistente virtual experto en ORISOD Enzyme®. Responde SOLO sobre este producto usando el contexto.
Sé breve y directo: máximo 2 oraciones. 
Si preguntan qué ofreces o cuál es tu producto, responde que ofreces ORISOD Enzyme® y explica brevemente qué es.
Si no está en el contexto, di que no tienes esa información.

Contexto:
{contexto_relevante}

Usuario: {user_input}
Asistente:"""

try:
    model = genai.GenerativeModel(model_name)
    print(f"Sending prompt length: {len(prompt)}")
    
    response = model.generate_content(
        prompt,
        generation_config=genai.types.GenerationConfig(
            temperature=0.7,
            max_output_tokens=300,
        )
    )
    
    print(f"Finish Reason: {response.candidates[0].finish_reason}")
    print(f"Parts: {response.parts}")
    
    if response.parts:
        print(f"✅ Response text: {response.text}")
    else:
        print("❌ No parts returned!")
        print(response)

except Exception as e:
    print(f"❌ Error: {e}")
