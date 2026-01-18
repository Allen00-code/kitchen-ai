import flet as ft
from src.services.supabase_service import supabase_client
from src.services.gemini_service import gemini_service
import datetime

class ChefView(ft.Column):
    def __init__(self):
        super().__init__()
        self.expand = True
        self.scroll = ft.ScrollMode.AUTO
        self.is_dark_mode = True
        self.manual_menu_visible = False

        # --- UI DE ESTADO Y RESULTADOS ---
        
        # 1. Indicador de carga
        self.loading_bar = ft.ProgressBar(width=400, color="orange", visible=False)
        self.status_text = ft.Text("", color="grey", italic=True)

        # 2. Área de Receta (CORREGIDO: FONDO BLANCO)
        self.recipe_card = ft.Container(
            visible=False,
            padding=20,
            border_radius=15,
            bgcolor="white", # <--- CAMBIO CLAVE: Fondo blanco para leer bien
            border=ft.border.all(1, "#E0E0E0"), # Borde gris suave
            shadow=ft.BoxShadow(spread_radius=1, blur_radius=5, color="#DDDDDD"), # Sombra suave
            content=ft.Markdown(
                value="", 
                extension_set=ft.MarkdownExtensionSet.GITHUB_WEB,
                selectable=True,
                on_tap_link=lambda e: self.page.launch_url(e.data)
            )
        )

        self.copy_btn = ft.IconButton(
            icon="content_copy", 
            tooltip="Copiar Receta", 
            visible=False,
            on_click=self.copy_to_clipboard
        )

        # --- CONFIGURACIÓN (Inputs) ---
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
            label="¿Qué se te antoja? (Estilo)",
            options=[
                ft.dropdown.Option("Sin preferencia"),
                ft.dropdown.Option("Algo Salado 🥨"),
                ft.dropdown.Option("Algo Dulce 🍬"),
                ft.dropdown.Option("Algo Picoso 🌶️"),
                ft.dropdown.Option("Algo Fresco/Frío ❄️"),
                ft.dropdown.Option("Bebidas 🍹"),
                ft.dropdown.Option("Ensaladas 🥗"),
                ft.dropdown.Option("Postre 🍰"),
                ft.dropdown.Option("Panadería 🥖"),
                ft.dropdown.Option("Rápido y Fácil ⚡"),
                ft.dropdown.Option("Gourmet 🎩"),
                ft.dropdown.Option("Vegetariano 🥦"),
                ft.dropdown.Option("Vegano 🌱"),
                ft.dropdown.Option("Experimento Raro 🧪")
            ],
            value="Sin preferencia", expand=True
        )
        
        self.additional_instructions = ft.TextField(
            label="Instrucciones Adicionales (Opcional)",
            hint_text="Ej: 'Sin cebolla', 'Usa AirFryer', 'Para 3 personas'...",
            text_size=13, multiline=False, expand=True
        )
        
        self.fit_mode_switch = ft.Switch(label="🥗 Modo Fit (Ingredientes Saludables)", value=False)
        
        self.exclusion_mode_switch = ft.Switch(
            label="🚫 Modo Exclusión (Usar todo MENOS lo marcado)", 
            value=False, active_color="red"
        )

        self.workspace = ft.Column()

        # Botones
        self.btn_auto = ft.ElevatedButton("🎲 Sugerencia Rápida (Auto)", icon="auto_awesome", bgcolor="purple", color="white", height=45, expand=True, on_click=self.run_auto_mode)
        self.btn_manual = ft.ElevatedButton("🥕 Seleccionar Ingredientes", icon="restaurant_menu", bgcolor="orange", color="white", height=45, expand=True, on_click=self.setup_manual_mode)

        self.controls = [
            ft.Container(
                padding=15,
                content=ft.Column([
                    ft.Text("Chef AI 👨‍🍳", size=24, weight="bold"),
                    
                    # Panel de Configuración
                    ft.Container(
                        padding=10, border=ft.border.all(1, "grey"), border_radius=10, 
                        content=ft.Column([
                            ft.Text("Configuración:", weight="bold"), 
                            ft.Row([self.meal_type_selector, self.caloric_goal_selector]),
                            ft.Row([self.vibe_selector]), 
                            ft.Row([self.additional_instructions]),
                            ft.Row([self.fit_mode_switch])
                        ])
                    ),
                    ft.Container(height=10),
                    
                    # Botones de Acción
                    ft.Row([self.btn_auto, self.btn_manual]),
                    ft.Divider(),
                    
                    # Espacio para selectores manuales
                    self.workspace,
                    
                    # Área de Estado y Resultados
                    ft.Column([
                        ft.Row([self.loading_bar], alignment=ft.MainAxisAlignment.CENTER),
                        ft.Row([self.status_text], alignment=ft.MainAxisAlignment.CENTER),
                        ft.Container(height=10),
                        
                        ft.Row([ft.Text("Resultado:", weight="bold"), self.copy_btn], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                        self.recipe_card
                    ])
                ])
            )
        ]
        
        self.selected_ingredients_names = set()
        self.cached_manual_items = [] 
        self.last_response_text = "" 

    # --- UTILIDADES ---
    def set_loading(self, is_loading, message=""):
        self.loading_bar.visible = is_loading
        self.status_text.value = message
        self.update()

    def copy_to_clipboard(self, e):
        if self.last_response_text:
            self.page.set_clipboard(self.last_response_text)
            self.page.snack_bar = ft.SnackBar(ft.Text("✅ Receta copiada al portapapeles"))
            self.page.snack_bar.open = True
            self.page.update()

    # --- FORMATEADOR INTELIGENTE ---
    def _format_ingredients_detailed(self, items_list):
        grouped = {}
        for item in items_list:
            cat_name = "Otros"
            if item.get('categories') and item['categories'].get('name'):
                cat_name = item['categories']['name']
            
            if cat_name not in grouped: grouped[cat_name] = []
            
            loc_name = ""
            if item.get('locations') and item['locations'].get('name'):
                loc_name = item['locations']['name'].lower()
            
            detail = f"{item['name']}"
            if "congel" in loc_name or "freezer" in loc_name:
                detail += " (CONGELADO/Requiere Descongelar)"
                
            grouped[cat_name].append(detail)
        
        final_str = ""
        for category, ingredients in grouped.items():
            ing_list = ", ".join(ingredients)
            final_str += f"\n- {category}: {ing_list}."
        return final_str

    # --- PROMPT ---
    def build_system_prompt(self):
        meal = self.meal_type_selector.value
        is_fit = self.fit_mode_switch.value
        caloric_goal = self.caloric_goal_selector.value
        vibe = self.vibe_selector.value
        notes = self.additional_instructions.value 
        
        base = "Actúa como un Chef experto y Nutricionista."
        if meal != "Cualquiera": base += f" Cocina: {meal.upper()}."
        
        if vibe != "Sin preferencia":
            if "Experimento" in vibe: base += " MODALIDAD: EXPERIMENTAL/FUSIÓN."
            elif "Bebidas" in vibe: base += " MODALIDAD: BEBIDAS/JUGOS."
            elif "Vegano" in vibe: base += " RESTRICCIÓN: 100% VEGANO."
            elif "Vegetariano" in vibe: base += " RESTRICCIÓN: VEGETARIANO."
            elif "Picoso" in vibe: base += " PREFERENCIA: PICANTE."
            else: base += f" ESTILO: {vibe.upper()}."

        if is_fit: base += " MODALIDAD: FIT/SALUDABLE."
        
        if caloric_goal == "Déficit Calórico": base += " OBJETIVO: DÉFICIT (Bajo en cal, alto volumen)."
        elif caloric_goal == "Superávit Calórico": base += " OBJETIVO: SUPERÁVIT (Alta densidad energética)."
            
        if notes: base += f" PETICIÓN USUARIO: {notes}."
        
        base += " Dame una respuesta EXTENSA usando Markdown (Negritas, Listas, Títulos)."
        
        base += "\n\nINSTRUCCIONES DE INVENTARIO:"
        base += "\n1. OPCIONALIDAD: La lista que te doy son OPCIONES. Elige solo lo que combine."
        base += "\n2. CONGELADOS: Si un item es '(CONGELADO)', sugiere descongelado."
        base += "\n3. CANTIDADES: Te doy nombres. TÚ define las porciones exactas en la receta."

        base += "\n\nOBLIGATORIO: Al final, incluye 'INFORMACIÓN NUTRICIONAL APROXIMADA'."
        
        return base

    # --- MODO AUTO ---
    def run_auto_mode(self, e):
        self.workspace.controls.clear()
        self.manual_menu_visible = False 
        self.recipe_card.visible = False
        self.copy_btn.visible = False
        try: self.workspace.update()
        except: pass
        
        self.set_loading(True, "🔍 Analizando inventario...")
        
        try:
            res = supabase_client.table("inventory").select("name, quantity, unit, categories(name), locations(name)").eq("is_shopping_list", False).execute()
            
            if not res.data:
                self.set_loading(False, "⚠️ Tu inventario está vacío.")
                return

            inventory_text = self._format_ingredients_detailed(res.data)
            
            sys_prompt = self.build_system_prompt()
            prompt = f"{sys_prompt} Mis opciones son: {inventory_text}. Dame 3 opciones detalladas."
            self._call_gemini_safe(prompt)
            
        except Exception as ex:
            self.set_loading(False, f"❌ Error: {ex}")

    # --- MODO MANUAL ---
    def setup_manual_mode(self, e):
        if self.manual_menu_visible:
            self.workspace.controls.clear()
            self.workspace.update()
            self.manual_menu_visible = False
            return

        self.manual_menu_visible = True
        self.recipe_card.visible = False 
        self.set_loading(True, "Cargando ingredientes...")
        self.workspace.controls.clear()
        self.selected_ingredients_names.clear()
        self.cached_manual_items = []
        
        try:
            res = supabase_client.table("inventory").select("name, quantity, unit, categories(name), locations(name)").eq("is_shopping_list", False).execute()
            self.set_loading(False, "")

            if not res.data:
                self.workspace.controls.append(ft.Text("Sin ingredientes."))
            else:
                self.cached_manual_items = res.data
                self.workspace.controls.append(
                    ft.Container(bgcolor="#FFF3E0", padding=5, border_radius=5, content=self.exclusion_mode_switch)
                )
                self.workspace.controls.append(ft.Text("Selecciona:", weight="bold"))
                
                for item in res.data:
                    txt = f"{item['name']} ({item['quantity']} {item['unit']})"
                    chk = ft.Checkbox(label=txt, value=False, on_change=lambda e, x=item['name']: self.toggle_selection(e, x))
                    self.workspace.controls.append(chk)
                
                self.workspace.controls.append(ft.ElevatedButton("🍳 Cocinar", bgcolor="green", color="white", on_click=self.run_manual_action))
            self.workspace.update()
            
        except Exception as ex:
            self.set_loading(False, f"❌ Error: {ex}")

    def toggle_selection(self, e, name):
        if e.control.value: self.selected_ingredients_names.add(name)
        else: self.selected_ingredients_names.discard(name)

    def run_manual_action(self, e):
        is_exclusion = self.exclusion_mode_switch.value
        final_items_data = []

        if is_exclusion:
            if not self.selected_ingredients_names:
                final_items_data = self.cached_manual_items # Todo
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

        inventory_text = self._format_ingredients_detailed(final_items_data)
        
        sys_prompt = self.build_system_prompt()
        prompt = f"{sys_prompt} Opciones disponibles: {inventory_text}. Sugiere una receta."
        self._call_gemini_safe(prompt)

    def _call_gemini_safe(self, prompt):
        self.set_loading(True, "👨‍🍳 Cocinando idea... (Consultando IA)")
        try:
            if not gemini_service.client:
                self.set_loading(False, "❌ Error: Falta API Key.")
                return
            
            response = gemini_service.client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt
            )
            
            self.last_response_text = response.text
            self.recipe_card.content.value = response.text 
            self.recipe_card.visible = True
            self.copy_btn.visible = True
            
            self.set_loading(False, "✅ ¡Listo! Aquí tienes tu receta:")
            
        except Exception as ex:
            self.set_loading(False, f"❌ Error IA: {ex}")