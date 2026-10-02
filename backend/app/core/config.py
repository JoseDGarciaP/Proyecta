from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "Proyecta API"
    database_url: str = "postgresql+psycopg://proyecta:proyecta@localhost:5432/proyecta"
    secret_key: str = "dev-secret-solo-para-desarrollo-local-cambiar"
    access_token_expire_minutes: int = 120
    # Dominios de correo permitidos para registrarse. Vacío = cualquiera. Los aliados externos no se restringen.
    allowed_email_domains: str = "ufpso.edu.co"
    cors_origins: str = "http://localhost:5173"
    # Dirección de la interfaz, para armar el enlace del correo de verificación.
    frontend_url: str = "http://localhost:5173"
    verificacion_horas: int = 48
    # Antes de crear una cuenta se consulta el DNS del dominio (registros MX) para descartar
    # correos inventados. Con false solo se revisa formato, tipeo y dominios desechables.
    verificar_dns_correo: bool = True
    correo_dns_timeout: float = 3.0
    # Correo saliente (SMTP). Vacío = no se envía: el enlace se imprime en la consola de la API.
    # Con Gmail: smtp.gmail.com, puerto 587 y una "contraseña de aplicación" de la cuenta.
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_usuario: str = ""
    smtp_password: str = ""
    smtp_remitente: str = ""
    # Ingreso con Google: ID de cliente OAuth (Google Cloud Console). Vacío = botón oculto.
    google_client_id: str = ""
    # IA: "ollama" (local y gratuito), "groq" (en línea, capa gratuita), "anthropic" (Claude, de pago)
    # o "reglas" (sin modelo).
    # Si el proveedor no responde se usa la heurística y la respuesta se marca como simulada.
    ia_proveedor: str = "ollama"
    ia_timeout: float = 120
    ollama_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.2:3b"
    groq_api_key: str = ""
    groq_model: str = "openai/gpt-oss-20b"
    groq_url: str = "https://api.groq.com/openai/v1"
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-opus-5"
    # Similitud semántica con sentence-transformers (gratuito, corre en la CPU).
    # El modelo se descarga una sola vez (~470 MB) a la caché de Hugging Face del usuario.
    # Si no está instalado o no se puede cargar, se usa similitud por palabras en común.
    embeddings_activos: bool = True
    embeddings_modelo: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

    @property
    def allowed_domains(self) -> list[str]:
        return [d.strip().lower() for d in self.allowed_email_domains.split(",") if d.strip()]

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
