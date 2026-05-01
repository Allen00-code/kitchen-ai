import flet as ft
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Carga el .env por si acaso no se cargó globalmente antes
load_dotenv()

MAX_ATTEMPTS = 5
LOCKOUT_MINUTES = 10


class LockView(ft.Container):
    def __init__(self, on_unlock_success):
        # Guardamos el callback ANTES del super() para poder referenciarlo
        # en los handlers que se pasan como on_submit / on_click
        self.on_unlock_success = on_unlock_success

        # --- Rate Limiter ---
        self.failed_attempts = 0
        self.lockout_until = None

        # --- Elementos de UI (construidos ANTES del super para poder
        #     incluirlos en el content que se pasa al constructor padre) ---
        self.pass_input = ft.TextField(
            label="Contraseña de acceso",
            password=True,
            can_reveal_password=True,
            width=300,
            prefix_icon="lock",
            on_submit=self.handle_unlock,  # También funciona con Enter
        )
        self.error_text = ft.Text("", color="red", size=12)

        self.btn_enter = ft.ElevatedButton(
            "Entrar",
            on_click=self.handle_unlock,
            bgcolor="orange",
            color="white",
            width=300,
        )

        _content = ft.Column(
            [
                ft.Icon("soup_kitchen", size=80, color="orange"),
                ft.Text("Kitchen AI", size=32, weight="bold"),
                ft.Text("Ingresa tu contraseña para continuar", color="grey", size=13),
                ft.Container(height=24),
                self.pass_input,
                ft.Container(height=12),
                self.btn_enter,
                ft.Container(height=8),
                self.error_text,
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            alignment=ft.MainAxisAlignment.CENTER,
        )

        # ✅ FIX FLET 0.84 WEB: todas las props se pasan al padre en __init__
        # para que el motor Flutter/web las fije correctamente desde el inicio.
        super().__init__(
            content=_content,
            expand=True,
            bgcolor="#F5F5F5",
            alignment=ft.Alignment(0.0, 0.0),
        )

    def handle_unlock(self, e):
        # --- 1. Verificar si está en periodo de bloqueo ---
        if self.lockout_until is not None:
            remaining = self.lockout_until - datetime.now()
            if remaining.total_seconds() > 0:
                total_secs = int(remaining.total_seconds())
                mins = total_secs // 60
                secs = total_secs % 60
                if mins > 0:
                    tiempo = f"{mins} min {secs} seg"
                else:
                    tiempo = f"{secs} seg"
                self.error_text.value = f"Demasiados intentos. Bloqueado por {tiempo}."
                self.pass_input.value = ""
                self.update()
                return
            else:
                # El bloqueo ya expiró → reiniciar contadores
                self.failed_attempts = 0
                self.lockout_until = None

        # --- 2. Validar contraseña ---
        entered = self.pass_input.value or ""
        app_password = os.getenv("APP_PASSWORD", "")

        if entered == app_password:
            # Contraseña correcta
            self.error_text.value = ""
            self.update()
            self.on_unlock_success()
        else:
            # Contraseña incorrecta
            self.failed_attempts += 1
            self.pass_input.value = ""

            if self.failed_attempts >= MAX_ATTEMPTS:
                self.lockout_until = datetime.now() + timedelta(minutes=LOCKOUT_MINUTES)
                self.error_text.value = f"Acceso bloqueado por {LOCKOUT_MINUTES} minutos."
            else:
                restantes = MAX_ATTEMPTS - self.failed_attempts
                self.error_text.value = f"Contraseña incorrecta. Intentos restantes: {restantes}."

            self.update()
