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

    def generate_recipe(
        self,
        inventory_items: list,
        is_weekly_plan: bool = False,
        suggest_missing: bool = False,
    ):
        """Genera una receta (o plan semanal de batch cooking) a partir del inventario."""
        if not self.client:
            return {"error": "Falta API Key"}

        try:
            # ── System instruction dinámica ──────────────────────────────────────
            if is_weekly_plan:
                system_instruction = (
                    "Eres un Chef de Alto Rendimiento y Nutriólogo Deportivo de élite "
                    "trabajando para un boxeador en entrenamiento intensivo. Tu misión es diseñar "
                    "un plan de 'Batch Cooking' (5 tuppers) que sea una obra maestra culinaria: "
                    "absolutamente delicioso, con perfiles de sabor complejos, pero ESTRICTAMENTE limpio. "
                    "REGLAS CULINARIAS: PROHIBIDO lo grasoso, frito o aburrido. Evita el clásico e "
                    "insípido pollo hervido. Utiliza técnicas de cocción inteligentes, especias, "
                    "hierbas aromáticas y cítricos para lograr un sabor espectacular tipo restaurante "
                    "sin añadir grasas saturadas. "
                    "ENFOQUE NUTRICIONAL: El plato DEBE ser regenerador. Altísimo en proteína magra "
                    "para reparar fibras musculares, carbohidratos complejos de absorción lenta para "
                    "energía explosiva en el ring, y vegetales ricos en antioxidantes para reducir "
                    "la inflamación post-entrenamiento."
                )
            else:
                system_instruction = (
                    "Eres un chef profesional y nutricionista. Genera recetas prácticas, "
                    "saludables y deliciosas utilizando únicamente (o principalmente) "
                    "los ingredientes disponibles en el inventario del usuario."
                )

            if suggest_missing:
                system_instruction += (
                    " Si el inventario es insuficiente para lograr una comida espectacular, "
                    "sugiere ingredientes adicionales que potencien el sabor y la nutrición, "
                    "manteniéndose económicos y fáciles de conseguir. Ponlos en 'missing_ingredients'."
                )
            else:
                system_instruction += (
                    " Utiliza ÚNICAMENTE los ingredientes del inventario. "
                    "Usa tu creatividad para sacar el máximo sabor. "
                    "Devuelve 'missing_ingredients' como lista vacía."
                )

            # ── Prompt del usuario ───────────────────────────────────────────────
            inventory_text = "\n".join(
                f"- {item.get('name', '?')} | cantidad: {item.get('quantity', '?')} "
                f"{item.get('unit', '')} | categoría: {item.get('categories', {}).get('name', '?')}"
                for item in inventory_items
            )

            if is_weekly_plan:
                task_description = (
                    "Diseña un plan de batch cooking de 5 tuppers para la semana de entrenamiento. "
                    "Explica en los pasos cómo cocinar todo de manera eficiente en una sola sesión."
                )
            else:
                task_description = "Genera la mejor receta posible con estos ingredientes."

            prompt = f"""{task_description}

Ingredientes disponibles en el inventario:
{inventory_text}

Responde ÚNICAMENTE con un objeto JSON válido (sin markdown, sin bloques de código) con
exactamente esta estructura:
{{
  "name": "Nombre de la receta o plan",
  "ingredients": [
    {{"name": "...", "quantity": 1, "unit": "..."}}
  ],
  "steps": [
    "Paso 1...",
    "Paso 2..."
  ],
  "nutrition": {{
    "calories": 0,
    "protein": 0,
    "carbs": 0,
    "fat": 0
  }},
  "missing_ingredients": [
    {{"name": "...", "quantity": 1, "unit": "..."}}
  ]
}}
Si no faltan ingredientes, devuelve "missing_ingredients" como lista vacía [].
"""

            # ── Llamada a la API ─────────────────────────────────────────────────
            response = self.client.models.generate_content(
                model="gemini-2.5-flash",
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    temperature=0.7 # Añadimos un poco de creatividad para mejorar el sabor
                ),
                contents=prompt,
            )

            text = response.text.replace("```json", "").replace("```", "").strip()
            result = json.loads(text)

            if "missing_ingredients" not in result:
                result["missing_ingredients"] = []

            return result

        except Exception as e:
            print(f"❌ ERROR generate_recipe: {e}")
            return {"error": str(e)}

gemini_service = GeminiService()