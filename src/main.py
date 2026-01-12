import flet as ft
import os
import threading
import time
from src.views.dashboard import DashboardView
from src.views.inventory_view import InventoryView
from src.views.chef_ui import ChefView
from src.views.shopping_view import ShoppingView
from src.views.login_view import LoginView

def main(page: ft.Page):
    # --- Configuración Inicial ---
    page.title = "KitchenAI 🤖"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 0
    page.window.width = 400
    page.window.height = 750
    page.window.resizable = True 
    
    upload_dir = os.path.join(os.getcwd(), "assets", "uploads")
    os.makedirs(upload_dir, exist_ok=True)

    # --- VARIABLES DE SESIÓN ---
    session_data = {
        "last_interaction": time.time(),
        "is_logged_in": False
    }
    
    SESSION_TIMEOUT_SECONDS = 20 * 60  # 20 Minutos

    # --- FUNCIÓN PARA REGISTRAR ACTIVIDAD ---
    def register_activity(e=None):
        session_data["last_interaction"] = time.time()

    # --- LÓGICA DE LOGOUT MANUAL ---
    def logout_click(e):
        print("👋 Cerrando sesión manualmente...")
        show_login()

    # --- MONITOR DE INACTIVIDAD (Daemon Thread) ---
    def session_check_loop():
        while True:
            time.sleep(5)
            if session_data["is_logged_in"]:
                elapsed = time.time() - session_data["last_interaction"]
                if elapsed > SESSION_TIMEOUT_SECONDS:
                    print("⚠️ Tiempo agotado. Cerrando sesión por inactividad...")
                    session_data["is_logged_in"] = False
                    break

    # --- NAVEGACIÓN ---
    def change_tab(e):
        register_activity()
        
        if not session_data["is_logged_in"]:
            show_login()
            return

        index = e.control.selected_index
        page.floating_action_button = None
        body_container.content = None 
        
        if index == 0: body_container.content = DashboardView()
        elif index == 1: body_container.content = InventoryView()
        elif index == 2: body_container.content = ShoppingView()
        elif index == 3: body_container.content = ChefView()
        
        body_container.update()
        page.update()

    nav_bar = ft.NavigationBar(
        selected_index=0,
        visible=False,
        on_change=change_tab,
        destinations=[
            ft.NavigationBarDestination(icon="dashboard", label="Inicio"),
            ft.NavigationBarDestination(icon="inventory", label="Inventario"),
            ft.NavigationBarDestination(icon="shopping_cart", label="Compras"),
            ft.NavigationBarDestination(icon="restaurant", label="Chef AI"),
        ]
    )
    
    # Barra Superior con Botón de Logout
    # CORRECCIÓN: Usamos strings ("blue", "white", "kitchen") para evitar errores de versión
    app_bar = ft.AppBar(
        leading=ft.Icon("kitchen"), 
        leading_width=40,
        title=ft.Text("KitchenAI", weight="bold"),
        center_title=False,
        bgcolor="blue",     # <--- String simple
        color="white",      # <--- String simple
        actions=[
            ft.IconButton("logout", tooltip="Cerrar Sesión", on_click=logout_click, icon_color="white")
        ]
    )

    body_container = ft.Container(expand=True)

    # --- CONTROL DE VISTAS ---
    def show_login():
        session_data["is_logged_in"] = False
        nav_bar.visible = False
        page.appbar = None 
        page.floating_action_button = None
        
        login_screen = LoginView(on_login_success=unlock_app)
        
        page.clean()
        page.add(ft.Container(expand=True, content=login_screen, bgcolor="#F5F5F5"))
        page.update()

    def unlock_app():
        session_data["is_logged_in"] = True
        session_data["last_interaction"] = time.time()
        
        page.clean()
        
        page.appbar = app_bar 
        page.navigation_bar = nav_bar
        nav_bar.visible = True
        
        body_container.content = DashboardView()
        page.add(body_container)
        
        # Monitor de sesión
        monitor_thread = threading.Thread(target=session_check_loop, daemon=True)
        monitor_thread.start()
        
        page.update()

    # Arrancamos
    show_login()

if __name__ == "__main__":
    ft.app(target=main)