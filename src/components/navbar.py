import flet as ft

def KitchenNavBar(on_change_function):
    return ft.NavigationBar(
        bgcolor="white",
        selected_index=0,
        on_change=on_change_function,
        destinations=[
            # CAMBIO FINAL: Usamos TEXTO ("string") en lugar de objetos.
            # Esto es inmortal y funciona en cualquier versión.
            ft.NavigationBarDestination(icon="home", label="Inicio"),
            ft.NavigationBarDestination(icon="list", label="Inventario"),
            ft.NavigationBarDestination(icon="star", label="Chef AI"),
            ft.NavigationBarDestination(icon="shopping_cart", label="Compras"),
        ]
    )