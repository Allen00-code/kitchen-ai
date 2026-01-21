import flet as ft
from src.views.dashboard import DashboardView
from src.views.inventory_view import InventoryView
from src.views.shopping_view import ShoppingView
from src.views.chef_ui import ChefView
from src.views.favorites_view import FavoritesView
from src.views.login_view import LoginView
from src.services.supabase_service import supabase_service # Importamos el servicio para hacer sign_out

# IMPORTAMOS TU CONFIGURACIÓN
import src.changelog_config as changelog

def main(page: ft.Page):
    page.title = "Kitchen AI"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 0
    page.bgcolor = "#F5F5F5"

    # Contenedor principal del cuerpo
    body_container = ft.Container(expand=True)

    # --- LÓGICA DEL CHANGELOG ---
    def check_changelog():
        last_seen = page.client_storage.get("last_seen_version")
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
        page.client_storage.set("last_seen_version", changelog.CURRENT_VERSION)

    # --- LÓGICA DE LOGOUT (NUEVO) ---
    def handle_logout():
        print("Cerrando sesión...")
        supabase_service.sign_out() # 1. Mata la sesión en Supabase
        page.clean()                # 2. Limpia la UI actual
        page.add(LoginView(on_login_success=start_app)) # 3. Muestra el Login de nuevo
        page.update()

    # --- NAVEGACIÓN ---
    def navigate_to(index):
        body_container.content = None
        
        if index == 0:
            # Pasamos la función de logout al Dashboard
            body_container.content = DashboardView(on_logout=handle_logout)
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

    # --- INICIO DE LA APP (Post-Login) ---
    def start_app():
        page.clean()
        page.add(app_layout)
        navigate_to(0)
        check_changelog()

    # Iniciar con Pantalla de Login
    page.add(LoginView(on_login_success=start_app))

if __name__ == "__main__":
    ft.app(target=main)