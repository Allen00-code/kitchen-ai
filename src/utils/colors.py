import flet as ft

# Paleta de Colores KitchenAI
PRIMARY = "#2E7D32"      # Verde Bosque (Sage)
SECONDARY = "#FF7043"    # Naranja Quemado
BACKGROUND = "#F5F5F7"   # Blanco Humo
SURFACE = "#FFFFFF"      # Blanco Puro
TEXT_PRIMARY = "#212121" # Gris Oscuro
TEXT_SECONDARY = "#757575" # Gris Medio
ERROR = "#D32F2F"        # Rojo Alerta

def get_theme():
    # Definimos el esquema de colores
    color_scheme = ft.ColorScheme(
        primary=PRIMARY,
        secondary=SECONDARY,
        surface=SURFACE,
        error=ERROR,
        # Nota: 'background' se maneja en page.bgcolor, no aquí
    )
    
    return ft.Theme(
        color_scheme=color_scheme,
        use_material3=True,
        # Eliminamos visual_density para evitar conflictos de versiones
    )