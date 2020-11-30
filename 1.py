import os
from pathlib import Path
import json
import time

import requests


class Parse5ka:
    _headers = {
        'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:82.0) Gecko/20100101 Firefox/82.0",
    }
    _params = {
        'records_per_page': 50,
    }

    def __init__(self, start_url):
        self.start_url = start_url

    @staticmethod
    def _get(*args, **kwargs) -> requests.Response:
        while True:
            try:
                response = requests.get(*args, **kwargs)
                if response.status_code != 200:
                    # todo Создать класс исключение
                    raise Exception
                return response
            except Exception:
                time.sleep(0.25)

    def parse(self, url):
        params = self._params
        while url:
            response: requests.Response = self._get(url, params=params, headers=self._headers)
            if params:
                params = {}
            data: dict = response.json()
            url = data.get('next')
            yield data.get('results')

    def run(self):
        for products in self.parse(self.start_url):
            for product in products:
                self._save_to_file(product, product['id'])
            time.sleep(0.1)

    @staticmethod
    def _save_to_file(product, file_name):
        path = Path(os.path.dirname(__file__)).joinpath('Products').joinpath(f'{file_name}.json')
        with open(path, 'w', encoding='UTF-8') as file:
            json.dump(product, file, ensure_ascii=False)


class ParseByCategory(Parse5ka):

    def __init__(self, start_url, category_url):
        self.category_url = category_url
        super().__init__(start_url)

    def _save_cat_to_file(self):
        for category in self._get(self.category_url, headers=self._headers).json():
            data = {
                "name": category['parent_group_name'],
                'code': category['parent_group_code'],
                "products": [],
            }
            file_name = category['parent_group_name']
            self._save_to_file(data, file_name)

    @staticmethod
    def _save_by_cat_to_file(product, cat_name):
        path = Path(os.path.dirname(__file__)).joinpath('Products').joinpath(f'{cat_name}.json')
        with open(path, 'a', encoding='UTF-8') as file:
            json.dump(product, file, ensure_ascii=False)

    def run(self):
        self._save_cat_to_file()

        for category in self._get(self.category_url, headers=self._headers).json():
            for products in self.parse(self.start_url):
                self._save_to_file(products, category['parent_group_name'])
        time.sleep(0.1)


if __name__ == '__main__':
    parser = ParseByCategory('https://5ka.ru/api/v2/special_offers/', 'https://5ka.ru/api/v2/categories/')
    parser.run()
