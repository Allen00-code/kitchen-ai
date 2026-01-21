import flet as ft
from src.services.supabase_service import supabase_client

class ShoppingView(ft.Column):
    def __init__(self):
        super().__init__()
        self.expand = True
        
        # --- UI INPUTS ---
        self.new_item_name = ft.TextField(
            hint_text="¿Qué falta? (ej. Leche)", 
            expand=True, 
            on_submit=self.add_item,
            text_size=16,
            border_color="blue",
            focused_border_color="blue"
        )
        self.btn_add = ft.IconButton(
            icon="add_circle", 
            icon_color="blue", 
            icon_size=40,
            tooltip="Agregar a la lista",
            on_click=self.add_item
        )
        
        # --- LISTA ---
        self.shopping_list = ft.Column(spacing=10, scroll=ft.ScrollMode.AUTO)

        self.controls = [
            ft.Container(
                padding=20,
                content=ft.Column([
                    ft.Text("Lista de Compras 🛒", size=24, weight="bold"),
                    ft.Text("Cosas que faltan en la cocina", color="grey"),
                    ft.Divider(),
                    ft.Row([self.new_item_name, self.btn_add]),
                    ft.Container(height=20),
                    self.shopping_list
                ])
            )
        ]

    def did_mount(self):
        self.load_items()

    def load_items(self):
        self.shopping_list.controls.clear()
        try:
            # Supabase filtra automáticamente por user_id gracias a RLS
            res = supabase_client.table("inventory").select("*").eq("is_shopping_list", True).order("id", desc=True).execute()
            data = res.data
            
            if not data:
                self.shopping_list.controls.append(
                    ft.Container(
                        content=ft.Column([
                            ft.Icon("check_circle_outline", size=50, color="green"),
                            ft.Text("¡Todo listo! No hace falta nada.", color="grey")
                        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                        alignment=ft.alignment.center,
                        padding=40
                    )
                )
            else:
                for item in data:
                    self.shopping_list.controls.append(self.create_item_row(item))
            
            self.update()
        except Exception as e:
            print(f"Error loading shopping list: {e}")

    def add_item(self, e):
        if not self.new_item_name.value: return

        # --- CORRECCIÓN CRÍTICA: OBTENER USER_ID ---
        user = supabase_client.auth.get_user()
        user_id = user.user.id if user and user.user else None
        
        if not user_id:
            self.page.snack_bar = ft.SnackBar(ft.Text("❌ Error de sesión. Reloguea por favor."))
            self.page.snack_bar.open = True
            self.page.update()
            return
        # -------------------------------------------

        try:
            supabase_client.table("inventory").insert({
                "name": self.new_item_name.value,
                "quantity": 1, # Default
                "unit": "pz",  # Default
                "is_shopping_list": True,
                "is_pending_entry": True, # Para que cuando se mueva a inventario, pida confirmar
                "user_id": user_id # <--- LA LLAVE QUE FALTABA
            }).execute()
            
            self.new_item_name.value = ""
            self.new_item_name.focus()
            self.load_items()
            
        except Exception as ex:
            print(f"Error adding: {ex}")
            self.page.snack_bar = ft.SnackBar(ft.Text(f"Error: {ex}"))
            self.page.snack_bar.open = True
            self.page.update()

    def delete_item(self, item_id):
        try:
            supabase_client.table("inventory").delete().eq("id", item_id).execute()
            self.load_items()
        except Exception as e:
            print(f"Error deleting: {e}")

    def move_to_inventory(self, item):
        # Al mover al inventario, solo cambiamos el flag.
        # El user_id YA EXISTE, así que no violamos ninguna regla de RLS al hacer update.
        try:
            supabase_client.table("inventory").update({
                "is_shopping_list": False,
                "is_pending_entry": True # Lo mandamos a "pendientes" en el inventario para revisar caducidad
            }).eq("id", item['id']).execute()
            
            self.page.snack_bar = ft.SnackBar(ft.Text(f"✅ {item['name']} comprado"))
            self.page.snack_bar.open = True
            self.load_items()
            self.page.update()
        except Exception as e:
            print(f"Error moving: {e}")

    def create_item_row(self, item):
        return ft.Container(
            bgcolor="white", padding=10, border_radius=10,
            border=ft.border.all(1, "#E0E0E0"),
            content=ft.Row([
                ft.Icon("radio_button_unchecked", color="grey"),
                ft.Text(item['name'], size=16, weight="bold", expand=True),
                ft.IconButton(
                    icon="check", 
                    icon_color="green", 
                    tooltip="¡Ya lo compré!",
                    on_click=lambda _, x=item: self.move_to_inventory(x)
                ),
                ft.IconButton(
                    icon="delete", 
                    icon_color="red", 
                    tooltip="Borrar",
                    on_click=lambda _, x=item['id']: self.delete_item(x)
                )
            ])
        )