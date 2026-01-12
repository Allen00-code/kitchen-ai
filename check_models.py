import os
from dotenv import load_dotenv
from google import genai

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    print("❌ Sin API Key")
    exit()

print("⏳ Conectando con Google...")

try:
    client = genai.Client(api_key=api_key)
    
    print("\n📋 LISTA DE MODELOS DISPONIBLES:")
    print("==================================")
    
    # Iteramos e imprimimos solo el nombre, que es lo que necesitamos
    for model in client.models.list():
        print(f"🔹 ID: {model.name}")
        
    print("\n==================================")
    print("✅ Fin del listado.")

except Exception as e:
    print(f"\n❌ Error: {e}")