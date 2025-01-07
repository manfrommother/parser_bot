'''
Базовый класс для парсеров различных магазинов
'''
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, List
import asyncio
import aiohttp
from loguru import logger
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from undetected_chromedriver import Chrome

from config import config


@dataclass
class ParserProduct:
    '''Класс для хранения информации о найденном товаре'''
    name: str
    price: float
    url: str
    store: str

class BaseParser(ABC):
    """Базовый класс для всех парсеров."""
    
    def __init__(self):
        self.name: str = self.__class__.__name___
        self.session: Optional[aiohttp.ClientSession] = None
        self.driver: Optional[webdriver.Chrome] = None

    async def __aenter__(self):
        '''Создание сессии для HTTP запросов.'''
        if not self.session:
            self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_value, exc_tb):
        '''Закрытие сессии'''
        if self.session:
            await self.session.close()
            self.session = None
        if self.driver:
            self.driver.quit()
            self.driver = None
    
    def _init_selenuim(self) -> None:
        '''Инициализация Selenium драйвера'''
        chrome_options = Options()
        if config.HEADLESS:
            chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')

        service = Service(executable_path=config.CHROME_DRIVER_PATH)
        self.driver = Chrome(
            service=service,
            options=chrome_options
        )
    @abstractmethod
    async def search_product(self, query: str) -> List[ParsedProduct]:
        """
        Поиск товара на сайте магазина.
        
        Args:
            query: Поисковый запрос

        Returns:
            List[ParsedProduct]: Список найденных товаров
        """
        pass

    @abstractmethod
    async def get_product_price(self, url: str) -> Optional[float]:
        """
        Получение текущей цены товара по URL.
        
        Args:
            url: URL товара

        Returns:
            Optional[float]: Цена товара или None, если цена не найдена
        """
        pass

    async def _make_request(
        self,
        url: str,
        method: str = "GET",
        **kwargs
    ) -> Optional[str]:
        """
        Выполнение HTTP запроса с обработкой ошибок.
        
        Args:
            url: URL для запроса
            method: HTTP метод
            **kwargs: Дополнительные параметры для запроса

        Returns:
            Optional[str]: Текст ответа или None в случае ошибки
        """
        try:
            async with self.session.request(method, url, **kwargs) as response:
                if response.status == 200:
                    return await response.text()
                logger.warning(
                    f"{self.name}: Получен статус {response.status} "
                    f"при запросе к {url}"
                )
                return None
        except asyncio.TimeoutError:
            logger.error(f"{self.name}: Таймаут при запросе к {url}")
            return None
        except Exception as e:
            logger.error(f"{self.name}: Ошибка при запросе к {url}: {e}")
            return None

    @staticmethod
    def clean_price(price_str: str) -> Optional[float]:
        """
        Очистка строки с ценой и преобразование в число.
        
        Args:
            price_str: Строка с ценой

        Returns:
            Optional[float]: Очищенная цена или None в случае ошибки
        """
        try:
            # Удаляем все символы кроме цифр и точки
            cleaned = ''.join(c for c in price_str if c.isdigit() or c == '.')
            return float(cleaned)
        except (ValueError, TypeError):
            return None

