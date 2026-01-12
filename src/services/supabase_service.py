import os
from supabase import create_client, Client
from dotenv import load_dotenv

# Cargar variables de entorno desde .env
load_dotenv()

class SupabaseClient:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SupabaseClient, cls).__new__(cls)
            cls._instance.client = cls._init_client()
        return cls._instance

    @staticmethod
    def _init_client() -> Client:
        url: str = os.environ.get("SUPABASE_URL")
        key: str = os.environ.get("SUPABASE_KEY")

        if not url or not key:
            raise ValueError("❌ ERROR: Faltan SUPABASE_URL o SUPABASE_KEY en el archivo .env")

        try:
            # Inicializamos el cliente
            client = create_client(url, key)
            return client
        except Exception as e:
            print(f"❌ Error al conectar con Supabase: {e}")
            raise e

    def get_client(self) -> Client:
        return self.client

# Instancia lista para importar
supabase_client = SupabaseClient().get_client()