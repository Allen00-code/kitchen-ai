import flet as ft
from src.views.dashboard import DashboardView
from src.views.inventory_view import InventoryView
from src.views.shopping_view import ShoppingView
from src.views.chef_ui import ChefView
from src.views.favorites_view import FavoritesView
from src.views.login_view import LoginView

# IMPORTAMOS TU CONFIGURACIÓN
import src.changelog_config as changelog

def main(page: ft.Page):
    page.title = "Kitchen AI"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 0
    page.bgcolor = "#F5F5F5"

    # Contenedor principal del cuerpo
    body_container = ft.Container(expand=True)

    # --- LÓGICA DEL CHANGELOG (NOVEDADES) ---
    def check_changelog():
        # 1. Preguntamos al dispositivo: "¿Qué versión viste la última vez?"
        last_seen = page.client_storage.get("last_seen_version")
        
        # 2. Si la versión del dispositivo es diferente a la actual...
        if last_seen != changelog.CURRENT_VERSION:
            show_changelog_dialog()

    def show_changelog_dialog():
        # Construimos la lista de puntos visualmente
        points_ui = []
        for point in changelog.CHANGELOG_POINTS:
            points_ui.append(
                ft.Row([
                    ft.Icon("check_circle", color="green", size=16),
                    ft.Text(point, size=14, expand=True)
                ], alignment=ft.MainAxisAlignment.START, vertical_alignment=ft.CrossAxisAlignment.START)
            )

        # Creamos el diálogo
        dlg = ft.AlertDialog(
            title=ft.Text(changelog.CHANGELOG_TITLE, weight="bold"),
            content=ft.Container(
                content=ft.Column(
                    [
                        ft.Text(f"Versión: {changelog.CURRENT_VERSION}", italic=True, color="grey"),
                        ft.Divider(),
                        *points_ui # Desempaquetamos los puntos aquí
                    ], 
                    scroll=ft.ScrollMode.AUTO,
                    height=200 # Altura máxima para que no tape todo en móviles pequeños
                ),
                width=300
            ),
            actions=[
                ft.ElevatedButton(
                    "¡Genial! 😎", 
                    on_click=lambda e: close_changelog(dlg),
                    bgcolor="blue", color="white"
                )
            ],
            modal=True # Obliga a cerrar el diálogo
        )
        page.open(dlg)

    def close_changelog(dlg):
        page.close(dlg)
        # 3. Guardamos la "marca" en el dispositivo para que no vuelva a salir
        page.client_storage.set("last_seen_version", changelog.CURRENT_VERSION)


    # --- NAVEGACIÓN (Igual que antes) ---
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

    # --- INICIO ---
    def start_app():
        page.clean()
        page.add(app_layout)
        navigate_to(0)
        # 4. LANZAMOS LA VERIFICACIÓN AL ENTRAR
        check_changelog()

    # Iniciar con Pantalla de Login
    page.add(LoginView(on_login_success=start_app))

if __name__ == "__main__":
    ft.app(target=main)