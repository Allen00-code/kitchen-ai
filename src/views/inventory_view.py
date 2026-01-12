import flet as ft
from src.services.supabase_service import supabase_client
import datetime

class InventoryView(ft.Column):
    def __init__(self):
        super().__init__()
        self.expand = True
        self.editing_item_id = None 

        # Filtros
        self.filter_category = ft.Dropdown(label="Categoría", text_size=12, expand=True, on_change=lambda _: self.refresh_list())
        self.filter_location = ft.Dropdown(label="Ubicación", text_size=12, expand=True, on_change=lambda _: self.refresh_list())

        # Grid
        self.inventory_grid = ft.GridView(
            expand=True, runs_count=2, max_extent=200, child_aspect_ratio=0.75,
            spacing=10, run_spacing=10, padding=10
        )
        
        # Formulario
        self.name_ref = ft.Ref[ft.TextField]()
        self.qty_ref = ft.Ref[ft.TextField]()
        self.unit_ref = ft.Ref[ft.Dropdown]()
        self.category_ref = ft.Ref[ft.Dropdown]()
        self.packaging_ref = ft.Ref[ft.Dropdown]()
        self.location_ref = ft.Ref[ft.Dropdown]()
        self.form_title = ft.Ref[ft.Text]()
        
        # Switch de Casero
        self.homemade_switch = ft.Switch(label="🏠 Hecho en Casa", value=False)
        
        self.date_text = ft.Ref[ft.TextField]()
        self.date_picker = ft.DatePicker(
            on_change=self.on_date_change,
            first_date=datetime.datetime(2023, 1, 1),
            last_date=datetime.datetime(2030, 12, 31)
        )
        
        self.btn_delete = ft.ElevatedButton(
            "Eliminar Producto", icon="delete", bgcolor="red", color="white", 
            on_click=lambda _: self.open_delete_dialog(), visible=False
        )

        self.form_view = self._build_form()
        self.list_view = self._build_list()
        self.controls = [self.list_view]

    def did_mount(self):
        # --- CORRECCIÓN DE SEGURIDAD ---
        # Si la página no está lista (None), abortamos para evitar el error en terminal
        if not self.page:
            return

        self.page.overlay.append(self.date_picker)
        self.page.floating_action_button = ft.FloatingActionButton(
            icon="add", bgcolor="blue", on_click=lambda _: self.open_form_for_create()
        )
        self.load_catalogs()
        self.refresh_list()
        self.page.update()

    def _build_list(self):
        return ft.Container(
            expand=True, padding=10,
            content=ft.Column([
                ft.Row([
                    ft.Text("Mi Inventario", size=24, weight="bold"),
                    ft.IconButton("refresh", on_click=lambda _: self.refresh_list())
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Row([self.filter_location, self.filter_category]),
                ft.Divider(height=10, color="transparent"),
                self.inventory_grid
            ])
        )

    def _build_form(self):
        return ft.Container(
            padding=20, expand=True,
            content=ft.Column([
                ft.Row([
                    ft.IconButton("arrow_back", on_click=lambda _: self.toggle_mode("list")),
                    ft.Text(ref=self.form_title, value="Nuevo Producto", size=20, weight="bold")
                ]),
                ft.Divider(),
                ft.TextField(ref=self.name_ref, label="Nombre del Producto", autofocus=True),
                
                ft.Row([
                    ft.Icon("house", color="brown"),
                    self.homemade_switch
                ]),
                
                ft.Row([
                    ft.TextField(ref=self.qty_ref, label="Cant", value="1", width=100, keyboard_type="number"),
                    ft.Dropdown(ref=self.unit_ref, label="Unidad", options=[
                        ft.dropdown.Option("pz"), ft.dropdown.Option("kg"), ft.dropdown.Option("lt"), ft.dropdown.Option("gr")
                    ], value="pz", expand=True)
                ]),
                
                ft.Row([
                    ft.TextField(ref=self.date_text, label="Fecha Caducidad", expand=True, hint_text="YYYY-MM-DD"),
                    ft.IconButton(icon="calendar_month", icon_color="blue", on_click=self.safe_open_date_picker)
                ]),

                ft.Dropdown(ref=self.category_ref, label="Categoría"),
                ft.Dropdown(ref=self.location_ref, label="Ubicación"),
                ft.Dropdown(ref=self.packaging_ref, label="Envase (Tallo, Bolsa...)"),
                
                ft.Container(height=20),
                
                ft.Column([
                    ft.Row([ft.ElevatedButton("Guardar", on_click=self.save_product, bgcolor="green", color="white", expand=True, height=45)]),
                    ft.Container(height=10),
                    self.btn_delete 
                ]),
                ft.Container(height=50)
            ], scroll=ft.ScrollMode.ALWAYS, expand=True)
        )

    def toggle_mode(self, mode):
        if mode == "form":
            self.controls = [self.form_view]
            self.page.floating_action_button = None
        else:
            self.controls = [self.list_view]
            self.refresh_list()
            self.page.floating_action_button = ft.FloatingActionButton(
                icon="add", bgcolor="blue", on_click=lambda _: self.open_form_for_create()
            )
        self.update()

    def safe_open_date_picker(self, e):
        try: self.date_picker.pick_date()
        except: 
            try: self.page.open(self.date_picker)
            except: pass

    def on_date_change(self, e):
        if self.date_picker.value:
            self.date_text.current.value = self.date_picker.value.strftime("%Y-%m-%d")
            self.update()

    # --- CRUD ---
    def open_form_for_create(self):
        self.editing_item_id = None
        self.form_title.current.value = "Nuevo Producto"
        self.name_ref.current.value = ""
        self.qty_ref.current.value = "1"
        self.date_text.current.value = ""
        self.homemade_switch.value = False 
        self.btn_delete.visible = False 
        self.toggle_mode("form")

    def open_form_for_edit(self, item):
        self.editing_item_id = item['id']
        self.form_title.current.value = "Editar Producto"
        self.name_ref.current.value = item['name']
        self.qty_ref.current.value = str(item['quantity'])
        self.unit_ref.current.value = item['unit']
        self.date_text.current.value = item.get('expiry_date') or ""
        self.homemade_switch.value = item.get('is_homemade', False) 
        
        if item['categories']: self.category_ref.current.value = item['categories']['name']
        if item['locations']: self.location_ref.current.value = item['locations']['name']
        if item['packaging_types']: self.packaging_ref.current.value = item['packaging_types']['name']
        
        self.btn_delete.visible = True
        self.toggle_mode("form")

    def open_delete_dialog(self):
        dialog = ft.AlertDialog(
            title=ft.Text("🗑️ Eliminar Producto"),
            content=ft.Text("¿Qué quieres hacer?"),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda e: self.close_dialog(dialog)),
                ft.TextButton("Solo Borrar", on_click=lambda e: self.execute_delete(to_cart=False, dlg=dialog), style=ft.ButtonStyle(color="red")),
                ft.ElevatedButton("Mover al Carrito", on_click=lambda e: self.execute_delete(to_cart=True, dlg=dialog), bgcolor="green", color="white"),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        self.page.open(dialog)

    def close_dialog(self, dlg):
        self.page.close(dlg)

    def execute_delete(self, to_cart, dlg):
        if not self.editing_item_id: return
        try:
            if to_cart:
                supabase_client.table("inventory").update({
                    "is_shopping_list": True,
                    "location_id": None,
                    "expiry_date": None
                }).eq("id", self.editing_item_id).execute()
                msg = "Movido al Carrito 🛒"
            else:
                supabase_client.table("inventory").delete().eq("id", self.editing_item_id).execute()
                msg = "Eliminado 🗑️"
            
            self.page.snack_bar = ft.SnackBar(ft.Text(msg))
            self.page.snack_bar.open = True
            self.page.close(dlg)
            self.toggle_mode("list")
        except Exception as e:
            print(f"Error delete: {e}")
            self.page.close(dlg)

    def load_catalogs(self):
        try:
            locs = supabase_client.table("locations").select("*").execute().data
            opts_loc = [ft.dropdown.Option(l['name']) for l in locs]
            self.location_ref.current.options = opts_loc
            self.filter_location.options = [ft.dropdown.Option("Todas")] + opts_loc
            
            cats = supabase_client.table("categories").select("*").execute().data
            opts_cat = [ft.dropdown.Option(c['name']) for c in cats]
            self.category_ref.current.options = opts_cat
            self.filter_category.options = [ft.dropdown.Option("Todas")] + opts_cat
            
            pkgs = supabase_client.table("packaging_types").select("*").execute().data
            self.packaging_ref.current.options = [ft.dropdown.Option(p['name']) for p in pkgs]
            self.update()
        except: pass

    def refresh_list(self):
        self.inventory_grid.controls.clear()
        try:
            res = supabase_client.table("inventory").select(
                "*, categories(name, color), locations(name), packaging_types(name)"
            ).eq("is_shopping_list", False).order("id", desc=True).execute()
            items = res.data
            
            if self.filter_location.value and self.filter_location.value != "Todas":
                items = [i for i in items if i['locations'] and i['locations']['name'] == self.filter_location.value]
            if self.filter_category.value and self.filter_category.value != "Todas":
                items = [i for i in items if i['categories'] and i['categories']['name'] == self.filter_category.value]

            if not items:
                self.inventory_grid.controls.append(ft.Text("No hay productos 🤷‍♂️"))
            else:
                for item in items:
                    self.inventory_grid.controls.append(self._create_item_card(item))
            
            # --- CORRECCIÓN DE SEGURIDAD ---
            # Solo actualizamos si la página existe
            if self.page:
                self.update()
        except Exception as e:
            print(f"Error refresh: {e}")

    def _create_item_card(self, item):
        cat_data = item['categories'] or {}
        color = cat_data.get('color', '#CCCCCC')
        icon_name = "kitchen"
        if "carn" in cat_data.get('name', '').lower(): icon_name = "restaurant"
        elif "lact" in cat_data.get('name', '').lower(): icon_name = "water_drop"
        elif "veg" in cat_data.get('name', '').lower(): icon_name = "eco"
        
        homemade_badge = ft.Container()
        if item.get('is_homemade'):
            homemade_badge = ft.Container(
                content=ft.Text("🏠 Casero", size=10, color="white"),
                bgcolor="brown", padding=3, border_radius=5
            )

        return ft.Container(
            bgcolor="white", border_radius=15, padding=10,
            shadow=ft.BoxShadow(spread_radius=1, blur_radius=3, color="grey"),
            on_click=lambda _: self.open_form_for_edit(item),
            content=ft.Column([
                ft.Container(bgcolor=color, height=5, border_radius=ft.border_radius.only(top_left=15, top_right=15), margin=ft.margin.only(left=-10, right=-10, top=-10)),
                ft.Container(height=5),
                ft.Row([ft.Icon(icon_name, size=35, color=color), homemade_badge], alignment=ft.MainAxisAlignment.CENTER),
                ft.Text(item['name'], weight="bold", size=14, max_lines=2, overflow="ellipsis", text_align="center"),
                ft.Text(f"{item['quantity']} {item['unit']}", size=12, color="grey", text_align="center"),
                ft.Container(
                    content=ft.Text(f"Exp: {item['expiry_date']}" if item.get('expiry_date') else "", size=10, color="orange")
                )
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=2)
        )

    def save_product(self, e):
        if not self.name_ref.current.value:
            self.name_ref.current.error_text = "Requerido"
            self.update()
            return
        try:
            loc_val, cat_val, pkg_val = self.location_ref.current.value, self.category_ref.current.value, self.packaging_ref.current.value
            loc_id, cat_id, pkg_id = None, None, None

            if loc_val:
                r = supabase_client.table("locations").select("id").eq("name", loc_val).execute()
                if r.data: loc_id = r.data[0]['id']
            if cat_val:
                r = supabase_client.table("categories").select("id").eq("name", cat_val).execute()
                if r.data: cat_id = r.data[0]['id']
            if pkg_val:
                r = supabase_client.table("packaging_types").select("id").eq("name", pkg_val).execute()
                if r.data: pkg_id = r.data[0]['id']

            data = {
                "name": self.name_ref.current.value,
                "quantity": float(self.qty_ref.current.value or 0),
                "unit": self.unit_ref.current.value,
                "category_id": cat_id, "location_id": loc_id, "packaging_id": pkg_id,
                "expiry_date": self.date_text.current.value if self.date_text.current.value else None,
                "is_homemade": self.homemade_switch.value,
                "is_shopping_list": False
            }

            if self.editing_item_id:
                supabase_client.table("inventory").update(data).eq("id", self.editing_item_id).execute()
                msg = "Actualizado"
            else:
                supabase_client.table("inventory").insert(data).execute()
                msg = "Creado"

            self.page.snack_bar = ft.SnackBar(ft.Text(f"✅ {msg}"))
            self.page.snack_bar.open = True
            self.toggle_mode("list")
        except Exception as ex:
            print(f"Error save: {ex}")
            if self.page: self.page.update()