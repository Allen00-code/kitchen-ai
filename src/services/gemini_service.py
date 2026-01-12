import os
import json
import mimetypes
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

class GeminiService:
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        self.client = None
        if not self.api_key:
            print("❌ ERROR: No hay API Key en .env")
        else:
            try:
                self.client = genai.Client(api_key=self.api_key)
                print("✅ Cliente Gemini inicializado")
            except Exception as e:
                print(f"❌ Error al crear cliente Gemini: {e}")

    def analyze_image(self, image_path: str):
        if not self.client: return {"error": "Falta API Key"}
        try:
            mime_type, _ = mimetypes.guess_type(image_path)
            if image_path.lower().endswith('.heic'): mime_type = 'image/heic'
            if not mime_type: mime_type = 'image/jpeg'

            with open(image_path, "rb") as f:
                image_bytes = f.read()

            prompt = """
            Analiza esta imagen. Responde SOLO JSON:
            {"name": "...", "category": "...", "packaging": "...", "quantity": 1, "unit": "pz"}
            Categorías: [Lácteos, Carnes, Vegetales, Frutas, Granos, Snacks, Bebidas, Limpieza, Aceites y Grasas, Otros]
            """
            
            # CAMBIO: Usamos 'gemini-2.5-flash' que apareció disponible en tu lista
            response = self.client.models.generate_content(
                model='gemini-2.5-flash',
                contents=[
                    types.Content(
                        parts=[
                            types.Part.from_bytes(data=image_bytes, mime_type=mime_type),
                            types.Part.from_text(text=prompt)
                        ]
                    )
                ]
            )
            text = response.text.replace("```json", "").replace("```", "").strip()
            return json.loads(text)
        except Exception as e:
            print(f"❌ ERROR IA: {e}")
            return {"error": str(e)}

gemini_service = GeminiService()