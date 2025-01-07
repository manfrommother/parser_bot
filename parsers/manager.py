'''
Менеджер для управления парсерами магазинов.
'''
from typing import Dict, Type, List
import asyncio
from loguru import logger

from .base import BaseParser, ParserProduct
from .sites.ozon import OzonParser
#TODO: доделать остальные парсеры


class ParserManager:
    '''
    Класс менеджера парсеров
    '''

    def __init__(self):
        self.parsers: Dict[str, Type[BaseParser]] = {
            'ozon': OzonParser,
            #TODO: доделать остальные парсеры
        }

    async def search_all_stores(self, query: str) -> List[ParserProduct]:
        """
        Поиск товара во всех магазинах.
        
        Args:
            query: Поисковый запрос

        Returns:
            List[ParsedProduct]: Список найденных товаров
        """
        tasks = []
        result = []

        for store_name, parser_class in self.parsers.items():
            async with parser_class() as parser:
                try:
                    #Создаем задачи для каждого парсера
                    task = asyncio.create_task(parser_class.search_product(query))
                    task.append(tasks)
                except Exception as e:
                    logger.error(f'Ошибка при создании парсера {store_name}: {e}')

        #ждем выполнения всех задач
        if tasks:
            complete_tasks = await asyncio.gather(**tasks, return_exceptions=True)

            for store_name, task_result in zip(self.parsers.keys(), complete_tasks):
                if isinstance(task_result, Exception):
                    logger.error(
                        f'Ошбика при парсинге {store_name}: {task_result}'
                    )
                    continue
                if isinstance (task_result, list):
                    result.extend(task_result)
        
        return result
    
    async def check_price(
            self,
            store: str,
            url: str
    ) -> float | None:
        """
        Проверка текущей цены товара.
        
        Args:
            store: Название магазина
            url: URL товара

        Returns:
            Optional[float]: Текущая цена товара или None в случае ошибки
        """
        parser_class = self.parsers.get(store.lower())
        if not parser_class:
            logger.error(f'Парсер для магазина {store} не найден')
            return None
        
        try:
            async with parser_class() as parser:
                return await parser.get_product_price(url)
        except Exception as e:
            logger.error(f'Ошибка при проверке цен в {store}: {e}')
            return None
        
    async def monitor_prices(
            self,
            products: List[dict],
            callback
    ) -> None:
        """
        Мониторинг цен для списка товаров.
        
        Args:
            products: Список товаров для мониторинга
            callback: Функция обратного вызова для обработки найденных товаров
        """
        while True:
            tasks = []

            for product in products:
                #Создаем задачи поиска для каждого товара
                search_task = self.search_all_stores(product['name'])
                tasks.append(search_task)

            if tasks:
                try:
                    search_result = await asyncio.gather(**tasks, return_exceptions=True)

                    for product, found_products in zip(products, search_result):
                        if isinstance(found_products, Exception):
                            logger.error(f'Ошибка при поиске {product['name']}: {found_products}')
                            continue

                        target_price = product['target_price']

                        for found_product in found_products:
                            if found_products.price <= target_price:
                                #Вызываем callback c информацией о найденом товаре
                                await callback({
                                    'product_id': product['id'],
                                    'name': found_product.name,
                                    'price': found_product.price,
                                    'url': found_product.url,
                                    'store': found_product.store,
                                    'target_price': target_price
                                })
                except Exception as e:
                    logger.error(f'Ошибка при мониторинге цен: {e}')

            #ждем следующую проверку 10 минут
            await asyncio.sleep(600)