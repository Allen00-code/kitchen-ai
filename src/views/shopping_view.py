import flet as ft
from src.services.supabase_service import supabase_client

class ShoppingView(ft.Column):
    def __init__(self):
        super().__init__()
        self.expand = True
        
        self.item_name = ft.TextField(
            label="¿Qué hace falta?", 
            expand=True, 
            on_submit=self.add_item,
            text_size=16
        )
        
        self.add_btn = ft.IconButton(
            icon="add_circle", 
            icon_color="green", 
            icon_size=40, 
            on_click=self.add_item
        )

        # La lista ya tiene expand=True, pero necesitaba ayuda de sus padres
        self.shopping_list = ft.ListView(expand=True, spacing=10, padding=20)

        self.controls = [
            ft.Container(
                padding=20,
                expand=True, # <--- CAMBIO 1: El contenedor ocupa todo el alto
                content=ft.Column([
                    ft.Text("Lista de Compras 🛒", size=24, weight="bold"),
                    ft.Row([self.item_name, self.add_btn]),
                    ft.Divider(),
                    self.shopping_list
                ], expand=True) # <--- CAMBIO 2: La columna interna también se estira
            )
        ]

    def did_mount(self):
        if self.page:
            self.load_items()

    def load_items(self):
        self.shopping_list.controls.clear()
        try:
            # Traemos solo lo que es shopping_list = TRUE
            res = supabase_client.table("inventory").select("*").eq("is_shopping_list", True).order("id", desc=True).execute()
            
            if not res.data:
                self.shopping_list.controls.append(
                    ft.Container(
                        content=ft.Column([
                            ft.Icon("shopping_cart_checkout", size=50, color="grey"),
                            ft.Text("¡Todo comprado!", color="grey")
                        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                        alignment=ft.alignment.center,
                        padding=50
                    )
                )
            else:
                for item in res.data:
                    self.shopping_list.controls.append(self.create_item_row(item))
            self.update()
        except Exception as e:
            print(f"Error loading shopping list: {e}")

    def create_item_row(self, item):
        return ft.Container(
            bgcolor="white", padding=10, border_radius=10,
            shadow=ft.BoxShadow(spread_radius=1, blur_radius=2, color="#DDDDDD"),
            content=ft.Row([
                ft.Icon("circle_outlined", color="grey"),
                ft.Text(item['name'], size=16, expand=True, weight="bold"),
                ft.IconButton(
                    icon="check", 
                    icon_color="green", 
                    tooltip="¡Ya lo compré!",
                    on_click=lambda e: self.mark_as_bought(item)
                ),
                ft.IconButton(
                    icon="delete_outline", 
                    icon_color="red", 
                    tooltip="Borrar",
                    on_click=lambda e: self.delete_item(item['id'])
                )
            ])
        )

    def add_item(self, e):
        if not self.item_name.value: return
        try:
            supabase_client.table("inventory").insert({
                "name": self.item_name.value,
                "is_shopping_list": True,
                "is_pending_entry": False, 
                "quantity": 1,
                "unit": "pz" 
            }).execute()
            
            self.item_name.value = ""
            self.load_items()
            self.item_name.focus()
        except Exception as ex:
            print(f"Error adding: {ex}")

    def mark_as_bought(self, item):
        try:
            # Mueve el item a la Sala de Espera del Inventario
            supabase_client.table("inventory").update({
                "is_shopping_list": False,
                "is_pending_entry": True 
            }).eq("id", item['id']).execute()

            self.load_items()
            
            self.page.snack_bar = ft.SnackBar(ft.Text(f"✅ {item['name']} movido a 'Por Acomodar' en Inventario"))
            self.page.snack_bar.open = True
            self.page.update()
        except Exception as ex:
            print(f"Error buying: {ex}")

    def delete_item(self, item_id):
        try:
            supabase_client.table("inventory").delete().eq("id", item_id).execute()
            self.load_items()
        except Exception as ex:
            print(f"Error deleting: {ex}")