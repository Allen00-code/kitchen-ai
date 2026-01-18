import flet as ft
from src.services.supabase_service import supabase_client
import datetime
from text_unidecode import unidecode

class InventoryView(ft.Column):
    def __init__(self):
        super().__init__()
        self.expand = True
        self.editing_item_id = None 
        self.all_items = [] 
        self.pending_items = []

        # --- SECCIÓN PENDIENTES (SALA DE ESPERA) ---
        self.pending_section = ft.Container(visible=False)

        # --- BARRA DE BÚSQUEDA ---
        self.search_bar = ft.TextField(
            label="Buscar producto...", prefix_icon="search",
            border_radius=10, text_size=14, expand=True,
            on_change=lambda _: self.run_local_filter()
        )

        # Filtros
        self.filter_category = ft.Dropdown(label="Categoría", text_size=12, expand=True, on_change=lambda _: self.run_local_filter())
        self.filter_location = ft.Dropdown(label="Ubicación", text_size=12, expand=True, on_change=lambda _: self.run_local_filter())

        # --- GRID PRINCIPAL (AQUÍ ESTÁ LA CORRECCIÓN) ---
        # Aplicamos el padding aquí mismo para no romper la referencia
        self.inventory_grid = ft.GridView(
            expand=True, 
            runs_count=2, 
            max_extent=200, 
            child_aspect_ratio=0.75,
            spacing=10, 
            run_spacing=10, 
            # Padding: Izq, Arr, Der, Abajo (80px para librar el botón flotante)
            padding=ft.padding.only(left=10, top=10, right=10, bottom=80) 
        )
        
        self.no_results_text = ft.Container(
            content=ft.Column([
                ft.Icon("search_off", size=40, color="grey"),
                ft.Text("No encontramos ese producto 🤷‍♂️", color="grey")
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            alignment=ft.alignment.center, visible=False, padding=20
        )
        
        # Formulario
        self.name_ref = ft.Ref[ft.TextField]()
        self.qty_ref = ft.Ref[ft.TextField]()
        self.unit_ref = ft.Ref[ft.Dropdown]()
        self.category_ref = ft.Ref[ft.Dropdown]()
        self.packaging_ref = ft.Ref[ft.Dropdown]()
        self.location_ref = ft.Ref[ft.Dropdown]()
        self.form_title = ft.Ref[ft.Text]()
        self.homemade_switch = ft.Switch(label="🏠 Hecho en Casa", value=False)
        self.date_text = ft.Ref[ft.TextField]()
        self.date_picker = ft.DatePicker(
            on_change=self.on_date_change,
            first_date=datetime.datetime(2023, 1, 1),
            last_date=datetime.datetime(2030, 12, 31)
        )
        self.btn_delete = ft.ElevatedButton(
            "Eliminar", icon="delete", bgcolor="red", color="white", 
            on_click=lambda _: self.open_delete_dialog(), visible=False
        )

        self.form_view = self._build_form()
        self.list_view = self._build_list()
        self.controls = [self.list_view]

    def did_mount(self):
        if not self.page: return
        self.page.overlay.append(self.date_picker)
        self.page.floating_action_button = ft.FloatingActionButton(
            icon="add", bgcolor="blue", on_click=lambda _: self.open_form_for_create()
        )
        self.load_catalogs()
        self.load_inventory_data()
        self.page.update()

    def _build_list(self):
        return ft.Container(
            expand=True, padding=10,
            content=ft.Column([
                ft.Row([
                    ft.Text("Mi Inventario", size=24, weight="bold"),
                    ft.IconButton("refresh", tooltip="Recargar", on_click=lambda _: self.load_inventory_data())
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                
                self.pending_section,
                
                ft.Row([self.search_bar]),
                ft.Row([self.filter_location, self.filter_category]),
                ft.Divider(height=10, color="transparent"),
                
                # Stack simple: Grid original + Texto de vacío
                ft.Stack([
                    self.inventory_grid, 
                    self.no_results_text
                ], expand=True)

            ], expand=True) 
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
                ft.Row([ft.Icon("house", color="brown"), self.homemade_switch]),
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
                ft.Dropdown(ref=self.packaging_ref, label="Envase"),
                ft.Container(height=20),
                ft.Column([
                    ft.Row([ft.ElevatedButton("Guardar y Acomodar ✅", on_click=self.save_product, bgcolor="green", color="white", expand=True, height=45)]),
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
            self.load_inventory_data() 
            self.page.floating_action_button = ft.FloatingActionButton(
                icon="add", bgcolor="blue", on_click=lambda _: self.open_form_for_create()
            )
        self.update()

    # --- CARGA DE DATOS ---
    def load_inventory_data(self):
        try:
            self.inventory_grid.controls.clear()
            self.no_results_text.visible = False
            
            res = supabase_client.table("inventory").select(
                "*, categories(name, color), locations(name), packaging_types(name)"
            ).eq("is_shopping_list", False).order("id", desc=True).execute()
            
            raw_data = res.data
            
            self.pending_items = [i for i in raw_data if i.get('is_pending_entry') is True]
            self.all_items = [i for i in raw_data if i.get('is_pending_entry') is not True]
            
            self.render_pending_section()
            self.run_local_filter()
            
        except Exception as e:
            print(f"Error loading data: {e}")

    def render_pending_section(self):
        if not self.pending_items:
            self.pending_section.visible = False
        else:
            self.pending_section.visible = True
            
            pending_row = ft.Row(scroll=ft.ScrollMode.HIDDEN)
            for item in self.pending_items:
                pending_row.controls.append(
                    ft.Container(
                        bgcolor="#E3F2FD", border=ft.border.all(1, "blue"),
                        border_radius=8, padding=10,
                        content=ft.Row([
                            ft.Icon("input", color="blue"),
                            ft.Text(item['name'], weight="bold", color="blue"),
                            ft.Text("Editar >", size=10, color="grey")
                        ]),
                        on_click=lambda _, x=item: self.open_form_for_edit(x)
                    )
                )

            self.pending_section.content = ft.Column([
                ft.Text(f"📥 {len(self.pending_items)} Recién comprados (Da click para acomodar):", size=12, weight="bold", color="blue"),
                pending_row,
                ft.Divider()
            ])

    # --- FILTRADO LOCAL ---
    def run_local_filter(self):
        filtered = self.all_items 
        
        if self.search_bar.value:
            search_term = unidecode(self.search_bar.value.lower())
            filtered = [i for i in filtered if search_term in unidecode(i['name'].lower())]

        if self.filter_location.value and self.filter_location.value != "Todas":
            filtered = [i for i in filtered if i['locations'] and i['locations']['name'] == self.filter_location.value]
            
        if self.filter_category.value and self.filter_category.value != "Todas":
            filtered = [i for i in filtered if i['categories'] and i['categories']['name'] == self.filter_category.value]

        self.inventory_grid.controls.clear()
        
        if not filtered:
            self.inventory_grid.visible = False
            self.no_results_text.visible = True
        else:
            self.inventory_grid.visible = True
            self.no_results_text.visible = False
            for item in filtered:
                self.inventory_grid.controls.append(self._create_item_card(item))
        
        if self.page: self.update()

    def _create_item_card(self, item):
        cat_data = item['categories'] or {}
        color = cat_data.get('color', '#CCCCCC')
        cat_name = cat_data.get('name', '').lower()
        icon_name = "kitchen"
        
        if "carn" in cat_name: icon_name = "restaurant"
        elif "lact" in cat_name: icon_name = "water_drop"
        elif "veg" in cat_name: icon_name = "eco"
        elif "bebida" in cat_name: icon_name = "local_bar"
        elif "fruta" in cat_name: icon_name = "apple"
        
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
                ft.Container(content=ft.Text(f"Exp: {item['expiry_date']}" if item.get('expiry_date') else "", size=10, color="orange"))
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=2)
        )

    # --- UTILIDADES DE FECHA Y CRUD ---
    def safe_open_date_picker(self, e):
        try: self.date_picker.pick_date()
        except: 
            try: self.page.open(self.date_picker)
            except: pass

    def on_date_change(self, e):
        if self.date_picker.value:
            self.date_text.current.value = self.date_picker.value.strftime("%Y-%m-%d")
            self.update()

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
        self.form_title.current.value = "Completar Registro" if item.get('is_pending_entry') else "Editar Producto"
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
                    "is_shopping_list": True, "location_id": None, "expiry_date": None, "is_pending_entry": False
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
            locs.sort(key=lambda x: x['name'])
            opts_loc = [ft.dropdown.Option(l['name']) for l in locs]
            self.location_ref.current.options = opts_loc
            self.filter_location.options = [ft.dropdown.Option("Todas")] + opts_loc
            
            cats = supabase_client.table("categories").select("*").execute().data
            cats.sort(key=lambda x: x['name'])
            opts_cat = [ft.dropdown.Option(c['name']) for c in cats]
            self.category_ref.current.options = opts_cat
            self.filter_category.options = [ft.dropdown.Option("Todas")] + opts_cat
            
            pkgs = supabase_client.table("packaging_types").select("*").execute().data
            pkgs.sort(key=lambda x: x['name'])
            self.packaging_ref.current.options = [ft.dropdown.Option(p['name']) for p in pkgs]
            self.update()
        except: pass

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
                "is_shopping_list": False,
                "is_pending_entry": False
            }

            if self.editing_item_id:
                supabase_client.table("inventory").update(data).eq("id", self.editing_item_id).execute()
                msg = "Registro completado ✅"
            else:
                supabase_client.table("inventory").insert(data).execute()
                msg = "Creado"

            self.page.snack_bar = ft.SnackBar(ft.Text(msg))
            self.page.snack_bar.open = True
            self.toggle_mode("list")
        except Exception as ex:
            print(f"Error save: {ex}")
            if self.page: self.page.update()