import os
import flet as ft
from src.views.dashboard import DashboardView
from src.views.inventory_view import InventoryView
from src.views.shopping_view import ShoppingView
from src.views.chef_ui import ChefView
from src.views.favorites_view import FavoritesView
from src.views.lock_view import LockView

# IMPORTAMOS TU CONFIGURACIÓN
import src.changelog_config as changelog

def main(page: ft.Page):
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

    # --- INICIO CON PANTALLA DE BLOQUEO ---
    def start_app():
        page.clean()
        page.add(app_layout)
        navigate_to(0)
        check_changelog()

    # Mostrar la pantalla de bloqueo al arrancar
    page.add(LockView(on_unlock_success=start_app))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    ft.app(target=main, view=ft.AppView.WEB_BROWSER, port=port, host="0.0.0.0")