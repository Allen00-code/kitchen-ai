import flet as ft
from src.services.supabase_service import supabase_client

class ShoppingView(ft.Column):
    def __init__(self):
        super().__init__()
        self.expand = True
        
        self.shopping_grid = ft.GridView(
            expand=True, runs_count=2, max_extent=200, child_aspect_ratio=0.8,
            spacing=10, run_spacing=10, padding=10
        )

        self.controls = [
            ft.Container(
                padding=20, expand=True,
                content=ft.Column([
                    ft.Text("🛒 Lista de Compras", size=24, weight="bold"),
                    ft.Text("Cosas que se acabaron o faltan.", color="grey"),
                    ft.Divider(),
                    self.shopping_grid
                ])
            )
        ]

    def did_mount(self):
        self.refresh_list()

    def refresh_list(self):
        self.shopping_grid.controls.clear()
        try:
            # Traemos solo lo que está en shopping_list = TRUE
            res = supabase_client.table("inventory").select("*").eq("is_shopping_list", True).order("id", desc=True).execute()
            items = res.data

            if not items:
                self.shopping_grid.controls.append(ft.Text("¡Todo comprado! 🎉"))
            else:
                for item in items:
                    self.shopping_grid.controls.append(self._create_card(item))
            
            self.update()
        except Exception as e:
            print(f"Error shopping list: {e}")

    def _create_card(self, item):
        return ft.Container(
            bgcolor="white", border_radius=15, padding=10,
            shadow=ft.BoxShadow(spread_radius=1, blur_radius=3, color="grey"),
            content=ft.Column([
                ft.Icon("shopping_cart", color="orange", size=30),
                ft.Text(item['name'], weight="bold", size=16, text_align="center"),
                ft.Text(f"Faltan: {item['quantity']} {item['unit']}", color="grey"),
                
                ft.ElevatedButton(
                    "¡Ya lo compré! ✅", 
                    bgcolor="green", color="white",
                    on_click=lambda e: self.mark_as_bought(item)
                )
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        )

    def mark_as_bought(self, item):
        try:
            # Al comprar, lo regresamos al inventario (is_shopping_list = False)
            # O podrías querer borrarlo. Aquí asumo que si lo compras, vuelve a la alacena.
            supabase_client.table("inventory").update({
                "is_shopping_list": False
            }).eq("id", item['id']).execute()
            
            self.page.snack_bar = ft.SnackBar(ft.Text(f"Reabastecido: {item['name']}"))
            self.page.snack_bar.open = True
            self.refresh_list()
        except Exception as e:
            print(e)