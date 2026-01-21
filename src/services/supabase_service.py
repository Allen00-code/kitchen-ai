import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

class SupabaseService:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SupabaseService, cls).__new__(cls)
            cls._instance.client = None
        return cls._instance

    def __init__(self):
        if not self.client:
            url = os.getenv("SUPABASE_URL")
            key = os.getenv("SUPABASE_KEY")
            
            if not url or not key:
                raise ValueError("Faltan credenciales SUPABASE_URL o SUPABASE_KEY en .env")
                
            self.client: Client = create_client(url, key)

    # --- NUEVOS MÉTODOS DE AUTH ---
    
    def sign_in(self, email, password):
        """Inicia sesión y guarda el token en el cliente"""
        try:
            res = self.client.auth.sign_in_with_password({
                "email": email,
                "password": password
            })
            return res
        except Exception as e:
            raise e

    def sign_up(self, email, password):
        """Registra un nuevo usuario"""
        try:
            res = self.client.auth.sign_up({
                "email": email,
                "password": password
            })
            return res
        except Exception as e:
            raise e
            
    def sign_out(self):
        self.client.auth.sign_out()

    def get_user(self):
        return self.client.auth.get_user()

    # Método para ayudar a asignar el user_id automáticamente en los inserts si es necesario
    # (Aunque RLS lo maneja, es bueno tener el ID a mano)
    def get_user_id(self):
        user = self.get_user()
        if user and user.user:
            return user.user.id
        return None

# Instancia global
supabase_service = SupabaseService()
# Mantenemos la variable 'supabase_client' por compatibilidad con el resto de tu código
supabase_client = supabase_service.client