from utils.mydb import *
from aiogram import types
from random import randint

class Catalog():

    async def get_info(self, catalog_id):
        conn, cursor = connect()

        cursor.execute(f'SELECT * FROM catalogs WHERE catalog_id = "{catalog_id}"')
        self.catalog = cursor.fetchone()

        self.catalog_id = self.catalog[0]
        self.catalog_name = self.catalog[1]
        self.catalog_photo = self.catalog[2]


    async def get_menu(self):
        await self.get_all_catalogs()

        markup = types.InlineKeyboardMarkup(row_width=2)

      #  for i in self.catalogs:
       #     markup.add(types.InlineKeyboardButton(text=f'{i[1]}', callback_data=f'catalog:{i[0]}'))
        
        x1 = 0
        x2 = 1
        try:
            for i in range(len(self.catalogs)):
                markup.add(
                    types.InlineKeyboardButton(text=f'{self.catalogs[x1][1]}', callback_data=f'catalog:{self.catalogs[x1][0]}'),
                    types.InlineKeyboardButton(text=f'{self.catalogs[x2][1]}', callback_data=f'catalog:{self.catalogs[x2][0]}')
                )

                x1 += 2
                x2 += 2
        except Exception as e:
            try:
                markup.add(
                    types.InlineKeyboardButton(text=f'{self.catalogs[x1][1]}', callback_data=f'catalog:{self.catalogs[x1][0]}'),
                )
            except:
                return markup
        
        return markup


    async def get_all_catalogs(self):
        conn, cursor = connect()

        cursor.execute(f'SELECT * FROM catalogs')
        self.catalogs = cursor.fetchall()


    async def create_catalog(self, name, file_name):
        conn, cursor = connect()

        catalog_id = f"c{randint(0, 999)}"

        cursor.execute(f'INSERT INTO catalogs VALUES ("{catalog_id}", "{name}", "{file_name}")')
        conn.commit()

        try:
            cursor.execute(f'CREATE TABLE {catalog_id} (product_id TEXT, name TEXT, price DECIMAL(10, 2), description TEXT)')
            conn.commit()
        except:
            pass


    async def get_menu_del_catalogs(self):
        await self.get_all_catalogs()

        markup = types.InlineKeyboardMarkup(row_width=2)

        for i in self.catalogs:
            markup.add(types.InlineKeyboardButton(text=f'{i[1]}', callback_data=f'del_catalog:{i[0]}'))

        return markup


    async def del_catalog(self, catalog_id):
        conn, cursor = connect()

        cursor.execute(f'DELETE FROM catalogs WHERE catalog_id = "{catalog_id}"')
        conn.commit()


    async def get_menu_add_product(self):
        await self.get_all_catalogs()

        markup = types.InlineKeyboardMarkup(row_width=2)

        for i in self.catalogs:
            markup.add(types.InlineKeyboardButton(text=f'{i[1]}', callback_data=f'add_product:{i[0]}'))

        return markup


    async def get_menu_del_product(self):
        await self.get_all_catalogs()

        markup = types.InlineKeyboardMarkup(row_width=2)

        for i in self.catalogs:
            markup.add(types.InlineKeyboardButton(text=f'{i[1]}', callback_data=f'del_product_menu:{i[0]}'))

        return markup


    async def get_menu_upload_product(self):
        await self.get_all_catalogs()

        markup = types.InlineKeyboardMarkup(row_width=2)

        for i in self.catalogs:
            markup.add(types.InlineKeyboardButton(text=f'{i[1]}', callback_data=f'upload_catalog:{i[0]}'))

        return markup


    async def get_catalog_photo(self, catalog_id):
        await self.get_info(catalog_id)

        return self.catalog_photo
