import os
import flet as ft
from src.views.dashboard import DashboardView
from src.views.inventory_view import InventoryView
from src.views.shopping_view import ShoppingView
from src.views.chef_ui import ChefView
from src.views.favorites_view import FavoritesView

# IMPORTAMOS TU CONFIGURACIÓN
import src.changelog_config as changelog

def main(page: ft.Page):
    print(">>> [DEBUG] Iniciando función main...")
    page.title = "Kitchen AI"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 0
    page.bgcolor = "#F5F5F5"
    # ✅ FIX FLET 0.84 WEB: sin estos dos ajustes, el Column raíz no se
    # estira al 100% del viewport del navegador y produce pantalla gris.
    page.vertical_alignment = ft.MainAxisAlignment.START
    page.horizontal_alignment = ft.CrossAxisAlignment.STRETCH

    # Contenedor principal del cuerpo (expand=True para ocupar todo el espacio)
    body_container = ft.Container(expand=True)

    # --- LÓGICA DEL CHANGELOG ---
    def check_changelog():
        # Flet 0.84 eliminó 'client_storage' sincrónico. 
        # Usamos 'session' que es seguro, vive en memoria y no crashea en web.
        last_seen = page.session.get("last_seen_version")
        if last_seen != changelog.CURRENT_VERSION:
            show_changelog_dialog()

    def show_changelog_dialog():
        points_ui = []
        for point in changelog.CHANGELOG_POINTS:
            points_ui.append(
                ft.Row([
                    ft.Icon("check_circle", color="green", size=16),
                    ft.Text(point, size=14, expand=True)
                ], alignment=ft.MainAxisAlignment.START, vertical_alignment=ft.CrossAxisAlignment.START)
            )

        dlg = ft.AlertDialog(
            title=ft.Text(changelog.CHANGELOG_TITLE, weight="bold"),
            content=ft.Container(
                content=ft.Column(
                    [
                        ft.Text(f"Versión: {changelog.CURRENT_VERSION}", italic=True, color="grey"),
                        ft.Divider(),
                        *points_ui
                    ],
                    scroll=ft.ScrollMode.AUTO,
                    height=200
                ),
                width=300
            ),
            actions=[
                ft.ElevatedButton("¡Genial! 😎", on_click=lambda e: close_changelog(dlg), bgcolor="blue", color="white")
            ],
            modal=True
        )
        page.open(dlg)

    def close_changelog(dlg):
        page.close(dlg)
        page.session.set("last_seen_version", changelog.CURRENT_VERSION)

    # --- NAVEGACIÓN ---
    def navigate_to(index):
        body_container.content = None

        if index == 0:
            body_container.content = DashboardView()
        elif index == 1:
            body_container.content = InventoryView()
        elif index == 2:
            body_container.content = ShoppingView()
        elif index == 3:
            body_container.content = ChefView(page_nav_callback=change_tab_programmatically)
        elif index == 4:
            body_container.content = FavoritesView()

        body_container.update()

    def change_tab_programmatically(route_name):
        rutas = ["dashboard", "inventory", "shopping", "chef", "favorites"]
        if route_name in rutas:
            idx = rutas.index(route_name)
            nav_bar.selected_index = idx
            nav_bar.update()
            navigate_to(idx)

    nav_bar = ft.NavigationBar(
        selected_index=0,
        label_behavior=ft.NavigationBarLabelBehavior.ALWAYS_SHOW,
        destinations=[
            ft.NavigationBarDestination(icon="dashboard", label="Inicio"),
            ft.NavigationBarDestination(icon="kitchen", label="Stock"),
            ft.NavigationBarDestination(icon="shopping_cart", label="Lista"),
            ft.NavigationBarDestination(icon="restaurant", label="Chef"),
            ft.NavigationBarDestination(icon="menu_book", label="Recetas"),
        ],
        on_change=lambda e: navigate_to(e.control.selected_index)
    )

    app_layout = ft.Column([
        body_container,
        nav_bar
    ], expand=True, spacing=0)

    # --- PANTALLA DE BLOQUEO NATIVA ---
    # Centramos la página temporalmente para el login
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.vertical_alignment = ft.MainAxisAlignment.CENTER

    def try_login(e):
        if pass_input.value == os.getenv("APP_PASSWORD", ""):
            # Limpiamos la pantalla y restauramos la alineación para la app
            page.clean()
            page.horizontal_alignment = ft.CrossAxisAlignment.START
            page.vertical_alignment = ft.MainAxisAlignment.START
            page.bgcolor = "white"
            page.add(app_layout)
            navigate_to(0)
            check_changelog()
        else:
            error_text.value = "Contraseña incorrecta"
            pass_input.value = ""
            page.update()

    pass_input = ft.TextField(
        label="Contraseña de acceso",
        password=True,
        can_reveal_password=True,
        width=300,
        prefix_icon="lock",
        on_submit=try_login
    )
    error_text = ft.Text("", color="red")

    login_view = ft.Column(
        [
            ft.Icon("soup_kitchen", size=80, color="orange"),
            ft.Text("Kitchen AI", size=32, weight="bold"),
            ft.Text("Acceso Privado", color="grey"),
            ft.Container(height=20),
            pass_input,
            ft.ElevatedButton("Entrar", on_click=try_login, bgcolor="orange", color="white", width=300),
            error_text
        ],
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        alignment=ft.MainAxisAlignment.CENTER,
    )

    print(">>> [DEBUG] Intentando renderizar la pantalla inicial...")
    page.add(login_view)
    page.update()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    ft.app(
        target=main,
        view=ft.AppView.WEB_BROWSER,
        port=port,
        host="0.0.0.0"
    )