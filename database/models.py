"""
Модели базы данных для хранения информации о товарах и пользователях.
"""
from datetime import datetime
from typing import Optional
from sqlalchemy import BigInteger, String, Float, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Базовый класс для всех моделей."""
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )


class User(Base):
    """Модель пользователя."""
    
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    username: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # Отношения
    products: Mapped[list["Product"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<User {self.id}>"


class Product(Base):
    """Модель отслеживаемого товара."""
    
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    target_price: Mapped[float] = mapped_column(Float, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # Внешние ключи
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )
    
    # Отношения
    user: Mapped[User] = relationship(back_populates="products")
    price_history: Mapped[list["PriceHistory"]] = relationship(
        back_populates="product",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Product {self.name} (Target: {self.target_price})>"


class PriceHistory(Base):
    """Модель для хранения истории цен."""
    
    __tablename__ = "price_history"

    id: Mapped[int] = mapped_column(primary_key=True)
    price: Mapped[float] = mapped_column(Float, nullable=False)
    url: Mapped[str] = mapped_column(String(1000), nullable=False)
    store: Mapped[str] = mapped_column(String(50), nullable=False)
    
    # Внешние ключи
    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False
    )
    
    # Отношения
    product: Mapped[Product] = relationship(back_populates="price_history")

    def __repr__(self) -> str:
        return f"<PriceHistory {self.store} - {self.price}>"