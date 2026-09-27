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
    # IA: "ollama" (local y gratuito), "anthropic" (Claude, de pago) o "reglas" (sin modelo).
    # Si el proveedor no responde se usa la heurística y la respuesta se marca como simulada.
    ia_proveedor: str = "ollama"
    ia_timeout: float = 120
    ollama_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.2:3b"
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-opus-5"

    @property
    def allowed_domains(self) -> list[str]:
        return [d.strip().lower() for d in self.allowed_email_domains.split(",") if d.strip()]

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
