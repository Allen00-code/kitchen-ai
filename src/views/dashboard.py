import flet as ft
from src.services.supabase_service import supabase_client
from datetime import datetime, timedelta

class DashboardView(ft.Column):
    def __init__(self):
        # --- HEADER (Saludo estático) ---
        self.header = ft.Container(
            padding=20,
            bgcolor="white",
            border_radius=15,
            shadow=ft.BoxShadow(blur_radius=5, color="#E0E0E0"),
            content=ft.Column([
                ft.Text("¡Hola Chef! 👋", size=24, weight="bold", color="blue"),
                ft.Text("Aquí tienes el resumen de tu cocina", size=14, color="grey")
            ])
        )

        # --- SECCIONES DE DATOS (Se llenan al cargar) ---
        self.stats_container = ft.Container()
        self.expiring_container = ft.Container()

        # ✅ FIX FLET 0.84 WEB: controls, expand y scroll se pasan al padre
        # en __init__ para que el motor Flutter/web los fije desde el inicio.
        super().__init__(
            controls=[
                self.header,
                ft.Container(height=20),
                self.stats_container,
                ft.Container(height=20),
                ft.Text("⚠️ Atención Requerida (Caducan pronto)", weight="bold", size=16),
                self.expiring_container
            ],
            expand=True,
            scroll=ft.ScrollMode.AUTO,
        )

    def did_mount(self):
        # Cargamos los datos cada vez que entramos a la pantalla
        self.load_dashboard_data()

    def load_dashboard_data(self):
        try:
            # Traemos TODO el inventario (no shopping list)
            res = supabase_client.table("inventory").select("*").eq("is_shopping_list", False).execute()
            items = res.data

            # 1. Conteo Total
            total_items = len(items)

            # 2. Lógica de Caducidad (Próximos 7 días)
            expiring_soon = []
            today = datetime.now().date()
            warning_limit = today + timedelta(days=7)

            for item in items:
                expiry_str = item.get('expiry_date')
                if expiry_str:
                    try:
                        exp_date = datetime.strptime(expiry_str, "%Y-%m-%d").date()
                        # Si ya venció O vence en la próxima semana
                        if exp_date <= warning_limit:
                            days_left = (exp_date - today).days
                            item['days_left'] = days_left
                            expiring_soon.append(item)
                    except: pass # Si la fecha está mal formato, la ignoramos

            # Ordenar: Los que vencen primero van arriba
            expiring_soon.sort(key=lambda x: x['days_left'])

            # --- RENDERIZAR STATS ---
            self.stats_container.content = ft.Row([
                self._build_stat_card("Productos", str(total_items), "kitchen", "blue"),
                self._build_stat_card("Por Caducar", str(len(expiring_soon)), "warning", "orange"),
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)

            # --- RENDERIZAR LISTA DE CADUCIDAD ---
            if not expiring_soon:
                self.expiring_container.content = ft.Container(
                    padding=20, bgcolor="white", border_radius=10,
                    content=ft.Row([
                        ft.Icon("check_circle", color="green"),
                        ft.Text("¡Todo fresco! Nada caduca pronto.", color="green")
                    ], alignment=ft.MainAxisAlignment.CENTER)
                )
            else:
                expiry_list = ft.Column(spacing=10)
                for item in expiring_soon:
                    days = item['days_left']
                    if days < 0:
                        msg = f"Venció hace {abs(days)} días"
                        color = "red"
                    elif days == 0:
                        msg = "¡Vence HOY!"
                        color = "red"
                    else:
                        msg = f"Vence en {days} días"
                        color = "orange"

                    expiry_list.controls.append(
                        ft.Container(
                            bgcolor="white", padding=10, border_radius=10, border=ft.border.all(1, "#EEEEEE"),
                            content=ft.Row([
                                ft.Icon("warning_amber", color=color),
                                ft.Column([
                                    ft.Text(item['name'], weight="bold"),
                                    ft.Text(f"{item['quantity']} {item['unit']}", size=12, color="grey")
                                ], expand=True),
                                ft.Container(
                                    bgcolor=ft.colors.with_opacity(0.1, color), padding=5, border_radius=5,
                                    content=ft.Text(msg, color=color, size=12, weight="bold")
                                )
                            ])
                        )
                    )
                self.expiring_container.content = expiry_list

            self.update()

        except Exception as e:
            print(f"Error dashboard: {e}")

    def _build_stat_card(self, title, value, icon, color):
        return ft.Container(
            expand=True,
            bgcolor="white",
            padding=20,
            border_radius=15,
            shadow=ft.BoxShadow(blur_radius=5, color="#F0F0F0"),
            content=ft.Column([
                ft.Icon(icon, color=color, size=30),
                ft.Text(value, size=24, weight="bold"),
                ft.Text(title, size=14, color="grey")
            ])
        )
