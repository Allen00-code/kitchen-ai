import flet as ft
from src.services.supabase_service import supabase_service
import time

class LoginView(ft.Container):
    def __init__(self, on_login_success):
        self.on_login_success = on_login_success

        # --- Elementos de UI (construidos ANTES del super para poder
        #     incluirlos en el content que se pasa al constructor padre) ---
        self.email_input = ft.TextField(label="Correo Electrónico", width=300, prefix_icon="email")
        self.pass_input = ft.TextField(label="Contraseña", password=True, can_reveal_password=True, width=300, prefix_icon="lock")
        self.status_text = ft.Text("", color="red", size=12)

        # Botones
        self.btn_login = ft.ElevatedButton("Iniciar Sesión", on_click=self.handle_login, bgcolor="blue", color="white", width=300)
        self.btn_signup = ft.OutlinedButton("Crear Cuenta Nueva", on_click=self.handle_signup, width=300)

        _content = ft.Column([
            # CAMBIO DE ICONO: De 'security' a 'soup_kitchen'
            ft.Icon("soup_kitchen", size=80, color="orange"),
            ft.Text("Kitchen AI", size=30, weight="bold"),
            ft.Text("Tu asistente de cocina personal", color="grey"),
            ft.Container(height=20),
            self.email_input,
            self.pass_input,
            ft.Container(height=10),
            self.btn_login,
            ft.Container(height=5),
            ft.Text("¿Primera vez aquí?", size=12),
            self.btn_signup,
            ft.Container(height=10),
            self.status_text
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, alignment=ft.MainAxisAlignment.CENTER)

        # ✅ FIX FLET 0.84 WEB: todas las props se pasan al padre en __init__
        super().__init__(
            content=_content,
            expand=True,
            bgcolor="#F5F5F5",
            alignment=ft.Alignment(0.0, 0.0),
        )

    def handle_login(self, e):
        if not self.email_input.value or not self.pass_input.value:
            self.status_text.value = "Por favor llena todos los campos"
            self.update()
            return

        self.status_text.value = "Conectando..."
        self.status_text.color = "blue"
        self.update()

        try:
            # Intentamos Login en Supabase
            supabase_service.sign_in(self.email_input.value, self.pass_input.value)

            self.status_text.value = "✅ ¡Bienvenido!"
            self.status_text.color = "green"
            self.update()
            time.sleep(0.5)
            self.on_login_success() # Pasamos al Dashboard

        except Exception as ex:
            self.status_text.value = f"Error: Credenciales inválidas o error de red."
            self.status_text.color = "red"
            print(f"Login Error: {ex}")
            self.update()

    def handle_signup(self, e):
        if not self.email_input.value or not self.pass_input.value:
            self.status_text.value = "Ingresa un correo y contraseña para registrarte"
            self.update()
            return

        self.status_text.value = "Creando cuenta..."
        self.status_text.color = "orange"
        self.update()

        try:
            supabase_service.sign_up(self.email_input.value, self.pass_input.value)
            self.status_text.value = "✅ Cuenta creada. ¡Ahora inicia sesión!"
            self.status_text.color = "green"
        except Exception as ex:
            self.status_text.value = f"Error al registrar: {ex}"
            self.status_text.color = "red"
        self.update()