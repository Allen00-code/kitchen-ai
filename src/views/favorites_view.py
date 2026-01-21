import flet as ft
from src.services.supabase_service import supabase_client

class FavoritesView(ft.Column):
    def __init__(self):
        super().__init__()
        self.expand = True
        self.scroll = ft.ScrollMode.AUTO
        self.recipes_column = ft.Column(spacing=15)

        self.controls = [
            ft.Container(
                padding=20,
                content=ft.Column([
                    ft.Text("Mis Recetas Guardadas 📖", size=24, weight="bold"),
                    ft.Divider(),
                    self.recipes_column
                ])
            )
        ]

    def did_mount(self):
        if self.page:
            self.load_recipes()

    def load_recipes(self):
        self.recipes_column.controls.clear()
        try:
            # Supabase filtra automáticamente por usuario gracias a RLS
            res = supabase_client.table("saved_recipes").select("*").order("created_at", desc=True).execute()
            
            if not res.data:
                self.recipes_column.controls.append(
                    ft.Container(
                        content=ft.Column([
                            ft.Icon("no_meals", size=50, color="grey"),
                            ft.Text("No tienes recetas guardadas aún.", color="grey")
                        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                        alignment=ft.alignment.center,
                        padding=40
                    )
                )
            else:
                for recipe in res.data:
                    self.recipes_column.controls.append(self.create_card(recipe))
            self.update()
        except Exception as e:
            print(f"Error loading favorites: {e}")

    def delete_recipe(self, r_id):
        try:
            supabase_client.table("saved_recipes").delete().eq("id", r_id).execute()
            self.page.snack_bar = ft.SnackBar(ft.Text("Receta eliminada"))
            self.page.snack_bar.open = True
            self.page.update()
            self.load_recipes()
        except Exception as e:
            print(f"Error deleting: {e}")

    def create_card(self, recipe):
        # Extraemos la info nutricional (si existe)
        nutri_info = recipe.get('nutritional_info', '')
        
        # Creamos el componente visual para la info nutricional
        nutri_component = ft.Container()
        if nutri_info:
            nutri_component = ft.Container(
                bgcolor="#F0F4C3", # Un verde/amarillo muy suave
                padding=10,
                border_radius=8,
                border=ft.border.all(1, "#DCE775"),
                content=ft.Row([
                    ft.Icon("local_fire_department", size=16, color="orange"),
                    ft.Text(nutri_info, size=12, weight="bold", color="#33691E", expand=True)
                ], alignment=ft.MainAxisAlignment.START)
            )

        return ft.Container(
            bgcolor="white", padding=15, border_radius=10,
            border=ft.border.all(1, "#E0E0E0"),
            shadow=ft.BoxShadow(blur_radius=3, color="#EEEEEE"),
            content=ft.Column([
                # Cabecera con Título y Botón Borrar
                ft.Row([
                    ft.Text(recipe['title'], weight="bold", size=18, expand=True, color="black"),
                    ft.IconButton(
                        icon="delete_outline", 
                        icon_color="red", 
                        tooltip="Borrar receta",
                        on_click=lambda _, id=recipe['id']: self.delete_recipe(id)
                    )
                ]),
                
                # --- AQUÍ MOSTRAMOS LA INFO NUTRICIONAL ---
                nutri_component,
                # ------------------------------------------

                ft.Divider(height=10, color="transparent"),

                # Detalles expandibles
                ft.ExpansionTile(
                    title=ft.Text("Ver Ingredientes y Pasos", color="blue", size=14),
                    controls=[
                        ft.Container(
                            padding=10,
                            content=ft.Column([
                                ft.Text("🛒 Ingredientes:", weight="bold"),
                                ft.Markdown(recipe['ingredients']),
                                ft.Divider(),
                                ft.Text("🔥 Instrucciones:", weight="bold"),
                                ft.Markdown(recipe['instructions']),
                            ])
                        )
                    ]
                )
            ])
        )