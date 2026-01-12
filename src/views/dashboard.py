import flet as ft
from src.services.supabase_service import supabase_client
from datetime import datetime

class DashboardView(ft.Column):
    def __init__(self):
        super().__init__()
        self.expand = True
        self.scroll = ft.ScrollMode.AUTO
        
        self.stats_container = ft.Row(spacing=20, alignment=ft.MainAxisAlignment.CENTER)
        self.expiring_container = ft.Column(spacing=10)

        self.controls = [
            ft.Container(
                padding=20,
                content=ft.Column([
                    ft.Text("Resumen de Cocina", size=24, weight="bold"),
                    ft.Divider(height=20, color="transparent"),
                    self.stats_container,
                    ft.Divider(height=20, color="transparent"),
                    ft.Text("⚠️ Alertas de Caducidad", size=20, weight="bold"),
                    self.expiring_container
                ])
            )
        ]

    def did_mount(self):
        self.load_data()

    def load_data(self):
        try:
            res_inv = supabase_client.table("inventory").select("*", count="exact").eq("is_shopping_list", False).execute()
            count_inv = len(res_inv.data)
            res_shop = supabase_client.table("inventory").select("*", count="exact").eq("is_shopping_list", True).execute()
            count_shop = len(res_shop.data)

            self.stats_container.controls = [
                self._build_stat_card("Productos", str(count_inv), "blue", "kitchen"),
                self._build_stat_card("En Lista", str(count_shop), "orange", "shopping_cart")
            ]
            
            self.expiring_container.controls.clear()
            today = datetime.now().date()
            items_with_date = [i for i in res_inv.data if i.get('expiry_date')]
            
            alerts = []
            for item in items_with_date:
                try:
                    exp_date = datetime.strptime(item['expiry_date'], "%Y-%m-%d").date()
                    delta = (exp_date - today).days
                    if delta < 0: alerts.append((item, f"Venció hace {abs(delta)} días", "red", "warning"))
                    elif delta == 0: alerts.append((item, "¡Vence HOY!", "red", "priority_high"))
                    elif delta <= 3: alerts.append((item, f"Vence en {delta} días", "orange", "access_time"))
                    elif delta <= 7: alerts.append((item, f"Vence en {delta} días", "yellow", "calendar_today"))
                except: pass

            if not alerts:
                self.expiring_container.controls.append(ft.Container(bgcolor="white", padding=15, border_radius=10, content=ft.Row([ft.Icon("check_circle", color="green"), ft.Text("Todo fresco.")])))
            else:
                for item, msg, color, icon in alerts:
                    self._add_alert_card(item, msg, color, icon)
            
            self.update()
        except Exception as e:
            print(f"Error dashboard: {e}")

    def _add_alert_card(self, item, msg, color, icon):
        text_color = "black" if color == "yellow" else "white"
        btn = None
        if color == "red":
            btn = ft.ElevatedButton("Gestionar", bgcolor="white", color="red", height=30, on_click=lambda e: self.open_resolve_dialog(item))

        row = [ft.Icon(icon, color=text_color), ft.Text(f"{item['name']}: {msg}", color=text_color, weight="bold", expand=True)]
        if btn: row.append(btn)

        self.expiring_container.controls.append(
            ft.Container(bgcolor=color, padding=10, border_radius=8, content=ft.Row(row, alignment=ft.MainAxisAlignment.SPACE_BETWEEN))
        )

    def _build_stat_card(self, title, value, color, icon_name):
        return ft.Container(bgcolor=color, padding=20, border_radius=15, expand=True, content=ft.Column([ft.Icon(icon_name, color="white", size=30), ft.Text(value, size=40, weight="bold", color="white"), ft.Text(title, color="white", size=14)], horizontal_alignment=ft.CrossAxisAlignment.CENTER))

    # --- DIÁLOGO ON-THE-FLY ---
    def open_resolve_dialog(self, item):
        self.selected_item = item
        # Creamos diálogo aquí mismo
        dialog = ft.AlertDialog(
            title=ft.Text("⚠️ Producto Vencido"),
            content=ft.Text(f"¿Qué hacer con {item['name']}?"),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda e: self.close_dialog(dialog)),
                ft.TextButton("Tirar 🗑️", on_click=lambda e: self.execute_resolve(to_cart=False, dlg=dialog), style=ft.ButtonStyle(color="red")),
                ft.ElevatedButton("Comprar 🛒", on_click=lambda e: self.execute_resolve(to_cart=True, dlg=dialog), bgcolor="green", color="white"),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        self.page.open(dialog)

    def close_dialog(self, dlg):
        self.page.close(dlg)

    def execute_resolve(self, to_cart, dlg):
        if not self.selected_item: return
        try:
            if to_cart:
                supabase_client.table("inventory").update({"is_shopping_list": True, "location_id": None, "expiry_date": None}).eq("id", self.selected_item['id']).execute()
                msg = "Movido al Carrito"
            else:
                supabase_client.table("inventory").delete().eq("id", self.selected_item['id']).execute()
                msg = "Eliminado"
            self.page.snack_bar = ft.SnackBar(ft.Text(f"✅ {msg}"))
            self.page.snack_bar.open = True
        except Exception as e:
            print(f"Error: {e}")
        
        self.page.close(dlg)
        self.load_data()
        self.page.update()