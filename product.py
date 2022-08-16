from utils.mydb import *
from aiogram import types
from random import randint
from main import bot
from datetime import datetime

import logging
import config



preview_text = """
<b>{}</b>

Цена: <b>{} рублей</b>

Доступно: <b>{} шт</b>

<i>{}</i>
"""

payment_text = """
<b>💳 Оплата</b>

<b>{}</b>

Кол-во: <b>{} шт</b>

<b>К оплате {} рублей</b>
"""

log_text = """
👤 {}

❕ Цена: {}
❕ Кол-во: {}
❕ Файл: {}
"""


class Product():

    async def get_info(self, product_id, catalog_id):
        conn, cursor = connect()

        cursor.execute(f'SELECT * FROM {catalog_id} WHERE product_id = "{product_id}"')
        self.product = cursor.fetchone()

        self.product_id = self.product[0]
        self.name = self.product[1]
        self.price = float(self.product[2])
        self.description = self.product[3]


    async def get_all_products_in_catalog(self, catalog_id):
        conn, cursor = connect()

        cursor.execute(f'SELECT * FROM {catalog_id}')
        self.products = cursor.fetchall()


    async def get_menu_products(self, catalog_id):
        await self.get_all_products_in_catalog(catalog_id)

        markup = types.InlineKeyboardMarkup(row_width=2)

        for i in self.products:
            markup.add(types.InlineKeyboardButton(text=f'{i[1]} ⋆ {i[2]} руб', callback_data=f'product:{i[0]}:{catalog_id}'))

        markup.add(types.InlineKeyboardButton(text=f'« Назад', callback_data=f'back_to_catalog'))

        return markup


    async def get_preview_text(self, product_id, catalog_id):
        await self.get_info(product_id, catalog_id)
        await self.get_amount_products(product_id)

        text = preview_text.format(
            self.name,
            self.price,
            self.amount_products,
            self.description
        )

        return text


    async def get_amount_products(self, product_id):
        conn, cursor = connect()

        cursor.execute(f'SELECT * FROM {product_id}')
        products = cursor.fetchall()

        self.amount_products = len(products)

        return self.amount_products


    async def get_preview_menu(self, product_id, catalog_id):
        markup = types.InlineKeyboardMarkup(row_width=1)

        markup.add(
            types.InlineKeyboardButton(text=f'Купить', callback_data=f'preview_buy_menu:{product_id}:{catalog_id}'),
            types.InlineKeyboardButton(text=f'« Назад', callback_data=f'catalog:{catalog_id}:{catalog_id}')
        )

        return markup


    async def get_buy_menu(self, product_id, catalog_id, amount=None, price=None, update=None):

        if amount == None and price == None:
            await self.get_info(product_id, catalog_id)

            amount = 1
            price = self.price
        elif update != None:
            await self.get_info(product_id, catalog_id)

            amount += update
            price = self.price * amount


        markup = types.InlineKeyboardMarkup(row_width=3)

        markup.add(
            types.InlineKeyboardButton(text=f'🔻', callback_data=f'buy_menu_update:{product_id}:{catalog_id}:{amount}:{price}:-1'),
            types.InlineKeyboardButton(text=f'{amount} шт', callback_data=f'amount_product'),
            types.InlineKeyboardButton(text=f'🔺', callback_data=f'buy_menu_update:{product_id}:{catalog_id}:{amount}:{price}:1'),
        )

        markup.add(
            types.InlineKeyboardButton(text=f'🔻 10', callback_data=f'buy_menu_update:{product_id}:{catalog_id}:{amount}:{price}:-10'),
            types.InlineKeyboardButton(text=f'🔺 10', callback_data=f'buy_menu_update:{product_id}:{catalog_id}:{amount}:{price}:10'),
        )

        markup.add(
            types.InlineKeyboardButton(text=f'Купить за {price} руб', callback_data=f'buy:{product_id}:{catalog_id}:{amount}:{price}'),
        )

        markup.add(
            types.InlineKeyboardButton(text=f'« Назад', callback_data=f'product:{product_id}:{catalog_id}'),
        )

        return markup


    async def get_payment_text(self, product_id, catalog_id, amount, price):
        await self.get_info(product_id, catalog_id)

        text = payment_text.format(
            self.name,
            amount,
            price
        )

        return text


    async def get_payment_menu(self, product_id, catalog_id, amount, price):

        markup = types.InlineKeyboardMarkup(row_width=1)

        markup.add(
            types.InlineKeyboardButton(text=f'Оплатить с баланса', callback_data=f'pay:{product_id}:{catalog_id}:{amount}:{price}'),
            types.InlineKeyboardButton(text=f'« Назад', callback_data=f'buy_menu_update:{product_id}:{catalog_id}:{amount}:{price}:0'),
        )

        return markup


    async def get_products(self, product_id, amount):
        logging.info(f'get products: product_id - {product_id}; amount - {amount}')

        conn, cursor = connect()

        cursor.execute(f'SELECT * FROM {product_id} LIMIT {amount}')
        products = cursor.fetchall()

        id_list = await self.get_id_list(products)

        await self.del_products(product_id, id_list)

        file_name = f'docs/tovar_{randint(0, 99999999999)}.txt'

        with open(file_name, 'w', encoding='UTF-8') as txt:
            for i in products:
                txt.write(f'{i[0]}\n')

        return file_name


    async def get_id_list(self, products_list):
        id_list = []

        for i in products_list:
            id_list.append(i[1])

        return id_list


    async def del_products(self, product_id, id_list):
        conn, cursor = connect()

        for i in id_list:
            cursor.execute(f'DELETE FROM {product_id} WHERE id = "{i}"')
            conn.commit()


    async def purchases_log(self, file_name, user_id, price, amount):
        chat = await bot.get_chat(user_id)

        text = log_text.format(
            f'{chat.id}/@{chat.username}/{chat.full_name}',
            price,
            amount,
            file_name
        )

        with open(file_name, 'r', encoding='UTF-8') as doc:
            try:
                await bot.send_message(chat_id=config.config('channel_id_logs'), text=text)
                await bot.send_document(chat_id=config.config('channel_id_logs'), document=doc)
            except: pass

        conn, cursor = connect()

        cursor.execute(f'INSERT INTO purchase_logs VALUES ("{user_id}", "{file_name}", "{amount}", "{price}", "{datetime.now()}")')
        conn.commit()


    async def create_product(self, catalog_id, name, description, price):
        conn, cursor = connect()

        product_id = f'p{randint(0, 999)}'

        cursor.execute(f'INSERT INTO {catalog_id} VALUES ("{product_id}", "{name}", "{price}", "{description}")')
        conn.commit()


        cursor.execute(f'CREATE TABLE {product_id} (product TEXT, id TEXT)')
        conn.commit()


    async def get_menu_del_product(self, catalog_id):
        await self.get_all_products_in_catalog(catalog_id)

        markup = types.InlineKeyboardMarkup(row_width=2)

        for i in self.products:
            markup.add(types.InlineKeyboardButton(text=f'{i[1]}', callback_data=f'del_product:{i[0]}:{catalog_id}'))

        return markup


    async def del_product(self, product_id, catalog_id):
        conn, cursor = connect()

        cursor.execute(f'DELETE FROM {catalog_id} WHERE product_id = "{product_id}"')
        conn.commit()


    async def get_data_purchases(self, chat_id):
        conn, cursor = connect()

        cursor.execute(f'SELECT * FROM purchase_logs WHERE user_id = "{chat_id}"')
        purchases = cursor.fetchall()

        markup = types.InlineKeyboardMarkup(row_width=2)

        if len(purchases) == 0:
            text = 'У вас нет покупок'

            return text, markup
        else:
            text = 'Список ваших покупок:'

            for i in purchases:
                markup.add(types.InlineKeyboardButton(text=f'{i[4][:19]} - {i[1][5:]}', callback_data=f'download:{i[1]}'))

            return text, markup


    async def get_menu_upload_product(self, catalog_id):
        await self.get_all_products_in_catalog(catalog_id)

        markup = types.InlineKeyboardMarkup(row_width=2)

        for i in self.products:
            markup.add(types.InlineKeyboardButton(text=f'{i[1]}', callback_data=f'upload_product:{i[0]}:{catalog_id}'))

        return markup


    async def upload_product(self, product_id, file_name):
        conn, cursor = connect()

        n = '\n'

        good = 0
        bad = 0

        try:
            with open(file_name, 'rb') as txt:
                sql = f'INSERT INTO {product_id} VALUES ("%s", "%s")'
                for i in txt.readlines():
                    i = i.decode(errors='ignore')
                    try:
                        cursor.execute(sql, (i.replace(n, ""), randint(0, 999999999)))
                        conn.commit()

                        good += 1
                    except Exception as e:
                        print(e)
                        bad += 1
        except Exception as e:
            print(e)

        print(f'GOOD: {good}\nBAD: {bad}')
        return good, bad



