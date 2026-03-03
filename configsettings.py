"""
Market Microstructure Arbitrage Configuration
Architectural Rationale: Pydantic settings for type-safe config with env fallbacks.
Centralized configuration prevents scattered API keys and enables hot reloading.
"""
from typing import Dict, List, Optional
from pydantic import Field, SecretStr, validator
from pydantic_settings import BaseSettings
import structlog

logger = structlog.get_logger(__name__)

class ExchangeConfig(BaseSettings):
    """Exchange-specific configuration with rate limit awareness"""
    name: str
    api_key: SecretStr
    api_secret: SecretStr
    enable_rate_limit: bool = True
    rate_limit_requests_per_minute: int = 100
    markets_to_monitor: List[str] = Field(default=["BTC/USDT", "ETH/USDT", "SOL/USDT"])
    
    @validator('markets_to_monitor')
    def validate_markets(cls, v):
        if not v:
            raise ValueError("At least one market must be monitored")
        if len(v) > 10:
            logger.warning("Monitoring more than 10 markets may impact performance")
        return v

class ArbitrageConfig(BaseSettings):
    """Arbitrage detection thresholds and parameters"""
    minimum_spread_percentage: float = Field(0.001, ge=0.0001, le=1.0)
    minimum_volume_usd: float = Field(1000.0, ge=100.0)
    max_slippage_percentage: float = Field(0.05, ge=0.01, le=1.0)
    triangular_pairs: List[List[str]] = Field(
        default=[
            ["BTC", "ETH", "USDT"],
            ["SOL", "BTC", "USDT"],
            ["ADA", "ETH", "USDT"]
        ]
    )
    
    # Timeouts in seconds
    order_book_timeout: int = 5
    execution_timeout: int = 10
    
    @validator('triangular_pairs')
    def validate_triangular_pairs(cls, v):
        for pair in v:
            if len(pair) != 3:
                raise ValueError(f"Triangular pair must have 3 assets: {pair}")
            if len(set(pair)) != 3:
                raise ValueError(f"Triangular pair must have unique assets: {pair}")
        return v

class SystemConfig(BaseSettings):
    """System-wide configuration"""
    log_level: str = Field("INFO", pattern="^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$")
    firebase_project_id: Optional[str] = None
    firestore_collection_prefix: str = "arbitrage_"
    max_concurrent_tasks: int = Field(10, ge=1, le=50)
    
    # Health checks
    health_check_interval: int = 30
    max_consecutive_failures: int = 3
    
    class Config:
        env_file = ".env"
        env_prefix = "ARB_"

class TradingConfig(Base