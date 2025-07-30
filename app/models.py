from sqlmodel import SQLModel, Field, Relationship, JSON, Column
from datetime import datetime
from decimal import Decimal
from typing import Optional, List, Dict, Any
from enum import Enum


# Enums for type safety
class TransactionType(str, Enum):
    BUY = "BUY"
    SELL = "SELL"


class AlertType(str, Enum):
    ABOVE = "ABOVE"
    BELOW = "BELOW"


class AlertStatus(str, Enum):
    ACTIVE = "ACTIVE"
    TRIGGERED = "TRIGGERED"
    DISABLED = "DISABLED"


# Persistent models (stored in database)
class User(SQLModel, table=True):
    __tablename__ = "users"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(unique=True, max_length=50)
    email: str = Field(unique=True, max_length=255, regex=r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")
    full_name: str = Field(max_length=100)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    holdings: List["PortfolioHolding"] = Relationship(back_populates="user")
    transactions: List["Transaction"] = Relationship(back_populates="user")
    alerts: List["PriceAlert"] = Relationship(back_populates="user")


class Stock(SQLModel, table=True):
    __tablename__ = "stocks"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    symbol: str = Field(unique=True, max_length=10, index=True)
    name: str = Field(max_length=200)
    exchange: str = Field(max_length=50)
    sector: Optional[str] = Field(default=None, max_length=100)
    market_cap: Optional[Decimal] = Field(default=None, decimal_places=2)
    current_price: Decimal = Field(decimal_places=4)
    previous_close: Decimal = Field(decimal_places=4)
    day_change: Decimal = Field(decimal_places=4)
    day_change_percent: Decimal = Field(decimal_places=4)
    volume: int = Field(default=0)
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Additional market data stored as JSON
    market_data: Dict[str, Any] = Field(default={}, sa_column=Column(JSON))

    # Relationships
    holdings: List["PortfolioHolding"] = Relationship(back_populates="stock")
    transactions: List["Transaction"] = Relationship(back_populates="stock")
    alerts: List["PriceAlert"] = Relationship(back_populates="stock")
    price_history: List["StockPriceHistory"] = Relationship(back_populates="stock")


class PortfolioHolding(SQLModel, table=True):
    __tablename__ = "portfolio_holdings"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    stock_id: int = Field(foreign_key="stocks.id", index=True)
    quantity: Decimal = Field(decimal_places=6)  # Support fractional shares
    average_cost: Decimal = Field(decimal_places=4)  # Average cost per share
    total_invested: Decimal = Field(decimal_places=2)  # Total amount invested
    current_value: Decimal = Field(decimal_places=2, default=Decimal("0"))  # Current market value
    unrealized_gain_loss: Decimal = Field(decimal_places=2, default=Decimal("0"))
    unrealized_gain_loss_percent: Decimal = Field(decimal_places=4, default=Decimal("0"))
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    user: User = Relationship(back_populates="holdings")
    stock: Stock = Relationship(back_populates="holdings")


class Transaction(SQLModel, table=True):
    __tablename__ = "transactions"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    stock_id: int = Field(foreign_key="stocks.id", index=True)
    transaction_type: TransactionType
    quantity: Decimal = Field(decimal_places=6)
    price: Decimal = Field(decimal_places=4)  # Price per share at transaction
    total_amount: Decimal = Field(decimal_places=2)  # Total transaction amount
    fees: Decimal = Field(decimal_places=2, default=Decimal("0"))  # Transaction fees
    notes: Optional[str] = Field(default=None, max_length=500)
    transaction_date: datetime = Field(default_factory=datetime.utcnow)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    user: User = Relationship(back_populates="transactions")
    stock: Stock = Relationship(back_populates="transactions")


class PriceAlert(SQLModel, table=True):
    __tablename__ = "price_alerts"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    stock_id: int = Field(foreign_key="stocks.id", index=True)
    alert_type: AlertType
    target_price: Decimal = Field(decimal_places=4)
    status: AlertStatus = Field(default=AlertStatus.ACTIVE)
    message: Optional[str] = Field(default=None, max_length=200)
    triggered_at: Optional[datetime] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    user: User = Relationship(back_populates="alerts")
    stock: Stock = Relationship(back_populates="alerts")


class StockPriceHistory(SQLModel, table=True):
    __tablename__ = "stock_price_history"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    stock_id: int = Field(foreign_key="stocks.id", index=True)
    price: Decimal = Field(decimal_places=4)
    volume: int = Field(default=0)
    timestamp: datetime = Field(default_factory=datetime.utcnow, index=True)

    # OHLC data for charts
    open_price: Optional[Decimal] = Field(default=None, decimal_places=4)
    high_price: Optional[Decimal] = Field(default=None, decimal_places=4)
    low_price: Optional[Decimal] = Field(default=None, decimal_places=4)
    close_price: Optional[Decimal] = Field(default=None, decimal_places=4)

    # Relationship
    stock: Stock = Relationship(back_populates="price_history")


class PortfolioSummary(SQLModel, table=True):
    __tablename__ = "portfolio_summaries"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", unique=True, index=True)
    total_value: Decimal = Field(decimal_places=2, default=Decimal("0"))
    total_invested: Decimal = Field(decimal_places=2, default=Decimal("0"))
    total_gain_loss: Decimal = Field(decimal_places=2, default=Decimal("0"))
    total_gain_loss_percent: Decimal = Field(decimal_places=4, default=Decimal("0"))
    day_change: Decimal = Field(decimal_places=2, default=Decimal("0"))
    day_change_percent: Decimal = Field(decimal_places=4, default=Decimal("0"))
    number_of_holdings: int = Field(default=0)
    last_updated: datetime = Field(default_factory=datetime.utcnow)

    # Relationship
    user: User = Relationship()


# Non-persistent schemas (for validation, forms, API requests/responses)
class UserCreate(SQLModel, table=False):
    username: str = Field(max_length=50)
    email: str = Field(max_length=255)
    full_name: str = Field(max_length=100)


class UserUpdate(SQLModel, table=False):
    username: Optional[str] = Field(default=None, max_length=50)
    email: Optional[str] = Field(default=None, max_length=255)
    full_name: Optional[str] = Field(default=None, max_length=100)
    is_active: Optional[bool] = Field(default=None)


class StockCreate(SQLModel, table=False):
    symbol: str = Field(max_length=10)
    name: str = Field(max_length=200)
    exchange: str = Field(max_length=50)
    sector: Optional[str] = Field(default=None, max_length=100)
    current_price: Decimal = Field(decimal_places=4)


class StockUpdate(SQLModel, table=False):
    name: Optional[str] = Field(default=None, max_length=200)
    exchange: Optional[str] = Field(default=None, max_length=50)
    sector: Optional[str] = Field(default=None, max_length=100)
    current_price: Optional[Decimal] = Field(default=None, decimal_places=4)
    previous_close: Optional[Decimal] = Field(default=None, decimal_places=4)
    is_active: Optional[bool] = Field(default=None)


class TransactionCreate(SQLModel, table=False):
    stock_id: int
    transaction_type: TransactionType
    quantity: Decimal = Field(decimal_places=6)
    price: Decimal = Field(decimal_places=4)
    fees: Decimal = Field(decimal_places=2, default=Decimal("0"))
    notes: Optional[str] = Field(default=None, max_length=500)
    transaction_date: Optional[datetime] = Field(default=None)


class PriceAlertCreate(SQLModel, table=False):
    stock_id: int
    alert_type: AlertType
    target_price: Decimal = Field(decimal_places=4)
    message: Optional[str] = Field(default=None, max_length=200)


class PriceAlertUpdate(SQLModel, table=False):
    alert_type: Optional[AlertType] = Field(default=None)
    target_price: Optional[Decimal] = Field(default=None, decimal_places=4)
    status: Optional[AlertStatus] = Field(default=None)
    message: Optional[str] = Field(default=None, max_length=200)


class StockPriceUpdate(SQLModel, table=False):
    price: Decimal = Field(decimal_places=4)
    volume: int = Field(default=0)
    open_price: Optional[Decimal] = Field(default=None, decimal_places=4)
    high_price: Optional[Decimal] = Field(default=None, decimal_places=4)
    low_price: Optional[Decimal] = Field(default=None, decimal_places=4)
    close_price: Optional[Decimal] = Field(default=None, decimal_places=4)


# Response schemas for API endpoints
class PortfolioHoldingResponse(SQLModel, table=False):
    id: int
    stock_symbol: str
    stock_name: str
    quantity: Decimal
    average_cost: Decimal
    current_price: Decimal
    current_value: Decimal
    unrealized_gain_loss: Decimal
    unrealized_gain_loss_percent: Decimal
    day_change: Decimal
    day_change_percent: Decimal


class PortfolioSummaryResponse(SQLModel, table=False):
    total_value: Decimal
    total_invested: Decimal
    total_gain_loss: Decimal
    total_gain_loss_percent: Decimal
    day_change: Decimal
    day_change_percent: Decimal
    number_of_holdings: int
    holdings: List[PortfolioHoldingResponse]


class StockSearchResponse(SQLModel, table=False):
    symbol: str
    name: str
    exchange: str
    current_price: Decimal
    day_change: Decimal
    day_change_percent: Decimal
