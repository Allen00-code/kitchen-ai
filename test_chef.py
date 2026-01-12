import os
import time
from dotenv import load_dotenv
from google import genai

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

print("--- DIAGNÓSTICO DE CHEF ---")
print(f"1. API Key: {api_key[:5]}..." if api_key else "❌ FALTA KEY")

try:
    client = genai.Client(api_key=api_key)
    print("2. Cliente creado.")
    
    prompt = "Dame una receta rápida de huevos revueltos. Solo 2 lineas."
    print(f"3. Enviando prompt a 'gemini-2.5-flash'...")
    
    start = time.time()
    # Forzamos una llamada simple sin Flet de por medio
    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=prompt
    )
    end = time.time()
    
    print(f"4. ¡RESPUESTA RECIBIDA! ({end - start:.2f} segundos)")
    print("-" * 20)
    print(response.text)
    print("-" * 20)

except Exception as e:
    print(f"\n❌ ERROR FATAL: {e}")