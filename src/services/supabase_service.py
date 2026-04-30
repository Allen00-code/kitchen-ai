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

# Instancia global
supabase_service = SupabaseService()
# Variable 'supabase_client' para compatibilidad con el resto del código
supabase_client = supabase_service.client