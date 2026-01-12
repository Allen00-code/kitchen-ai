import flet as ft
import time
import random

class LoginView(ft.Column):
    def __init__(self, on_login_success):
        super().__init__()
        self.on_login_success = on_login_success
        self.expand = True
        self.alignment = ft.MainAxisAlignment.CENTER
        self.horizontal_alignment = ft.CrossAxisAlignment.CENTER
        
        # --- CONFIGURACIÓN DE SEGURIDAD ---
        self.CORRECT_PASSWORD = "Chef2025"  # <--- TU CONTRASEÑA
        self.MAX_ATTEMPTS = 5
        self.LOCKOUT_DURATION = 300  # 300 segundos = 5 minutos
        
        self.attempts = 0
        self.lockout_time = None # Momento en que se bloqueó
        
        # --- CAPTCHA MATEMÁTICO ---
        self.num1 = random.randint(1, 10)
        self.num2 = random.randint(1, 10)
        self.captcha_answer = self.num1 + self.num2

        # --- UI ---
        self.logo = ft.Icon(name="lock_outline", size=80, color="blue")
        self.title = ft.Text("KitchenAI", size=24, weight="bold")
        self.subtitle = ft.Text("Verificación de Seguridad", color="grey")
        
        self.pass_input = ft.TextField(
            label="Contraseña", password=True, can_reveal_password=True, 
            text_align="center", width=280
        )
        
        # Campo del Captcha
        self.captcha_input = ft.TextField(
            label=f"¿Cuánto es {self.num1} + {self.num2}?", 
            text_align="center", width=280, 
            keyboard_type="number",
            hint_text="Resuelve la suma (Anti-Bots)"
        )
        
        self.login_btn = ft.ElevatedButton(
            "Entrar", bgcolor="blue", color="white", width=280, height=45,
            on_click=self.check_login
        )
        
        self.status_text = ft.Text("", color="red", size=12, text_align="center")

        self.controls = [
            ft.Container(
                content=ft.Column([
                    self.logo, self.title, self.subtitle,
                    ft.Divider(height=20, color="transparent"),
                    self.pass_input,
                    ft.Container(height=10),
                    self.captcha_input, # Agregamos el captcha visualmente
                    ft.Container(height=20),
                    self.login_btn,
                    ft.Container(height=10),
                    self.status_text
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                padding=40, border_radius=20, bgcolor="white",
                shadow=ft.BoxShadow(blur_radius=10, color="grey")
            )
        ]

    def check_login(self, e):
        # 1. VERIFICAR SI ESTÁ BLOQUEADO TEMPORALMENTE
        if self.lockout_time:
            elapsed = time.time() - self.lockout_time
            if elapsed < self.LOCKOUT_DURATION:
                remaining = int(self.LOCKOUT_DURATION - elapsed)
                minutes = remaining // 60
                seconds = remaining % 60
                self.status_text.value = f"⏳ Sistema en enfriamiento.\nIntenta en {minutes}m {seconds}s."
                self.status_text.color = "orange"
                self.update()
                return
            else:
                # El tiempo pasó, reseteamos todo
                self.reset_lockout()

        # 2. VERIFICAR CAPTCHA
        if self.captcha_input.value != str(self.captcha_answer):
            self.status_text.value = "🤖 Error en la suma. ¿Eres un robot?"
            self.regenerate_captcha() # Cambiamos la suma para evitar spam
            self.update()
            return

        # 3. VERIFICAR CONTRASEÑA
        if self.pass_input.value == self.CORRECT_PASSWORD:
            self.status_text.value = "✅ Acceso Correcto"
            self.status_text.color = "green"
            self.pass_input.disabled = True
            self.captcha_input.disabled = True
            self.update()
            time.sleep(0.5)
            self.on_login_success()
        else:
            self.handle_failed_attempt()

    def handle_failed_attempt(self):
        self.attempts += 1
        remaining = self.MAX_ATTEMPTS - self.attempts
        self.regenerate_captcha() # Nueva suma
        self.pass_input.value = ""
        
        if remaining <= 0:
            self.lockout_time = time.time()
            self.status_text.value = "⛔ Demasiados intentos.\nBloqueo temporal de 5 minutos."
            self.status_text.color = "red"
            self.pass_input.disabled = True
            self.captcha_input.disabled = True
            self.login_btn.disabled = True
            self.logo.name = "timer_off"
            self.logo.color = "red"
        else:
            self.status_text.value = f"❌ Contraseña incorrecta.\nTe quedan {remaining} intentos."
        
        self.update()

    def reset_lockout(self):
        self.attempts = 0
        self.lockout_time = None
        self.pass_input.disabled = False
        self.captcha_input.disabled = False
        self.login_btn.disabled = False
        self.logo.name = "lock_outline"
        self.logo.color = "blue"
        self.status_text.value = ""
        self.regenerate_captcha()

    def regenerate_captcha(self):
        self.num1 = random.randint(1, 10)
        self.num2 = random.randint(1, 10)
        self.captcha_answer = self.num1 + self.num2
        self.captcha_input.label = f"¿Cuánto es {self.num1} + {self.num2}?"
        self.captcha_input.value = ""