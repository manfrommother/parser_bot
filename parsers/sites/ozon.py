'''
Парсер для Ozon
'''
from typing import List, Optional
from bs4 import BeautifulSoup
from loguru import logger
import asyncio

from ..base import BaseParser, ParserProduct


class OzonParser(BaseParser):
    '''Класс парсер для Ozon'''

    BASE_URL = 'https://www.ozon.ru'
    SEARCH_URL = f'{BASE_URL}/search'

    def __init__(self):
        super().__init__()
        self._init_selenuim()

    async def search_product(self, query: str) -> List[ParserProduct]:
        '''
        Поиск товара на Ozon.

        Args:
            query: Поисковый запрос

        Returns:
            List[ParsedProduct]: Список найденных товаров
        '''
        try:
            search_url = f'{self.SEARCH_URL}?text={query}'
            self.driver.get(search_url)

            #Ждем загрузки результатов
            await asyncio.sleep(3)

            soup = BeautifulSoup(self.driver.page_source, 'lxml')

            result = []

            for product_card in soup.find_all('div', {'class': 'uo8'}):
                try:
                    name_elem = product_card.find('span', {'class': 'tsBody500Medium'})
                    price_elem = product_card.find('span', {'class': 'c3-c2'})
                    url_elem = product_card.find('a', {'class': 'title-hover-target'})

                    if not all([name_elem, price_elem, url_elem]):
                        continue

                    name = name_elem.text.strip()
                    price_str = price_elem.text.strip()
                    url = f'{self.BASE_URL}{url_elem['href']}'

                    price = self.clean_price(price_str)
                    if not price:
                        continue

                    result.append(ParserProduct(
                        name=name,
                        price=price,
                        url=url,
                        store='Ozon'
                    ))
                except Exception as e:
                    logger.error(f'Ошибка при парсинге карточки товара: {e}')
                    continue
            return result
        except Exception as e:
            logger.error(f'Ошибка при поиске на Ozon: {e}')
            return []
        
    async def get_product_price(self, url: str) -> Optional[float]:
        """
        Получение текущей цены товара по URL.
        
        Args:
            url: URL товара

        Returns:
            Optional[float]: Цена товара или None, если цена не найдена
        """
        try:
            self.driver.get(url)
            await asyncio.sleep(2)

            soup = BeautifulSoup(self.driver.page_source, 'lxml')
            price_elem = soup.find('span', {'class': 'c3-a2'})

            if not price_elem:
                return None
            
            return self.clean_price(price_elem.text)
        except Exception as e:
            logger.error(f'Ошибка при получении цены товара на Ozon: {e}')
            return None