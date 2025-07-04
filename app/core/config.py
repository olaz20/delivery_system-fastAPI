from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_hostname: str
    database_port: str
    database_password: str
    database_name: str 
    database_username: str

    email_host_user: str
    email_host_password: str
    default_from_email: str
    email_host: str
    email_port: str
    email_use_tls: bool
    email_use_ssl: bool
    access_token_expire_minutes: int
    refresh_token_expire_days: int
 
    secret_key: str

    default_admin_email: str
    admin_password: str
    
    upload_dir: str

    base_price_per_km: float
    weight_price_per_kg:float
    demand_multiplier:float
    gps_freshness_minutes:int

    paystack_secret_key: str
    frontend_url: str

    class Config:
        env_file = ".env"
settings = Settings()
