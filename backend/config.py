from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import model_validator

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    database_url: str = "sqlite:///./conduit.db"
    redis_url: str = ""
    customer_token: str = "local-customer-change-me"
    operator_token: str = "local-operator-change-me"
    customer_id: str = "cus_demo"
    payment_provider: str = "simulator"
    stripe_secret_key: str = ""
    stripe_webhook_secret: str = ""
    planner: str = "rules"
    llm_base_url: str = "https://api.openai.com/v1"
    llm_api_key: str = ""
    llm_model: str = ""
    reviewer_model: str = ""
    embedding_model: str = ""
    auto_limit_cents: int = 2500
    confirm_limit_cents: int = 25000
    shadow_mode: bool = False

    @model_validator(mode="after")
    def safe_config(self):
        if not 0 <= self.auto_limit_cents <= self.confirm_limit_cents:
            raise ValueError("Invalid authorization thresholds")
        if self.customer_token == self.operator_token:
            raise ValueError("Customer and operator tokens must differ")
        if self.payment_provider not in {"simulator", "stripe"}:
            raise ValueError("Unknown payment provider")
        if self.payment_provider == "stripe" and not self.stripe_secret_key.startswith("sk_test_"):
            raise ValueError("Only Stripe test keys are allowed")
        return self

@lru_cache
def settings():
    return Settings()
