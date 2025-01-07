"""
Операции с базой данных.
"""
from typing import Optional, List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from .models import User, Product, PriceHistory


class DatabaseOperations:
    """Класс для работы с базой данных."""

    def __init__(self, session: AsyncSession):
        """
        Инициализация операций с базой данных.
        
        Args:
            session: Асинхронная сессия SQLAlchemy
        """
        self.session = session

    async def get_or_create_user(self, user_id: int, username: Optional[str] = None) -> User:
        """
        Получение или создание пользователя.
        
        Args:
            user_id: ID пользователя в Telegram
            username: Username пользователя в Telegram

        Returns:
            User: Объект пользователя
        """
        query = select(User).where(User.id == user_id)
        result = await self.session.execute(query)
        user = result.scalar_one_or_none()

        if not user:
            user = User(id=user_id, username=username)
            self.session.add(user)
            await self.session.commit()
            await self.session.refresh(user)

        return user

    async def add_product(self, user_id: int, name: str, target_price: float) -> Product:
        """
        Добавление нового товара для отслеживания.
        
        Args:
            user_id: ID пользователя
            name: Название товара
            target_price: Целевая цена

        Returns:
            Product: Созданный объект товара
        """
        product = Product(
            user_id=user_id,
            name=name,
            target_price=target_price
        )
        self.session.add(product)
        await self.session.commit()
        await self.session.refresh(product)
        return product

    async def get_user_products(self, user_id: int) -> List[Product]:
        """
        Получение всех активных товаров пользователя.
        
        Args:
            user_id: ID пользователя

        Returns:
            List[Product]: Список товаров пользователя
        """
        query = select(Product).where(
            Product.user_id == user_id,
            Product.is_active == True
        ).options(selectinload(Product.price_history))
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def delete_product(self, user_id: int, product_id: int) -> bool:
        """
        Удаление товара пользователя.
        
        Args:
            user_id: ID пользователя
            product_id: ID товара

        Returns:
            bool: True если товар успешно удален, False если товар не найден
        """
        query = select(Product).where(
            Product.user_id == user_id,
            Product.id == product_id
        )
        result = await self.session.execute(query)
        product = result.scalar_one_or_none()

        if not product:
            return False

        # Помечаем товар как неактивный вместо физического удаления
        product.is_active = False
        await self.session.commit()
        return True

    async def add_price_history(
        self,
        product_id: int,
        price: float,
        url: str,
        store: str
    ) -> PriceHistory:
        """
        Добавление записи в историю цен.
        
        Args:
            product_id: ID товара
            price: Цена товара
            url: URL товара
            store: Название магазина

        Returns:
            PriceHistory: Созданная запись истории цен
        """
        history = PriceHistory(
            product_id=product_id,
            price=price,
            url=url,
            store=store
        )
        self.session.add(history)
        await self.session.commit()
        await self.session.refresh(history)
        return history

    async def get_product_price_history(
        self,
        product_id: int,
        limit: int = 10
    ) -> List[PriceHistory]:
        """
        Получение истории цен товара.
        
        Args:
            product_id: ID товара
            limit: Максимальное количество записей

        Returns:
            List[PriceHistory]: История цен товара
        """
        query = select(PriceHistory).where(
            PriceHistory.product_id == product_id
        ).order_by(PriceHistory.created_at.desc()).limit(limit)
        result = await self.session.execute(query)
        return list(result.scalars().all())