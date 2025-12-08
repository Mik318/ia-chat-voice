import google.generativeai as genai
import os
from dotenv import load_dotenv
import time

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    print("❌ No GEMINI_API_KEY found")
    exit(1)

genai.configure(api_key=api_key)

models_to_test = [
    "gemini-2.5-flash",
    "gemini-2.0-flash-exp",
    "gemini-exp-1206",
    "gemini-2.0-flash-001"
]

print("🧪 Testing alternative models...")

for model_name in models_to_test:
    print(f"\n👉 Testing {model_name}...")
    try:
        model = genai.GenerativeModel(model_name)
        response = model.generate_content("Hi")
        print(f"✅ SUCCESS! {model_name} is working.")
        print(f"   Response: {response.text}")
        # If one works, suggest it and break? No, let's test all to find the best one.
    except Exception as e:
        if "429" in str(e):
            print(f"❌ {model_name}: Quota Exceeded (429)")
        elif "404" in str(e):
            print(f"❌ {model_name}: Not Found (404)")
        else:
            print(f"❌ {model_name}: Error {str(e)[:100]}...")
    time.sleep(1)
