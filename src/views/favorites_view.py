import flet as ft
from src.services.supabase_service import supabase_client


class FavoritesView(ft.Column):
    def __init__(self):
        super().__init__()
        self.expand = True
        self.spacing = 0

        # ── Contenedores de cada pestaña (con scroll propio) ──────────────────
        self.individual_recipes_container = ft.Column(
            spacing=15,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
            visible=True,
        )
        self.weekly_recipes_container = ft.Column(
            spacing=15,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
            visible=False,
        )

        # ── Botones de pestaña manual ──────────────────────────────────────────
        self.btn_individual = ft.ElevatedButton(
            text="Platos Individuales 🍳",
            on_click=self._show_individual,
            style=ft.ButtonStyle(
                bgcolor={"": "#1565C0"},
                color={"": "white"},
                shape={"": ft.RoundedRectangleBorder(radius=8)},
            ),
        )
        self.btn_weekly = ft.ElevatedButton(
            text="Planes Semanales 🥊",
            on_click=self._show_weekly,
            style=ft.ButtonStyle(
                bgcolor={"": "#424242"},
                color={"": "#BDBDBD"},
                shape={"": ft.RoundedRectangleBorder(radius=8)},
            ),
        )

        # ── Layout principal ───────────────────────────────────────────────────
        self.controls = [
            ft.Container(
                padding=ft.padding.only(left=20, right=20, top=20, bottom=8),
                content=ft.Row(
                    [ft.Text("Mis Recetas Guardadas 📖", size=24, weight="bold")],
                    alignment=ft.MainAxisAlignment.START,
                ),
            ),
            ft.Divider(height=1),
            # Barra de pestañas manual
            ft.Container(
                padding=ft.padding.only(left=16, right=16, top=12, bottom=4),
                content=ft.Row(
                    [self.btn_individual, self.btn_weekly],
                    spacing=10,
                ),
            ),
            ft.Divider(height=1, color="transparent"),
            # Contenido de las pestañas
            ft.Container(
                expand=True,
                padding=ft.padding.only(left=12, right=12, top=8, bottom=12),
                content=ft.Column(
                    [
                        self.individual_recipes_container,
                        self.weekly_recipes_container,
                    ],
                    expand=True,
                    spacing=0,
                ),
            ),
        ]

    # ── Alternancia de pestañas ────────────────────────────────────────────────
    def _show_individual(self, e=None):
        self.individual_recipes_container.visible = True
        self.weekly_recipes_container.visible = False
        # Botón activo
        self.btn_individual.style = ft.ButtonStyle(
            bgcolor={"": "#1565C0"},
            color={"": "white"},
            shape={"": ft.RoundedRectangleBorder(radius=8)},
        )
        # Botón inactivo
        self.btn_weekly.style = ft.ButtonStyle(
            bgcolor={"": "#424242"},
            color={"": "#BDBDBD"},
            shape={"": ft.RoundedRectangleBorder(radius=8)},
        )
        self.update()

    def _show_weekly(self, e=None):
        self.individual_recipes_container.visible = False
        self.weekly_recipes_container.visible = True
        # Botón activo
        self.btn_weekly.style = ft.ButtonStyle(
            bgcolor={"": "#E65100"},
            color={"": "white"},
            shape={"": ft.RoundedRectangleBorder(radius=8)},
        )
        # Botón inactivo
        self.btn_individual.style = ft.ButtonStyle(
            bgcolor={"": "#424242"},
            color={"": "#BDBDBD"},
            shape={"": ft.RoundedRectangleBorder(radius=8)},
        )
        self.update()

    # ── Ciclo de vida ─────────────────────────────────────────────────────────
    def did_mount(self):
        if self.page:
            self.load_recipes()

    # ── Carga y filtrado ──────────────────────────────────────────────────────
    def load_recipes(self):
        self.individual_recipes_container.controls.clear()
        self.weekly_recipes_container.controls.clear()

        try:
            res = (
                supabase_client
                .table("saved_recipes")
                .select("*")
                .order("created_at", desc=True)
                .execute()
            )

            if not res.data:
                self.individual_recipes_container.controls.append(self._empty_state())
                self.weekly_recipes_container.controls.append(self._empty_state())
            else:
                for recipe in res.data:
                    card = self.create_card(recipe)
                    if recipe.get("is_weekly_plan"):
                        self.weekly_recipes_container.controls.append(card)
                    else:
                        self.individual_recipes_container.controls.append(card)

                # Estado vacío por pestaña si no hay recetas en esa categoría
                if not self.individual_recipes_container.controls:
                    self.individual_recipes_container.controls.append(
                        self._empty_state("No tienes platos individuales guardados aún.")
                    )
                if not self.weekly_recipes_container.controls:
                    self.weekly_recipes_container.controls.append(
                        self._empty_state("No tienes planes semanales guardados aún.")
                    )

            self.update()

        except Exception as e:
            print(f"Error loading favorites: {e}")

    # ── Estado vacío reutilizable ─────────────────────────────────────────────
    def _empty_state(self, message="No tienes recetas guardadas aún."):
        return ft.Container(
            content=ft.Column(
                [
                    ft.Icon("no_meals", size=50, color="grey"),
                    ft.Text(message, color="grey", text_align=ft.TextAlign.CENTER),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            alignment=ft.alignment.center,
            padding=40,
        )

    # ── Borrar receta ─────────────────────────────────────────────────────────
    def delete_recipe(self, r_id):
        try:
            supabase_client.table("saved_recipes").delete().eq("id", r_id).execute()
            self.page.snack_bar = ft.SnackBar(ft.Text("🗑️ Receta eliminada"))
            self.page.snack_bar.open = True
            self.page.update()
            self.load_recipes()
        except Exception as e:
            print(f"Error deleting: {e}")

    # ── Tarjeta de receta ─────────────────────────────────────────────────────
    def create_card(self, recipe):
        nutri_info = recipe.get("nutritional_info", "")
        is_weekly = recipe.get("is_weekly_plan", False)

        # Badge de tipo de receta
        badge = ft.Container(
            padding=ft.padding.symmetric(horizontal=8, vertical=3),
            border_radius=20,
            bgcolor="#FFF3E0" if is_weekly else "#E3F2FD",
            border=ft.border.all(1, "#FFB74D" if is_weekly else "#90CAF9"),
            content=ft.Text(
                "🥊 Plan Semanal" if is_weekly else "🍳 Plato Individual",
                size=11,
                color="#E65100" if is_weekly else "#1565C0",
                weight="bold",
            ),
        )

        # Bloque nutricional
        nutri_component = ft.Container()
        if nutri_info:
            nutri_component = ft.Container(
                bgcolor="#F0F4C3",
                padding=10,
                border_radius=8,
                border=ft.border.all(1, "#DCE775"),
                content=ft.Row(
                    [
                        ft.Icon("local_fire_department", size=16, color="orange"),
                        ft.Text(
                            nutri_info,
                            size=12,
                            weight="bold",
                            color="#33691E",
                            expand=True,
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.START,
                ),
            )

        return ft.Container(
            bgcolor="white",
            padding=15,
            border_radius=12,
            border=ft.border.all(1, "#E0E0E0"),
            shadow=ft.BoxShadow(blur_radius=4, color="#DDDDDD"),
            content=ft.Column(
                [
                    # Cabecera: título + badge + botón borrar
                    ft.Row(
                        [
                            ft.Column(
                                [
                                    ft.Text(
                                        recipe.get("title", "Sin nombre"),
                                        weight="bold",
                                        size=18,
                                        color="black",
                                    ),
                                    badge,
                                ],
                                spacing=4,
                                expand=True,
                            ),
                            ft.IconButton(
                                icon="delete_outline",
                                icon_color="red",
                                tooltip="Borrar receta",
                                on_click=lambda _, rid=recipe["id"]: self.delete_recipe(rid),
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        vertical_alignment=ft.CrossAxisAlignment.START,
                    ),
                    nutri_component,
                    ft.Divider(height=8, color="transparent"),
                    # Detalles expandibles
                    ft.ExpansionTile(
                        title=ft.Text("Ver Ingredientes y Pasos", color="blue", size=14),
                        controls=[
                            ft.Container(
                                padding=10,
                                content=ft.Column(
                                    [
                                        ft.Text("🛒 Ingredientes:", weight="bold"),
                                        ft.Markdown(recipe.get("ingredients", "")),
                                        ft.Divider(),
                                        ft.Text("🔥 Instrucciones:", weight="bold"),
                                        ft.Markdown(recipe.get("instructions", "")),
                                    ]
                                ),
                            )
                        ],
                    ),
                ],
                spacing=6,
            ),
        )