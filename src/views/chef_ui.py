import flet as ft
import json
import re
from src.services.supabase_service import supabase_client
from src.services.gemini_service import gemini_service

class ChefView(ft.Column):
    def __init__(self, page_nav_callback=None): 
        super().__init__()
        self.page_nav_callback = page_nav_callback
        self.expand = True
        self.scroll = ft.ScrollMode.AUTO
        self.manual_menu_visible = False

        # --- UI DE ESTADO ---
        self.loading_bar = ft.ProgressBar(width=400, color="orange", visible=False)
        self.status_text = ft.Text("", color="grey", italic=True)

        # --- CONTENEDOR DE TARJETAS ---
        self.recipes_column = ft.Column(spacing=20) 

        # --- INPUTS DE CONFIGURACIÓN ---
        self.meal_type_selector = ft.Dropdown(
            label="Tipo de Comida",
            options=[
                ft.dropdown.Option("Cualquiera"), ft.dropdown.Option("Desayuno"),
                ft.dropdown.Option("Almuerzo"), ft.dropdown.Option("Cena"), ft.dropdown.Option("Snack")
            ],
            value="Cualquiera", expand=True
        )

        self.caloric_goal_selector = ft.Dropdown(
            label="Objetivo Calórico",
            options=[
                ft.dropdown.Option("Ninguno"),
                ft.dropdown.Option("Déficit Calórico"),
                ft.dropdown.Option("Superávit Calórico")
            ],
            value="Ninguno", expand=True
        )

        self.vibe_selector = ft.Dropdown(
            label="¿Qué se te antoja?",
            options=[
                ft.dropdown.Option("Sin preferencia"),
                ft.dropdown.Option("Algo Salado 🥨"), ft.dropdown.Option("Algo Dulce 🍬"),
                ft.dropdown.Option("Algo Picoso 🌶️"), ft.dropdown.Option("Algo Fresco ❄️"),
                ft.dropdown.Option("Rápido y Fácil ⚡"), ft.dropdown.Option("Gourmet 🎩"),
                ft.dropdown.Option("Comfort Food 🍲")
            ],
            value="Sin preferencia", expand=True
        )
        
        self.additional_instructions = ft.TextField(
            label="Instrucciones Adicionales",
            hint_text="Ej: 'Muy detallado', 'Explicame como niño', 'Sin cebolla'...",
            text_size=13, multiline=False, expand=True
        )
        
        self.fit_mode_switch = ft.Switch(label="🥗 Modo Fit", value=False)
        self.exclusion_mode_switch = ft.Switch(label="🚫 Modo Exclusión", value=False, active_color="red")

        self.workspace = ft.Column()

        # Botones Principales
        self.btn_auto = ft.ElevatedButton("🎲 Sugerencia Auto", icon="auto_awesome", bgcolor="purple", color="white", height=45, expand=True, on_click=self.run_auto_mode)
        self.btn_manual = ft.ElevatedButton("🥕 Selección Manual", icon="restaurant_menu", bgcolor="orange", color="white", height=45, expand=True, on_click=self.setup_manual_mode)

        self.controls = [
            ft.Container(
                padding=15,
                content=ft.Column([
                    ft.Row([
                        ft.Text("Chef AI 👨‍🍳", size=24, weight="bold"),
                        ft.IconButton(icon="book", icon_color="brown", tooltip="Mis Recetas Guardadas", on_click=self.go_to_favorites)
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    
                    ft.Container(
                        padding=10, border=ft.border.all(1, "grey"), border_radius=10, 
                        content=ft.Column([
                            ft.Row([self.meal_type_selector, self.caloric_goal_selector]),
                            ft.Row([self.vibe_selector]), 
                            ft.Row([self.additional_instructions]),
                            ft.Row([self.fit_mode_switch])
                        ])
                    ),
                    ft.Container(height=10),
                    ft.Row([self.btn_auto, self.btn_manual]),
                    ft.Divider(),
                    self.workspace,
                    ft.Column([
                        ft.Row([self.loading_bar], alignment=ft.MainAxisAlignment.CENTER),
                        ft.Row([self.status_text], alignment=ft.MainAxisAlignment.CENTER),
                        ft.Container(height=10),
                        self.recipes_column
                    ])
                ])
            )
        ]
        
        self.selected_ingredients_names = set()
        self.cached_manual_items = [] 

    def go_to_favorites(self, e):
        if self.page_nav_callback:
            self.page_nav_callback("favorites")

    # --- UTILIDADES ---
    def set_loading(self, is_loading, message=""):
        self.loading_bar.visible = is_loading
        self.status_text.value = message
        self.update()

    def clean_json_text(self, text):
        # Limpia los bloques de código markdown si existen
        pattern = r"```json\s*(.*?)\s*```"
        match = re.search(pattern, text, re.DOTALL)
        if match: return match.group(1)
        return text

    # --- GUARDADO Y COPIADO ---
    def copy_recipe(self, recipe_data):
        text = f"🍳 {recipe_data['title']}\n\n📝 Ingredientes:\n" + "\n".join([f"- {i}" for i in recipe_data['ingredients']])
        text += "\n\n🔥 Instrucciones:\n" + "\n".join([f"{idx+1}. {step}" for idx, step in enumerate(recipe_data['instructions'])])
        self.page.set_clipboard(text)
        self.page.snack_bar = ft.SnackBar(ft.Text("✅ Copiado"))
        self.page.snack_bar.open = True
        self.page.update()

    def save_recipe_to_db(self, recipe_data):
        try:
            supabase_client.table("saved_recipes").insert({
                "title": recipe_data['title'],
                "ingredients": "\n".join(recipe_data['ingredients']),
                "instructions": "\n".join(recipe_data['instructions']),
                "nutritional_info": recipe_data.get('macros', ''),
                "tags": f"{self.meal_type_selector.value}, {self.vibe_selector.value}"
            }).execute()
            self.page.snack_bar = ft.SnackBar(ft.Text("❤️ Guardada en Recetario"))
            self.page.snack_bar.open = True
            self.page.update()
        except Exception as e:
            self.page.snack_bar = ft.SnackBar(ft.Text(f"❌ Error: {e}"))
            self.page.snack_bar.open = True
            self.page.update()

    # --- UI TARJETAS ---
    def render_recipe_cards(self, recipes_list):
        self.recipes_column.controls.clear()
        for i, recipe in enumerate(recipes_list):
            ing_controls = [ft.Text("🛒 Ingredientes:", weight="bold")]
            for ing in recipe.get('ingredients', []):
                ing_controls.append(ft.Text(f"• {ing}", size=13))
            
            step_controls = [ft.Text("🔥 Pasos Detallados:", weight="bold")]
            for idx, step in enumerate(recipe.get('instructions', [])):
                step_controls.append(ft.Container(
                    content=ft.Text(f"{idx+1}. {step}", size=13),
                    padding=ft.padding.only(bottom=5)
                ))

            card = ft.Container(
                bgcolor="white", padding=20, border_radius=15, border=ft.border.all(1, "#E0E0E0"),
                shadow=ft.BoxShadow(spread_radius=1, blur_radius=5, color="#DDDDDD"),
                content=ft.Column([
                    ft.Text(f"{recipe['title']}", size=20, weight="bold", color="black"),
                    ft.Divider(),
                    ft.Column(ing_controls, spacing=2),
                    ft.Container(height=10),
                    ft.Column(step_controls, spacing=2),
                    ft.Divider(),
                    ft.Text(f"📊 {recipe.get('macros', '')}", size=12, italic=True, color="grey"),
                    ft.Row([
                        ft.ElevatedButton("Copiar", icon="content_copy", color="blue", bgcolor="#E3F2FD", on_click=lambda _, r=recipe: self.copy_recipe(r), expand=True),
                        ft.ElevatedButton("Guardar", icon="favorite", color="white", bgcolor="pink", on_click=lambda _, r=recipe: self.save_recipe_to_db(r), expand=True)
                    ])
                ])
            )
            self.recipes_column.controls.append(card)
        self.update()

    # --- PROMPT REFORZADO ---
    def build_system_prompt(self):
        meal = self.meal_type_selector.value
        is_fit = self.fit_mode_switch.value
        caloric_goal = self.caloric_goal_selector.value
        vibe = self.vibe_selector.value
        notes = self.additional_instructions.value 
        
        base = "Eres un Chef Ejecutivo experto. TU MISION: Crear recetas EXTREMADAMENTE DETALLADAS."
        if meal != "Cualquiera": base += f" Tipo: {meal}."
        if vibe != "Sin preferencia": base += f" Estilo: {vibe}."
        if is_fit: base += " Modo FIT."
        if notes: base += f" Nota: {notes}."

        base += "\n\nREGLAS DE FORMATO (CRÍTICO):"
        base += "1. Responde SOLO con un JSON válido (Lista de objetos)."
        base += "2. En 'ingredients': Sé preciso con cantidades (ej: '200g de pollo', '1 pizca de sal')."
        base += "3. En 'instructions': NO seas breve. Explica la técnica, tiempos y señales visuales (ej: 'Cocinar hasta que los bordes estén dorados, aprox 4 min')."
        base += "\nEstructura JSON: "
        base += '[{"title": "Nombre Épico", "ingredients": ["100g X", "2 cdas Y"], "instructions": ["Paso 1 detallado...", "Paso 2 con tip..."], "macros": "Info nutricional"}]'
        
        return base

    # --- LOGICA DE DATOS ---
    def _format_ingredients_detailed(self, items_list):
        grouped = {}
        for item in items_list:
            cat = item.get('categories', {}).get('name', 'Otros') if item.get('categories') else 'Otros'
            if cat not in grouped: grouped[cat] = []
            detail = f"{item['name']} ({item['quantity']} {item['unit']})"
            grouped[cat].append(detail)
        return str(grouped)

    def run_auto_mode(self, e):
        self.set_loading(True, "🔍 Analizando y diseñando...")
        try:
            res = supabase_client.table("inventory").select("name, quantity, unit, categories(name)").eq("is_shopping_list", False).execute()
            inv_txt = self._format_ingredients_detailed(res.data)
            sys = self.build_system_prompt()
            self._call_gemini_safe(f"{sys} Inventario: {inv_txt}. Dame 3 opciones detalladas.")
        except Exception as ex: self.set_loading(False, f"Error: {ex}")

    def setup_manual_mode(self, e):
        if self.manual_menu_visible:
            self.workspace.controls.clear()
            self.workspace.update()
            self.manual_menu_visible = False
            return

        self.manual_menu_visible = True
        self.recipes_column.controls.clear()
        self.set_loading(True, "Cargando ingredientes...")
        self.workspace.controls.clear()
        self.selected_ingredients_names.clear()
        self.cached_manual_items = []
        
        try:
            res = supabase_client.table("inventory").select("name, quantity, unit, categories(name), locations(name)").eq("is_shopping_list", False).execute()
            self.set_loading(False, "")

            if not res.data:
                self.workspace.controls.append(ft.Text("Sin ingredientes en tu inventario."))
            else:
                self.cached_manual_items = res.data
                self.workspace.controls.append(ft.Container(bgcolor="#FFF3E0", padding=5, border_radius=5, content=self.exclusion_mode_switch))
                self.workspace.controls.append(ft.Text("Selecciona:", weight="bold"))
                
                for item in res.data:
                    txt = f"{item['name']} ({item['quantity']} {item['unit']})"
                    chk = ft.Checkbox(label=txt, value=False, on_change=lambda e, x=item['name']: self.toggle_selection(e, x))
                    self.workspace.controls.append(chk)
                
                self.workspace.controls.append(ft.ElevatedButton("🍳 Cocinar", bgcolor="green", color="white", on_click=self.run_manual_action))
            self.workspace.update()
            
        except Exception as ex: self.set_loading(False, f"❌ Error: {ex}")

    def toggle_selection(self, e, name):
        if e.control.value: self.selected_ingredients_names.add(name)
        else: self.selected_ingredients_names.discard(name)

    def run_manual_action(self, e):
        is_exclusion = self.exclusion_mode_switch.value
        final_items_data = []

        if is_exclusion:
            if not self.selected_ingredients_names:
                final_items_data = self.cached_manual_items
            else:
                final_items_data = [item for item in self.cached_manual_items if item['name'] not in self.selected_ingredients_names]
        else:
            if not self.selected_ingredients_names:
                self.set_loading(False, "⚠️ Selecciona al menos un ingrediente.")
                return
            final_items_data = [item for item in self.cached_manual_items if item['name'] in self.selected_ingredients_names]

        if not final_items_data:
            self.set_loading(False, "⚠️ No quedaron ingredientes disponibles.")
            return

        inv_txt = self._format_ingredients_detailed(final_items_data)
        sys = self.build_system_prompt()
        self._call_gemini_safe(f"{sys} Opciones (filtradas): {inv_txt}. Dame 3 opciones detalladas.")

    # --- MÉTODO CON DIAGNÓSTICO PARA VER EN TERMINAL ---
    def _call_gemini_safe(self, prompt):
        print("\n--- 🚀 INICIANDO PETICIÓN A GEMINI ---")
        print(f"📝 Prompt enviado (extracto): {prompt[:150]}...")
        
        try:
            if not gemini_service.client:
                print("❌ ERROR: No se encontró el cliente de Gemini (API Key faltante).")
                self.set_loading(False, "Falta API Key")
                return
            
            # Llamada a la API
            print("⏳ Esperando respuesta de Google...")
            response = gemini_service.client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt
            )
            
            print("--- 📥 RESPUESTA RECIBIDA DE GEMINI ---")
            print(f"Texto Crudo recibido:\n{response.text}") # ESTO VEREMOS EN TERMINAL
            print("---------------------------------------")

            # Intento de limpieza
            clean_text = self.clean_json_text(response.text)
            print(f"🧹 Texto limpio para JSON: {clean_text[:50]}...")

            # Intento de Parsing
            recipes_data = json.loads(clean_text)
            print("✅ JSON Parseado correctamente. Generando tarjetas...")
            
            self.set_loading(False, "✅ ¡Listo! Elige tu favorita:")
            self.render_recipe_cards(recipes_data)
            
        except json.JSONDecodeError as json_err:
            print(f"❌ ERROR JSON: No se pudo convertir el texto a JSON.\nDetalle: {json_err}")
            self.set_loading(False, "❌ Error: La IA no devolvió un formato válido.")
        except Exception as ex:
            print(f"❌ ERROR GENERAL: {ex}")
            self.set_loading(False, f"❌ Error del sistema: {ex}")