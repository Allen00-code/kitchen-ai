import flet as ft
from src.services.supabase_service import supabase_client

class FavoritesView(ft.Column):
    def __init__(self):
        super().__init__()
        self.expand = True
        self.scroll = ft.ScrollMode.AUTO
        self.cards_column = ft.Column(spacing=15)
        
        self.controls = [
            ft.Container(
                padding=20,
                content=ft.Column([
                    ft.Row([
                        ft.Icon("menu_book", color="brown", size=30),
                        ft.Text("Mi Recetario Personal", size=24, weight="bold")
                    ]),
                    ft.Divider(),
                    self.cards_column
                ])
            )
        ]
        
    def did_mount(self):
        self.load_favorites()
        
    def load_favorites(self):
        self.cards_column.controls.clear()
        try:
            # Obtener recetas ordenadas por la más reciente
            res = supabase_client.table("saved_recipes").select("*").order("created_at", desc=True).execute()
            data = res.data
            
            if not data:
                self.cards_column.controls.append(
                    ft.Container(
                        content=ft.Column([
                            ft.Icon("cookie", size=50, color="grey"),
                            ft.Text("Aún no tienes recetas guardadas.", color="grey"),
                            ft.Text("Ve a 'Chef AI' para generar algunas.", size=12, color="grey")
                        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                        alignment=ft.alignment.center,
                        padding=40
                    )
                )
            else:
                for recipe in data:
                    self.cards_column.controls.append(self.create_card(recipe))
            self.update()
        except Exception as e:
            self.cards_column.controls.append(ft.Text(f"Error cargando: {e}"))
            self.update()
            
    def delete_recipe(self, r_id):
        try:
            supabase_client.table("saved_recipes").delete().eq("id", r_id).execute()
            self.load_favorites() # Recargar lista
            self.page.snack_bar = ft.SnackBar(ft.Text("Receta eliminada 🗑️"))
            self.page.snack_bar.open = True
            self.page.update()
        except: pass

    def create_card(self, recipe):
        return ft.Container(
            bgcolor="white", padding=15, border_radius=10,
            border=ft.border.all(1, "#E0E0E0"),
            shadow=ft.BoxShadow(blur_radius=5, color="#EEEEEE"),
            content=ft.Column([
                ft.Row([
                    ft.Text(recipe['title'], weight="bold", size=18, expand=True, color="black"),
                    ft.IconButton("delete", icon_color="red", tooltip="Borrar del recetario", 
                                  on_click=lambda _, x=recipe['id']: self.delete_recipe(x))
                ]),
                ft.Row([
                    ft.Container(
                        content=ft.Text(f"🏷️ {recipe.get('tags','')}", size=10, color="white"),
                        bgcolor="blue", padding=5, border_radius=5
                    )
                ]),
                ft.Container(height=10),
                ft.ExpansionTile(
                    title=ft.Text("Ver Ingredientes y Pasos", color="green", weight="bold"),
                    controls=[
                        ft.Divider(),
                        ft.Text("📝 Ingredientes:", weight="bold"),
                        ft.Text(recipe['ingredients'], size=14),
                        ft.Container(height=10),
                        ft.Text("🔥 Instrucciones:", weight="bold"),
                        ft.Text(recipe['instructions'], size=14),
                        ft.Container(height=10),
                    ]
                )
            ])
        )