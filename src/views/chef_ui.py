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
        
        # Estado para controlar la visibilidad del menú manual
        self.manual_menu_visible = False

        # --- TERMINAL (LOG) ---
        self.terminal = ft.TextField(
            value="✅ Sistema listo. Esperando comando...",
            multiline=True, read_only=True, min_lines=10, max_lines=20, text_size=12,
            bgcolor="#1E1E1E", color="#33FF00", border_color="grey",
            text_style=ft.TextStyle(font_family="monospace")
        )

        self.theme_toggle_btn = ft.IconButton(icon="dark_mode", tooltip="Tema", on_click=self.toggle_terminal_theme)

        # --- CONFIGURACIÓN ---
        self.meal_type_selector = ft.Dropdown(
            label="Tipo de Comida",
            options=[
                ft.dropdown.Option("Cualquiera"), ft.dropdown.Option("Desayuno"),
                ft.dropdown.Option("Almuerzo"), ft.dropdown.Option("Cena"), ft.dropdown.Option("Snack")
            ],
            value="Cualquiera", expand=True
        )
        
        self.fit_mode_switch = ft.Switch(label="🥗 Modo Fit (Bajo en calorías)", value=False)
        
        # Switch para Modo Exclusión
        self.exclusion_mode_switch = ft.Switch(
            label="🚫 Modo Exclusión (Usar todo MENOS lo marcado)", 
            value=False,
            active_color="red"
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
                    ft.Container(padding=10, border=ft.border.all(1, "grey"), border_radius=10, content=ft.Column([ft.Text("Configuración:", weight="bold"), ft.Row([self.meal_type_selector]), ft.Row([self.fit_mode_switch])])),
                    ft.Container(height=10),
                    ft.Row([self.btn_auto, self.btn_manual]),
                    ft.Divider(),
                    self.workspace,
                    ft.Divider(),
                    ft.Row([
                        ft.Text("Log del Sistema (Chef AI):", size=12, color="grey"),
                        ft.Row([self.theme_toggle_btn, ft.IconButton(icon="content_copy", tooltip="Copiar", on_click=self.copy_to_clipboard)])
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    self.terminal
                ])
            )
        ]
        
        self.selected_ingredients_names = set()
        self.cached_manual_items = [] 

    # --- UTILIDADES ---
    def log(self, message):
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        self.terminal.value += f"\n[{timestamp}] {message}"
        try: self.terminal.update()
        except: pass

    def clear_log(self):
        self.terminal.value = "--- NUEVA OPERACIÓN ---"
        try: self.terminal.update()
        except: pass

    def copy_to_clipboard(self, e):
        self.page.set_clipboard(self.terminal.value)
        self.page.snack_bar = ft.SnackBar(ft.Text("✅ Copiado"))
        self.page.snack_bar.open = True
        self.page.update()

    def toggle_terminal_theme(self, e):
        self.is_dark_mode = not self.is_dark_mode
        if self.is_dark_mode:
            self.terminal.bgcolor = "#1E1E1E"
            self.terminal.color = "#33FF00"
            self.theme_toggle_btn.icon = "dark_mode"
        else:
            self.terminal.bgcolor = "white"
            self.terminal.color = "black"
            self.theme_toggle_btn.icon = "light_mode"
        self.terminal.update()
        self.theme_toggle_btn.update()

    # --- FORMATEADOR INTELIGENTE ---
    def _format_ingredients_detailed(self, items_list):
        grouped = {}
        for item in items_list:
            cat_name = "Otros"
            if item.get('categories') and item['categories'].get('name'):
                cat_name = item['categories']['name']
            
            if cat_name not in grouped: grouped[cat_name] = []
            
            detail = f"{item['quantity']} {item['unit']} de {item['name']}"
            grouped[cat_name].append(detail)
        
        final_str = ""
        for category, ingredients in grouped.items():
            ing_list = ", ".join(ingredients)
            final_str += f"\n- En {category} tengo: {ing_list}."
        return final_str

    # --- PROMPT ---
    def build_system_prompt(self):
        meal = self.meal_type_selector.value
        is_fit = self.fit_mode_switch.value
        base = "Actúa como un Chef experto."
        if meal != "Cualquiera": base += f" El usuario quiere cocinar: {meal.upper()}."
        if is_fit: base += " RESTRICCIÓN: Receta FIT, baja en calorías."
        base += " Dame una respuesta EXTENSA. Incluye cantidades exactas."
        base += " REGLA DE ORO: Usa ESTRICTAMENTE los ingredientes dados y sus CANTIDADES. Si tengo 1 huevo, no pidas 3. Puedes sugerir básicos (sal, aceite)."
        return base

    # --- MODO AUTO ---
    def run_auto_mode(self, e):
        # 1. Limpiamos cualquier menú manual abierto
        self.workspace.controls.clear()
        self.manual_menu_visible = False 
        try: self.workspace.update()
        except: pass
        
        self.clear_log()
        self.log("🔵 Iniciando Modo Auto...")
        
        try:
            self.log("📡 Leyendo inventario completo...")
            res = supabase_client.table("inventory").select("name, quantity, unit, categories(name)").eq("is_shopping_list", False).execute()
            
            if not res.data:
                self.log("⚠️ Inventario vacío.")
                return

            inventory_text = self._format_ingredients_detailed(res.data)
            self.log(f"✅ Inventario analizado por categorías.")
            
            sys_prompt = self.build_system_prompt()
            prompt = f"{sys_prompt} Mi inventario detallado es: {inventory_text}. Dame 3 recetas posibles."
            self._call_gemini_safe(prompt)
            
        except Exception as ex:
            self.log(f"❌ Error: {ex}")

    # --- MODO MANUAL (CON TOGGLE) ---
    def setup_manual_mode(self, e):
        # LOGICA TOGGLE: Si ya está visible, lo ocultamos y salimos
        if self.manual_menu_visible:
            self.workspace.controls.clear()
            self.workspace.update()
            self.manual_menu_visible = False
            self.log("🟠 Menú de ingredientes oculto.")
            return

        # Si no está visible, lo abrimos
        self.manual_menu_visible = True
        self.clear_log()
        self.log("🟠 Cargando ingredientes...")
        self.workspace.controls.clear()
        self.selected_ingredients_names.clear()
        self.cached_manual_items = []
        
        try:
            res = supabase_client.table("inventory").select("name, quantity, unit, categories(name)").eq("is_shopping_list", False).execute()
            
            if not res.data:
                self.workspace.controls.append(ft.Text("Sin ingredientes."))
            else:
                self.cached_manual_items = res.data
                
                # Agregamos el switch de exclusión
                self.workspace.controls.append(
                    ft.Container(
                        bgcolor="#FFF3E0", padding=5, border_radius=5,
                        content=self.exclusion_mode_switch
                    )
                )
                self.workspace.controls.append(ft.Text("Marca los ingredientes:", weight="bold"))
                
                for item in res.data:
                    txt = f"{item['name']} ({item['quantity']} {item['unit']})"
                    chk = ft.Checkbox(label=txt, value=False, on_change=lambda e, x=item['name']: self.toggle_selection(e, x))
                    self.workspace.controls.append(chk)
                
                self.workspace.controls.append(ft.ElevatedButton("🍳 Cocinar", bgcolor="green", color="white", on_click=self.run_manual_action))
            self.workspace.update()
            
        except Exception as ex:
            self.log(f"❌ Error: {ex}")

    def toggle_selection(self, e, name):
        if e.control.value: self.selected_ingredients_names.add(name)
        else: self.selected_ingredients_names.discard(name)

    def run_manual_action(self, e):
        is_exclusion = self.exclusion_mode_switch.value
        final_items_data = []

        if is_exclusion:
            if not self.selected_ingredients_names:
                self.log("ℹ️ No marcaste nada para excluir. Usando TODO el inventario.")
                final_items_data = self.cached_manual_items
            else:
                final_items_data = [item for item in self.cached_manual_items if item['name'] not in self.selected_ingredients_names]
                excluded_str = ", ".join(self.selected_ingredients_names)
                self.log(f"🚫 Excluyendo: {excluded_str}")
        else:
            if not self.selected_ingredients_names:
                self.log("⚠️ Marca al menos un ingrediente (o activa modo exclusión).")
                return
            final_items_data = [item for item in self.cached_manual_items if item['name'] in self.selected_ingredients_names]

        if not final_items_data:
            self.log("⚠️ No quedaron ingredientes disponibles para cocinar.")
            return

        inventory_text = self._format_ingredients_detailed(final_items_data)
        
        mode_txt = "EXCLUYENDO lo marcado" if is_exclusion else "USANDO lo marcado"
        self.log(f"🍳 Cocinando ({mode_txt})...")
        
        sys_prompt = self.build_system_prompt()
        prompt = f"{sys_prompt} Tengo disponibles obligatoriamente estos ingredientes: {inventory_text}. Crea una receta."
        self._call_gemini_safe(prompt)

    def _call_gemini_safe(self, prompt):
        self.log("🚀 Consultando a Gemini...")
        try:
            if not gemini_service.client:
                self.log("❌ Error: Falta API Key.")
                return
            response = gemini_service.client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt
            )
            self.log("\n✨ RECETA GENERADA:\n" + ("="*40))
            self.log(response.text)
            self.log("="*40)
        except Exception as ex:
            self.log(f"❌ Error IA: {ex}")