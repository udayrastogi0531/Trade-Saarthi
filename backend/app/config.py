"""Application configuration via environment variables."""

from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "AI Trading Assistant"
    app_env: Literal["development", "staging", "production"] = "development"
    debug: bool = False
    api_prefix: str = "/api/v1"
    secret_key: str = Field(default="change-me-in-production")

    database_url: str = Field(
        default="postgresql+asyncpg://trading:trading_secret@localhost:5432/trading_db"
    )
    redis_url: str = "redis://localhost:6379/0"

    max_daily_loss_pct: float = 2.0
    max_drawdown_pct: float = 10.0
    max_trades_per_day: int = 5
    max_position_size_pct: float = 5.0
    min_risk_reward: float = 2.0
    default_account_capital: float = 100_000.0

    groq_api_key: str = ""
    groq_model: str = "llama-3.3-70b-versatile"
    ai_provider: Literal["groq", "deepseek"] = "groq"
    deepseek_api_key: str = ""
    deepseek_base_url: str = "https://api.deepseek.com"
    news_api_key: str = ""
    marketaux_api_key: str = ""

    telegram_bot_token: str = ""
    telegram_chat_id: str = ""
    telegram_enabled: bool = False

    broker_mode: Literal["paper", "kite"] = "paper"
    kite_api_key: str = ""
    kite_api_secret: str = ""
    kite_access_token: str = ""

    market_data_provider: Literal["mock", "kite", "yfinance"] = "mock"
    nse_enabled: bool = True

    execution_enabled: bool = False
    paper_trading: bool = True

    prometheus_enabled: bool = True

    # Scanner
    scanner_enabled: bool = True
    scanner_interval_minutes: int = 3
    watchlist_symbols: str = "RELIANCE,TCS,INFY,HDFCBANK,NIFTY"
    scanner_min_confidence: float = 70.0
    scanner_max_concurrent: int = 10

    # Signal quality (base thresholds — v4 conservative overrides below)
    min_mtf_alignment_score: float = 0.65

    # Advanced risk
    atr_stop_multiplier: float = 1.5
    max_portfolio_exposure_pct: float = 30.0
    max_sector_exposure_pct: float = 15.0
    consecutive_loss_reduction: int = 3
    daily_risk_budget_pct: float = 2.0
    volatility_position_scale: bool = True

    # Celery
    celery_broker_url: str = ""
    celery_result_backend: str = ""

    # Chart analysis
    chart_analysis_enabled: bool = True

    # Copilot
    copilot_enabled: bool = True
    copilot_default_language: Literal["en", "hi", "hinglish"] = "hinglish"
    copilot_session_ttl_hours: int = 24
    copilot_max_history: int = 20

    # Voice — STT
    stt_provider: Literal["groq", "faster_whisper", "deepgram"] = "groq"
    groq_whisper_model: str = "whisper-large-v3"
    deepgram_api_key: str = ""
    faster_whisper_model: str = "base"

    # Voice — TTS
    tts_provider: Literal["gtts", "elevenlabs", "azure"] = "gtts"
    elevenlabs_api_key: str = ""
    elevenlabs_voice_id: str = "21m00Tcm4TlvDq8ikWAM"
    azure_tts_key: str = ""
    azure_tts_region: str = "eastus"
    voice_alerts_enabled: bool = True

    # Market structure
    min_structure_confidence: float = 55.0
    structure_block_fake_breakout: bool = True

    # Learning engine
    learning_enabled: bool = True
    adaptive_confidence_enabled: bool = True

    # Briefings
    briefings_enabled: bool = True
    briefing_language: Literal["en", "hi", "hinglish"] = "hinglish"

    # Execution safety
    execution_manual_confirm: bool = True
    execution_cooldown_minutes: int = 15
    execution_max_slippage_pct: float = 0.3
    execution_duplicate_window_minutes: int = 30
    volatility_shutdown_atr_pct: float = 8.0

    # Scanner v2.2
    scanner_retry_attempts: int = 3
    scanner_health_degraded_latency_ms: int = 5000

    # v4.0 — Conservative signal filtering
    min_signal_quality_score: float = 72.0
    signal_confidence_threshold: float = 78.0
    conservative_mode: bool = True
    min_liquidity_volume_ratio: float = 0.65
    max_fake_breakout_risk: float = 0.55
    volatility_anomaly_atr_pct: float = 12.0

    # Walk-forward validation
    walk_forward_windows: int = 5
    walk_forward_train_pct: float = 0.7
    walk_forward_oos_pct: float = 0.2
    overfitting_sharpe_gap_threshold: float = 1.5
    strategy_decay_win_rate_drop: float = 15.0

    # Monte Carlo
    monte_carlo_simulations: int = 2000
    monte_carlo_ruin_threshold_pct: float = 25.0

    # Data quality
    data_quality_enabled: bool = True
    max_candle_gap_minutes: int = 30
    stale_data_threshold_seconds: int = 120
    block_signals_on_bad_data: bool = True
    enforce_nse_market_hours: bool = False

    # AI reasoning cache (reduces duplicate LLM calls during scans)
    ai_reasoning_cache_ttl_seconds: int = 180
    capital_safety_enabled: bool = True
    default_deployment_stage: Literal["sandbox", "tiny_live", "staged", "full"] = "sandbox"
    tiny_live_max_capital: float = 10_000.0

    # Security
    api_auth_enabled: bool = False
    api_key: str = ""
    api_rate_limit_per_minute: int = 120
    audit_log_enabled: bool = True

    @property
    def watchlist(self) -> list[str]:
        return [s.strip().upper() for s in self.watchlist_symbols.split(",") if s.strip()]

    @property
    def celery_broker(self) -> str:
        return self.celery_broker_url or self.redis_url

    @property
    def celery_backend(self) -> str:
        return self.celery_result_backend or self.redis_url

    @field_validator("min_risk_reward")
    @classmethod
    def validate_min_rr(cls, v: float) -> float:
        if v < 1.0:
            raise ValueError("min_risk_reward must be at least 1.0")
        return v

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()
