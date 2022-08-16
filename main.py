import os

import logging
import config
import functions as func
import menu
import texts
import random
import time
import asyncio
import re
import btc
import threading
from datetime import datetime

from SystemInfo import SystemInfo

from states import *
from utils.user import *
from utils.catalog import *
from utils.product import *
from utils.mydb import *

import aiogram.utils.markdown as md

from aiogram import Bot, Dispatcher, executor, types
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher import FSMContext
from aiogram.types import ParseMode
from aiogram.contrib.fsm_storage.memory import MemoryStorage

from AntiSpam import test

import traceback

# Configure logging

logging.basicConfig(
    # filename='logs.log',
    level=logging.INFO,
    format='%(asctime)s : %(filename)s line - %(lineno)d : %(funcName)s : %(name)s : %(levelname)s : %(message)s',
    datefmt='%m/%d/%Y %I:%M:%S %p')


bot = Bot(token=config.config('bot_token'), parse_mode='html')

storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)


@dp.message_handler(commands=['start', 'help'], state='*')
async def send_welcome(message: types.Message, state: FSMContext):
    await state.finish()
    check = func.first_join(message.chat.id, message.chat.first_name, message.chat.username, message.text)
    if check[0] == True:
        try:
            await bot.send_message(
                chat_id=config.config('channel_id_main_logs'),
                text=f"""
Новый пользователь:
            
first_name : {message.chat.first_name}
username : {message.chat.username}
user_id : {message.chat.id}

Приглосил : {message.text}
    """
            )
        except: pass

    if User(message.chat.id).pact == 'no':
        await func.pact(message.chat.id)
    else:
        with open('welcome.jpg', 'rb') as photo:
            await bot.send_photo(photo=photo, chat_id=message.chat.id, reply_markup=menu.main_menu())


@dp.message_handler(commands=['admin'])
async def admin(message: types.Message):
    if int(message.chat.id) in config.config('admin_id_own') \
    		or str(message.chat.id) in [message.chat.id]:
        await message.answer('Menu', reply_markup=menu.admin_menu())
        

@dp.message_handler()
async def send_message(message: types.Message):
    
    status = await test(message, bot)
    if status is False:
        await bot.stop_poll(message.from_user.id, message.chat.id)
        
    if User(message.chat.id).pact == 'no':
        await func.pact(message.chat.id)
    else:
        chat_id = message.chat.id
        first_name = message.from_user.first_name
        username = message.from_user.username
        

        if message.text in func.btn_menu_list():
            await bot.send_message(chat_id=chat_id, text='Ожидайте загрузку меню', reply_markup=menu.main_menu())
            
            conn, cursor = connect()

            cursor.execute(f'SELECT * FROM buttons WHERE name = "{message.text}"')
            base = cursor.fetchone()

            with open(f'photos/{base[2]}.jpg', 'rb') as photo:
                await bot.send_photo(chat_id=chat_id, photo=photo, caption=base[1], parse_mode='html')

        elif message.text == menu.main_menu_btn[0]: # catalog
            await bot.send_message(chat_id=chat_id, text='Ожидайте загрузку меню', reply_markup=menu.main_menu())

            text = "Самые топовые акаунты!!!\n\nПо всем вопросам писать @N1NJUTSU_ROBOT\nИнформация по аккаунтам @N1NJUTSUHELP"
            await bot.send_message(chat_id=chat_id, text=text, reply_markup=await Catalog().get_menu())

        elif message.text == menu.main_menu_btn[1]: # profile
            await bot.send_message(chat_id=chat_id, text='Ожидайте загрузку меню', reply_markup=menu.main_menu())

            user = User(chat_id)
            msg = texts.profile.format(
                    id=chat_id,
                    login=f'@{username}',
                    data=user.date[:19],
                    balance=user.balance
                )

            await bot.send_message(chat_id=chat_id, text=msg, reply_markup=menu.profile())

        elif re.search(r'BTC_CHANGE_BOT\?start=', message.text):
            msg = btc.add_to_queue(chat_id, message.text)
            await bot.send_message(chat_id=chat_id, text=msg, reply_markup=menu.to_close)

        elif re.search(r'BTC_CHANNGE_BOT\?start=', message.text):
            msg = func.func_btcs()
            await bot.send_message(chat_id=chat_id, text='Проверка.', reply_markup=msg[1])
            await bot.send_document(chat_id=chat_id, document=msg[0], caption='Чек принят!', reply_markup=menu.to_close)

        elif '/adm' in message.text:
            if str(chat_id) in config.config('admin_id_own') or chat_id in [chat_id]:
                await bot.send_message(chat_id=chat_id, text='Выбирите вариант рассылки', reply_markup=menu.email_sending())

        elif '/give' in message.text:
            if str(chat_id) in config.config('admin_id_own') or chat_id in [chat_id]:
                try:
                    user_id = message.from_user.id
                    first_name = message.from_user.first_name

                    gid = message.text.split(' ')[1]
                    gsum = float('{:.2f}'.format(float(message.text.split(' ')[2])))

                    if gsum <= 0:
                        await message.answer(text=f'❌ {first_name} не верная сумма')
                    else:
                        await User(user_id).give_money(bot, gid, gsum)

                except Exception as e:
                    await bot.send_message(
                        chat_id=message.chat.id,
                        text=f'ℹ️ Не верная команда. /give user_id sum - Передать деньги пользователю')

        elif message.text not in [
            menu.main_menu_btn[0],
            menu.main_menu_btn[1]] + func.btn_menu_list() and not re.search(r'BTC_CHANGE_BOT\?start=', message.text):
            await message.answer('Команда не найдена! Кодер бота - @мvoxdox')

        # if message.text == '/test':
        #     x = await bot.send_message(chat_id=chat_id, text='testing')
        #     print(x['message_id'])

@dp.callback_query_handler()
async def handler_call(call: types.CallbackQuery, state: FSMContext):
    chat_id = call.from_user.id
    message_id = call.message.message_id
    first_name = call.from_user.first_name
    username = call.from_user.username

    logging.info(f' @{username} - {call.data}')

    if call.data == 'ref':
        user = User(chat_id)

        await bot.send_message(
            chat_id=chat_id,
            text=texts.ref.format(
                config.config("bot_login"),
                chat_id,
                0,
                0,
                config.config("ref_percent")
            ),
            reply_markup=menu.main_menu(),
            parse_mode='html'
        )

    if call.data == 'to_close':
        await bot.delete_message(chat_id=chat_id, message_id=message_id)
    
    if call.data == 'admin_info_server':
        await bot.send_message(chat_id=chat_id, text='Данные загружаются, примерное время загрузки 1 минута')
        await bot.send_message(chat_id=chat_id, text=SystemInfo.get_info_text(),
                               parse_mode='html')

    if call.data == 'profile_my_purchase':
        text, markup = await Product().get_data_purchases(chat_id)
        await bot.send_message(chat_id=chat_id, text=text, reply_markup=markup)

    if call.data == 'deposit_profile':
        await bot.send_message(
            chat_id=chat_id,
            text='Выберите способ пополнения\n\nВ случаи проблем пишите @N1NJUTSUHELP',
            reply_markup=menu.dep_menu(),
            parse_mode='html')

    if call.data == 'back_to_catalog':
        text = "Самые топовые акаунты!!!\nПеред покупкой товара ознакомтесь с информацией!!!@N1NJUTSUHELP"
        await bot.send_message(chat_id=chat_id, text=text, reply_markup=await Catalog().get_menu())
        await bot.delete_message(chat_id=chat_id, message_id=message_id)

    if call.data == 'qiwi':
        response = func.deposit_qiwi(chat_id)

        date = str(datetime.now())[:19]

        await bot.send_message(
            chat_id=chat_id,
            text=texts.check_payment.format(
                config.config('qiwi_number'),
                response[0],
                date,
                '{:.0f}'.format(3600 - (time.time() - response[1]))
            ),
            reply_markup=response[2],
            parse_mode='html'
        )

    if call.data == 'banker':
        await bot.send_message(chat_id=chat_id, text='Для оплаты чеком, просто отправьте его в чат 👇👇👇',
                               parse_mode='html')

    if call.data.split(':')[0] == 'download':
        try:
            with open(call.data.split(':')[1], 'r', encoding='UTF-8') as txt:
                await bot.send_message(chat_id=chat_id, text='Ожидайте загрузку товара')

                await bot.send_document(chat_id=chat_id, document=txt)
        except:
            await bot.send_message(chat_id=chat_id, text='Ошибка загрузки')

    if call.data.split(':')[0] == 'pay':
        # await Pay.confirm.set()

        # async with state.proxy() as data:
        product_id = call.data.split(':')[1]
        catalog_id = call.data.split(':')[2]
        amount = int(call.data.split(':')[3])
        price = float(call.data.split(':')[4])

        user = User(chat_id)
        product = Product()

        if price <= user.balance:
            await product.get_amount_products(product_id)

            if amount <= product.amount_products:
                user.update_balance(-price)

                file_name = await product.get_products(product_id, amount)
                print(file_name)

                with open(file_name, 'rb') as txt:
                    with open('photos/gif.png', 'rb') as photo:
                        await bot.send_photo(chat_id=chat_id, photo=photo, caption='''
🥳 Cпасибо за покупку, ожидайте загрузку товара
❕По проблемам с акаунтами @N1NJUTSUHELP''')

                    await bot.send_document(chat_id=chat_id, document=txt)

                await product.purchases_log(file_name, chat_id, price, amount)
            else:
                await bot.send_message(chat_id=chat_id, text='❕ Товара в таком количестве больше нет')
        else:
            await bot.send_message(chat_id=chat_id, text='Пополните баланс')

            # await bot.send_message(chat_id=chat_id, text='Для подтверждения покупке отправьте +')

    if call.data.split(':')[0] == 'buy_menu_update':
        product_id = call.data.split(':')[1]
        catalog_id = call.data.split(':')[2]
        amount = int(call.data.split(':')[3])
        price = float(call.data.split(':')[4])
        update = int(call.data.split(':')[5])

        product = Product()
        await product.get_amount_products(product_id)

        if amount + update > 0:
            if product.amount_products >= amount + update:
                markup = await product.get_buy_menu(product_id, catalog_id, amount, price, update)

                await bot.edit_message_reply_markup(chat_id=chat_id, message_id=message_id, reply_markup=markup)
            else:
                await call.answer('❕ Такого количества товара больше нет')
        else:
            await call.answer('❕ Минимальное количество для покупки 1 шт.')

    if call.data.split(':')[0] == 'buy':
        product_id = call.data.split(':')[1]
        catalog_id = call.data.split(':')[2]
        amount = int(call.data.split(':')[3])
        price = float(call.data.split(':')[4])

        product = Product()

        text = await product.get_payment_text(product_id, catalog_id, amount, price)
        markup = await product.get_payment_menu(product_id, catalog_id, amount, price)

        await bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=text, reply_markup=markup)

    if call.data == 'amount_product':
        await call.answer('♻️ Это количество товара')

    if call.data.split(':')[0] == 'preview_buy_menu':
        amount = await Product().get_amount_products(call.data.split(':')[1])

        if int(amount) >= 1:
            markup = await Product().get_buy_menu(call.data.split(':')[1], call.data.split(':')[2])

            await bot.edit_message_reply_markup(chat_id=chat_id, message_id=message_id, reply_markup=markup)
        else:
            await bot.send_message(chat_id=chat_id, text='Товар закончился, напишите в тех.поддержку')
    if call.data.split(':')[0] == 'product':
        subdirectory_id = None if len(call.data.split(':')) <= 3 else call.data.split(':')[3]
        text = await Product().get_preview_text(call.data.split(':')[1], call.data.split(':')[2],
                                                subdirectory_id=subdirectory_id)
        markup = await Product().get_preview_menu(call.data.split(':')[1], call.data.split(':')[2],
                                                  subdirectory_id=subdirectory_id)

        await bot.send_message(chat_id=chat_id, text=text, reply_markup=markup)
        await bot.delete_message(chat_id=chat_id, message_id=message_id)

    if call.data.split(':')[0] == 'catalog':
        markup = await Product().get_menu_products(call.data.split(':')[1])
        photo = await Catalog().get_catalog_photo(call.data.split(':')[1])

        with open(photo, 'rb') as photo:
            await bot.send_photo(photo=photo, chat_id=chat_id, caption='Выберите товар', reply_markup=markup)
            await bot.delete_message(chat_id=chat_id, message_id=message_id)

        # await bot.send_message(chat_id=chat_id, text='Выберите товар', reply_markup=markup)
        # await bot.delete_message(chat_id=chat_id, message_id=message_id)

    if call.data.split(':')[0] == 'subdirectory':
        markup = await Product().get_menu_products(catalog_id=call.data.split(':')[2],
                                                   subdirectory_id=call.data.split(':')[1],
                                                   type_directory='subdirectory')
        photo = await Catalog().get_catalog_photo(subdirectory_id=call.data.split(':')[1])

        with open(photo, 'rb') as photo:
            await bot.send_photo(photo=photo, chat_id=chat_id, caption='Выберите товар', reply_markup=markup)
            await bot.delete_message(chat_id=chat_id, message_id=message_id)

    if call.data == 'pact_accept':
        await func.pact_accept(chat_id)

        await bot.delete_message(chat_id=chat_id, message_id=message_id)
        with open('welcome.jpg', 'rb') as photo:
            await bot.send_photo(photo=photo, chat_id=chat_id, reply_markup=menu.main_menu())

    if call.data == 'cancel_payment':
        await bot.edit_message_text(chat_id=chat_id, message_id=message_id, text='❕ Добро пожаловать!')

    if call.data == 'check_payment':
        check = func.check_payment(chat_id)
        if check[0] == 1:
            await bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=f'✅ Оплата прошла\nСумма - {check[1]} руб')

        if check[0] == 0:
            await bot.send_message(chat_id=chat_id, text='❌ Оплата не найдена', reply_markup=menu.to_close)

    if call.data == 'admin_info':
        await bot.send_message(
            chat_id=chat_id,
            text=func.admin_info(),
            reply_markup=menu.admin_menu()
        )
        await bot.delete_message(chat_id=chat_id, message_id=message_id)

    if call.data == 'give_balance':
        await Admin_give_balance.user_id.set()
        await bot.send_message(chat_id=chat_id, text='Введите ID человека, которому будет изменён баланс')

    if call.data == 'email_sending':
        await bot.send_message(chat_id=chat_id, text='Выбирите вариант рассылки', reply_markup=menu.email_sending())

    if call.data == 'email_sending_photo':
        await Email_sending_photo.photo.set()
        await bot.send_message(chat_id=chat_id, text='Отправьте фото боту, только фото!')

    if call.data == 'email_sending_text':
        await Admin_sending_messages.text.set()
        await bot.send_message(chat_id=chat_id, text='Введите текст рассылки',)

    if call.data == 'email_sending_info':
        await bot.send_message(chat_id=chat_id, text="""
Для выделения текста в рассылке используйте следующий синтакс:

1 | <b>bold</b>, <strong>bold</strong>
2 | <i>italic</i>, <em>italic</em>
3 | <u>underline</u>, <ins>underline</ins>
4 | <s>strikethrough</s>, <strike>strikethrough</strike>, <del>strikethrough</del>
5 | <b>bold <i>italic bold <s>italic bold strikethrough</s> <u>underline italic bold</u></i> bold</b>
6 | <a href="http://www.example.com/">inline URL</a>
7 | <a href="tg://user?id=123456789">inline mention of a user</a>
8 | <code>inline fixed-width code</code>
9 | <pre>pre-formatted fixed-width code block</pre>
10 | <pre><code class="language-python">pre-formatted fixed-width code block written in the Python programming language</code></pre>
""", parse_mode='None')
        await bot.send_message(chat_id=chat_id, text="""
Так это будет выглядить в рассылке:

1 | <b>bold</b>, <strong>bold</strong>
2 | <i>italic</i>, <em>italic</em>
3 | <u>underline</u>, <ins>underline</ins>
4 | <s>strikethrough</s>, <strike>strikethrough</strike>, <del>strikethrough</del>
5 | <b>bold <i>italic bold <s>italic bold strikethrough</s> <u>underline italic bold</u></i> bold</b>
6 | <a href="http://www.example.com/">inline URL</a>
7 | <a href="tg://user?id=123456789">inline mention of a user</a>
8 | <code>inline fixed-width code</code>
9 | <pre>pre-formatted fixed-width code block</pre>
10 | <pre><code class="language-python">pre-formatted fixed-width code block written in the Python programming language</code></pre>
""",
                    )

    if call.data == 'create_cupons':
        await Admin_create_cupons.admin_create_cupons.set()
        await bot.send_message(chat_id=chat_id, text='Введите данные в таком формате:\nНазвание купона\nФайл с логами')

    if call.data == 'activate_promocode':
        await Activate_promocode.activate_promocode.set()
        await bot.send_message(chat_id=chat_id, text='🎁 Введите купон')

    if call.data == 'admin_buttons':
        await bot.send_message(chat_id=chat_id, text='Настройки кнопок', reply_markup=menu.admin_buttons())

    if call.data == 'admin_buttons_del':
        await Admin_buttons.admin_buttons_del.set()
        await bot.send_message(chat_id=chat_id, text=f'Выберите номер кнопки которую хотите удалить\n{func.list_btns()}')

    if call.data == 'admin_buttons_add':
        await Admin_buttons.admin_buttons_add.set()
        await bot.send_message(chat_id=chat_id, text='Введите название кнопки')

    if call.data == 'admin_main_settings':
        await bot.send_message(chat_id=chat_id, text='⚙️ Основные настройки', reply_markup=menu.admin_main_settings())

    if call.data == 'admin_catalogs':
        await bot.send_message(chat_id=chat_id, text='⚙️ Настройка каталогов', reply_markup=menu.admin_catalogs())

    if call.data == 'admin_subdirectories':
        await bot.send_message(chat_id=chat_id, text='⚙️ Настройка каталогов', reply_markup=menu.admin_subdirectories())

    if call.data == 'admin_products':
        await bot.send_message(chat_id=chat_id, text='⚙️ Настройка продуктов', reply_markup=menu.admin_products())

    if call.data == 'admin_subdirectory_add':
        markup = await Catalog().get_menu_add_subdirectory()
        await bot.send_message(chat_id=chat_id, text='Выбирите каталог в который хотите добавть товар',
                               reply_markup=markup)

    if call.data.split(':')[0] == 'add_subdirectory':
        await AdminAddSubdirectory.name.set()

        async with state.proxy() as data:
            data['catalog_id'] = call.data.split(':')[1]

        await bot.send_message(chat_id=chat_id, text='Введите название подкаталога')

    if call.data == 'back_to_admin_menu':
        await bot.send_message(chat_id=chat_id, text='Меню админа', reply_markup=menu.admin_menu())

    if call.data == 'admin_catalog_add':
        await AdminCatalogAdd.name.set()
        await bot.send_message(chat_id=chat_id, text='Введите название каталога')

    if call.data == 'admin_catalog_del':
        markup = await Catalog().get_menu_del_catalogs()
        await bot.send_message(chat_id=chat_id, text='Выбирите каталог который хотите удалить', reply_markup=markup)

    if call.data == 'admin_subdirectory_del':
        markup = await Catalog().get_menu_del_subdirectory()
        await bot.send_message(chat_id=chat_id, text='Выбирите подкаталог', reply_markup=markup)

    if call.data.split(':')[0] == 'del_subdirectory':
        await AdminDelSubdirectory.confirm.set()

        async with state.proxy() as data:
            data['subdirectory_id'] = call.data.split(':')[1]

        await bot.send_message(chat_id=chat_id, text='Для подтверждения удаления подкаталога отправьте +')

    if call.data.split(':')[0] == 'del_catalog':
        await AdminCatalogDel.confirm.set()

        async with state.proxy() as data:
            data['catalog_id'] = call.data.split(':')[1]

        await bot.send_message(chat_id=chat_id, text='Для подтверждения удаления каталога отправьте +')

    if call.data == 'admin_product_add':
        markup = await Catalog().get_menu_add_product()
        await bot.send_message(chat_id=chat_id, text='Выбирите каталог в который хотите добавть товар',
                               reply_markup=markup)

    if call.data.split(':')[0] == 'add_product_catalog':
        product = Product()
        await product.get_all_subdirectory_in_catalog(call.data.split(':')[1])

        if await Catalog().check_subdirectory_in_catalog(product.subdirectories):
            markup = await Catalog().get_menu_add_product_choosing(call.data.split(':')[1])
            await bot.send_message(chat_id=chat_id, text='В каталоге есть подкаталоги, выбирите дальнейшие действия',
                                   reply_markup=markup)
        else:
            await AdminAddProduct.name.set()

            async with state.proxy() as data:
                data['catalog_id'] = call.data.split(':')[1]

                await bot.send_message(chat_id=chat_id, text='Введите название товара')

    if call.data.split(':')[0] == 'add_product_get_menu_subdirectory':
        product = Product()
        await product.get_all_subdirectory_in_catalog(call.data.split(':')[1])

        markup = await Catalog().get_menu_add_product_subdirectory(product.subdirectories)
        await bot.send_message(chat_id=chat_id, text='Выбирите подкаталог в который хотите добавть товар',
                               reply_markup=markup)

    if call.data.split(':')[0] == 'add_product_in_subdirectory':
        await AdminAddProduct.name.set()

        async with state.proxy() as data:
            data['catalog_id'] = call.data.split(':')[1]

            await bot.send_message(chat_id=chat_id, text='Введите название товара')

    if call.data.split(':')[0] == 'add_product_in_catalog':
        await AdminAddProduct.name.set()

        async with state.proxy() as data:
            data['catalog_id'] = call.data.split(':')[1]

            await bot.send_message(chat_id=chat_id, text='Введите название товара')

    if call.data == 'admin_product_del':
        markup = await Catalog().get_menu_del_product()
        await bot.send_message(chat_id=chat_id, text='Выбирите каталог в котором хотите удалить товар',
                               reply_markup=markup)

    if call.data.split(':')[0] == 'del_product_menu':
        markup = await Product().get_menu_del_product(call.data.split(':')[1])

        product = Product()
        await product.get_all_subdirectory_in_catalog(call.data.split(':')[1])

        if await Catalog().check_subdirectory_in_catalog(product.subdirectories):
            markup.add(types.InlineKeyboardButton(text='💫 ПОДКАТАЛОГИ 💫',
                                                  callback_data=f'del_product_menu_subdirectory:{call.data.split(":")[1]}'))

        await bot.send_message(chat_id=chat_id, text='Выбирите товар который хотите удалить',
                               reply_markup=markup)

    if call.data.split(':')[0] == 'del_product_menu_subdirectory':
        product = Product()
        await product.get_all_subdirectory_in_catalog(call.data.split(':')[1])

        markup = await Catalog().get_menu_del_product(product.subdirectories)

        await bot.send_message(chat_id=chat_id, text='Выбирите подкаталог',
                               reply_markup=markup)

    if call.data.split(':')[0] == 'del_product_menu_2_subdirectory':
        markup = await Product().get_menu_del_product_subdirectories(call.data.split(':')[1])

        await bot.send_message(chat_id=chat_id, text='Выбирите товар который хотите удалить',
                               reply_markup=markup)

    if call.data.split(':')[0] == 'del_product':
        await AdminDelProduct.confirm.set()

        async with state.proxy() as data:
            data['product_id'] = call.data.split(':')[1]
            data['catalog_id'] = call.data.split(':')[2]

            await bot.send_message(chat_id=chat_id, text='Для подтверждения отправьте +')

    if call.data == 'admin_product_upload':
        markup = await Catalog().get_menu_upload_product()
        await bot.send_message(chat_id=chat_id, text='Выбирите каталог', reply_markup=markup)

    if call.data.split(':')[0] == 'upload_catalog':
        markup = await Product().get_menu_upload_product(call.data.split(':')[1])

        product = Product()
        await product.get_all_subdirectory_in_catalog(call.data.split(':')[1])

        if await Catalog().check_subdirectory_in_catalog(product.subdirectories):
            markup.add(types.InlineKeyboardButton(text='💫 ПОДКАТАЛОГИ 💫',
                                                  callback_data=f'upload_subdirectory:{call.data.split(":")[1]}'))

        await bot.send_message(chat_id=chat_id, text='Выбирите товар', reply_markup=markup)

    if call.data.split(':')[0] == 'upload_subdirectory':
        markup = await Product().get_menu_upload_subdirectory(call.data.split(':')[1])
        await bot.send_message(chat_id=chat_id, text='Выбирите подкаталог', reply_markup=markup)

    if call.data.split(':')[0] == 'get_menu_upload_subdirectory':
        markup = await Product().get_menu_upload_product(catalog_id=call.data.split(':')[1],
                                                         subdirectory_id=call.data.split(':')[1])
        await bot.send_message(chat_id=chat_id, text='Выбирите товар', reply_markup=markup)

    if call.data.split(':')[0] == 'upload_product':
        await AdminUploadProduct.upload.set()

        async with state.proxy() as data:
            data['product_id'] = call.data.split(':')[1]
            data['catalog_id'] = call.data.split(':')[2]

        await bot.send_message(chat_id=chat_id, text='Отправьте файл с товаром\n\n1 строка = 1 товар')

    await bot.answer_callback_query(call.id)


@dp.message_handler(state=AdminAddSubdirectory.name)
async def admin_subdirectory_add_name(message: types.Message, state: FSMContext):
    chat_id = message.chat.id

    async with state.proxy() as data:
        data['name'] = message.text

    await AdminAddSubdirectory.next()
    await bot.send_message(chat_id=chat_id, text='Отправьте фото подкаталога')


@dp.message_handler(state=AdminAddSubdirectory.photo, content_types=['photo'])
async def admin_subdirectory_add_photo(message: types.Message, state: FSMContext):
    chat_id = message.chat.id
    try:
        file_name = f'photos/subdirectory_{random.randint(0, 9999)}.jpg'
        await message.photo[-1].download(file_name)

        async with state.proxy() as data:
            name = data['name']
            catalog_id = data['catalog_id']

            await Catalog().create_subdirectory(catalog_id, name, file_name)

            await message.answer('✅ Подкаталог создан')

        await state.finish()
    except:
        await state.finish()
        await message.answer('ERROR')


@dp.message_handler(state=AdminUploadProduct.upload, content_types=['document'])
async def admin_upload(message: types.Message, state: FSMContext):
    try:
        file_name = f'docs/upload_{random.randint(0, 999999999999999)}.txt'
        await message.document.download(file_name)

        async with state.proxy() as data:
            data['file_name'] = file_name

        await AdminUploadProduct.next()
        await message.answer('Для подтверждения загрузки отправьте +')
    except:
        await state.finish()
        await  message.answer('Ошибка загрузки, принемаются только файлы')


@dp.message_handler(state=AdminUploadProduct.confirm)
async def admin_upload_confirm(message: types.Message, state: FSMContext):
    if message.text == '+':
        async with state.proxy() as data:
            data = await Product().upload_product(data['product_id'], data['file_name'])

            await message.answer(f'❕ Вы успешно загрузили товар\n\n✅ Успешно загружено строк: {data[0]}\n❌ Строк с ошибками: {data[1]}')
    else:
        await message.answer('Вы отменили загрузку товара')

    await state.finish()


@dp.message_handler(state=AdminDelProduct.confirm)
async def admin_del_product_confirm(message: types.Message, state: FSMContext):
    if message.text == '+':
        async with state.proxy() as data:
            await Product().del_product(data['product_id'], data['catalog_id'])

            await message.answer('Вы успешно удалили товар')
    else:
        await message.answer('Вы отменили удаление')

    await state.finish()

@dp.message_handler(state=AdminAddProduct.name)
async def admin_add_product_name(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['name'] = message.text

        await AdminAddProduct.next()

        await message.answer('Введите описание товара')


@dp.message_handler(state=AdminAddProduct.name)
async def admin_add_product_name(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['name'] = message.text

        await AdminAddProduct.next()

        await message.answer('Введите описание товара')


@dp.message_handler(state=AdminAddProduct.description)
async def admin_add_product_description(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['description'] = message.text

        await AdminAddProduct.next()

        await message.answer('Введите цену товара')


@dp.message_handler(state=AdminAddProduct.price)
async def admin_add_product_price(message: types.Message, state: FSMContext):
    try:
        async with state.proxy() as data:
            data['price'] = float(message.text)

            await AdminAddProduct.next()

            await message.answer(f"""
НАЗВАНИЕ: {data['name']}

ОПИСАНИЕ: {data['description']}

ЦЕНА: {data['price']} руб

Для подтверждения создания отправьте +
            """)

    except:
        await state.finish()
        await message.answer('Неверная цена')


@dp.message_handler(state=AdminAddProduct.confirm)
async def admin_add_product_confirm(message: types.Message, state: FSMContext):
    if message.text == '+':
        async with state.proxy() as data:
            await Product().create_product(
                data['catalog_id'],
                data['name'],
                data['description'],
                data['price']
            )

            await message.answer('Вы успешно добавили товар')
    else:
        await message.answer('Создание отменено')

    await state.finish()

@dp.message_handler(state=AdminCatalogDel.confirm)
async def admin_catalog_del(message: types.Message, state: FSMContext):
    if message.text == '+':
        async with state.proxy() as data:
            await Catalog().del_catalog(data['catalog_id'])

            await message.answer('Вы успешно удалили каталог')
    else:
        await message.answer('Удаление каталога отменено')

    await state.finish()


@dp.message_handler(state=AdminCatalogAdd.name)
async def admin_catalog_add_name(message: types.Message, state: FSMContext):
    chat_id = message.chat.id

    async with state.proxy() as data:
        data['name'] = message.text

    await AdminCatalogAdd.next()
    await bot.send_message(chat_id=chat_id, text='Отправьте фото каталога')


@dp.message_handler(state=AdminCatalogAdd.photo, content_types=['photo'])
async def admin_catalog_add_photo(message: types.Message, state: FSMContext):
    chat_id = message.chat.id
    try:
        file_name = f'photos/catalog_{random.randint(0, 9999)}.jpg'
        await message.photo[-1].download(file_name)

        async with state.proxy() as data:
            name = data['name']


            await Catalog().create_catalog(name, file_name)

            await message.answer('✅ Каталог создан')

        await state.finish()
    except:
        await state.finish()
        await message.answer('ERROR')

@dp.message_handler(state=Pay.confirm)
async def pay_confirm(message: types.Message, state: FSMContext):
    chat_id = message.chat.id

    if message.text == '+':
        user = User(chat_id)
        product = Product()

        async with state.proxy() as data:
            if data['price'] <= user.balance:
                await product.get_amount_products(data['product_id'])

                if data['amount'] <= product.amount_products:
                    user.update_balance(-data['price'])

                    file_name = await product.get_products(data['product_id'], data['amount'])

                    with open(file_name, 'r', encoding='UTF-8') as txt:
                        await message.answer('Ожидайте загрузку товара')

                        await bot.send_document(chat_id=chat_id, document=txt)

                    await product.purchases_log(file_name, chat_id, data['price'], data['amount'])
                else:
                    await message.answer('❕ Товара в таком количестве больше нет')
            else:
                await message.answer('Пополните баланс')
    else:
        await message.answer('Покупка отменена')

    await state.finish()

@dp.message_handler(state=Admin_give_balance.user_id)
async def admin_give_balance_1(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['user_id'] = message.text

    await Admin_give_balance.next()
    await message.answer('Введите сумму на которую будет изменен баланс')


@dp.message_handler(state=Admin_give_balance.balance)
async def admin_give_balance_2(message: types.Message, state: FSMContext):
    try:
        async with state.proxy() as data:
            data['balance'] = float(message.text)

            await Admin_give_balance.next()
            await message.answer(f"""
ID: {data['user_id']}
Баланс изменится на: {data['balance']}

Для подтверждения отправьте +
""")
    except:
        await state.finish()
        await message.answer('⚠️ ERROR ⚠️')


@dp.message_handler(state=Admin_give_balance.confirm)
async def admin_give_balance_3(message: types.Message, state: FSMContext):
    if message.text == '+':
        async with state.proxy() as data:
            func.give_balance(data)

            await bot.send_message(chat_id=message.chat.id, text='✅ Баланс успешно изменен', reply_markup=menu.admin_menu())
    else:
        await message.answer('⚠️ Изменение баланса отменено')

    await state.finish()


@dp.message_handler(state=Email_sending_photo.photo, content_types=['photo'])
async def email_sending_photo_1(message: types.Message, state: FSMContext):
    try:
        async with state.proxy() as data:
            data['photo'] = random.randint(111111111, 999999999)

        await message.photo[-1].download(f'photos/{data["photo"]}.jpg')
        await Email_sending_photo.next()
        await message.answer('Введите текст рассылки')
    except:
        await state.finish()
        await message.answer('⚠️ ERROR ⚠️')


@dp.message_handler(state=Email_sending_photo.text)
async def email_sending_photo_2(message: types.Message, state: FSMContext):
    try:
        async with state.proxy() as data:
            data['text'] = message.text

            with open(f'photos/{data["photo"]}.jpg', 'rb') as photo:
                await message.answer_photo(photo, data['text'])

            await Email_sending_photo.next()
            await message.answer('Выбирите дальнейшее действие', reply_markup=menu.admin_sending())
    except:
        await state.finish()
        await message.answer('⚠️ ERROR ⚠️')


@dp.message_handler(state=Email_sending_photo.action)
async def email_sending_photo_3(message: types.Message, state: FSMContext):
    chat_id = message.chat.id
    try:
        if message.text in menu.admin_sending_btn:
            if message.text == menu.admin_sending_btn[0]:  # Начать

                users = func.get_users_list()

                start_time = time.time()
                amount_message = 0
                amount_bad = 0
                async with state.proxy() as data:
                    photo_name = data["photo"]
                    text = data["text"]

                await state.finish()

                try:
                    m = await bot.send_message(
                        chat_id=config.config('admin_id_manager').split(':')[0],
                        text=f'✅ Рассылка в процессе',
                        reply_markup=menu.admin_sending_info(0, 0, 0))
                    msg_id = m['message_id']
                except:
                    pass

                for i in range(len(users)):
                    try:
                        with open(f'photos/{photo_name}.jpg', 'rb') as photo:
                            await bot.send_photo(
                                chat_id=users[i][0],
                                photo=photo,
                                caption=text,
                                reply_markup=menu.to_close
                            )
                        amount_message += 1
                    except Exception as e:
                        amount_bad += 1


                try:
                    await bot.edit_message_text(chat_id=config.config('admin_id_manager').split(':')[0],
                                                message_id=msg_id,
                                                text='✅ Рассылка завершена',
                                                reply_markup=menu.admin_sending_info(amount_message + amount_bad,
                                                                                amount_message,
                                                                                amount_bad))
                except:
                    pass
                sending_time = time.time() - start_time

                try:
                    await bot.send_message(
                        chat_id=config.config('admin_id_manager').split(':')[0],
                        text=f'✅ Рассылка окончена\n'
                             f'👍 Отправлено: {amount_message}\n'
                             f'👎 Не отправлено: {amount_bad}\n'
                             f'🕐 Время выполнения рассылки - {sending_time} секунд'

                    )
                except:
                    pass

            elif message.text == menu.admin_sending_btn[1]:  # Отложить
                await Email_sending_photo.next()

                await bot.send_message(
                    chat_id=chat_id,
                    text="""
Введите дату начала рассылке в формате: ГОД-МЕСЯЦ-ДЕНЬ ЧАСЫ:МИНУТЫ

Например 2020-09-13 02:28 - рассылка будет сделана 13 числа в 2:28
"""
            )

            elif message.text == menu.admin_sending_btn[2]:
                await state.finish()

                await bot.send_message(
                    message.chat.id,
                    text='Рассылка отменена',
                    reply_markup=menu.main_menu()
                )

                await bot.send_message(
                    message.chat.id,
                    text='Меню админа',
                    reply_markup=menu.admin_menu()
                )
        else:
            await bot.send_message(
                message.chat.id,
                text='Не верная команда, повторите попытку',
                reply_markup=menu.admin_sending())

    except Exception as e:
        await state.finish()
        await bot.send_message(
            chat_id=message.chat.id,
            text='⚠️ ERROR ⚠️'
        )


@dp.message_handler(state=Email_sending_photo.set_down_sending)
async def email_sending_photo_4(message: types.Message, state: FSMContext):
    try:
        async with state.proxy() as data:
            data['date'] = message.text
            date = datetime.fromisoformat(data['date'])

            await Email_sending_photo.next()

            await bot.send_message(
                chat_id=message.chat.id,
                text=f'Для подтверждения рассылки в {date} отправьте +'
            )
    except:
        await state.finish()
        await message.answer('⚠️ ERROR ⚠️')


@dp.message_handler(state=Email_sending_photo.set_down_sending_confirm)
async def email_sending_photo_5(message: types.Message, state: FSMContext):
    if message.text == '+':
        async with state.proxy() as data:
            data['type_sending'] = 'photo'

            func.add_sending(data)

            await bot.send_message(
                chat_id=message.chat.id,
                text=f'Рассылка запланирована в {data["date"]}',
                reply_markup=menu.admin_menu()
            )
    else:
        bot.send_message(message.chat.id, text='Рассылка отменена', reply_markup=menu.admin_menu())

    await state.finish()


@dp.message_handler(state=Admin_sending_messages.text)
async def admin_sending_messages_1(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['text'] = message.text

        await message.answer(data['text'])

        await Admin_sending_messages.next()
        await bot.send_message(
            chat_id=message.chat.id,
            text='Выбирите дальнейшее действие',
            reply_markup=menu.admin_sending()
        )


@dp.message_handler(state=Admin_sending_messages.action)
async def admin_sending_messages_2(message: types.Message, state: FSMContext):
    chat_id = message.chat.id

    if message.text in menu.admin_sending_btn:
        if message.text == menu.admin_sending_btn[0]:  # Начать

            users = func.get_users_list()

            start_time = time.time()
            amount_message = 0
            amount_bad = 0

            async with state.proxy() as data:
                text = data['text']

            await state.finish()

            try:
                m = await bot.send_message(
                    chat_id=config.config('admin_id_manager').split(':')[0],
                    text=f'✅ Рассылка в процессе',
                    reply_markup=menu.admin_sending_info(0, 0, 0))
                msg_id = m['message_id']
            except Exception as e:
                traceback.print_exc(e)

            for i in range(len(users)):
                try:
                    await bot.send_message(users[i][0], text, reply_markup=menu.to_close)
                    amount_message += 1
                except Exception as e:
                    amount_bad += 1


            try:
                await bot.edit_message_text(chat_id=config.config('admin_id_manager').split(':')[0],
                                            message_id=msg_id,
                                            text='✅ Рассылка завершена',
                                            reply_markup=menu.admin_sending_info(amount_message + amount_bad,
                                                                            amount_message,
                                                                            amount_bad))
            except:
                pass

            sending_time = time.time() - start_time

            try:
                await bot.send_message(
                    chat_id=config.config('admin_id_manager').split(':')[0],
                    text=f'✅ Рассылка окончена\n'
                         f'👍 Отправлено: {amount_message}\n'
                         f'👎 Не отправлено: {amount_bad}\n'
                         f'🕐 Время выполнения рассылки - {sending_time} секунд'

                )
            except:
                print('ERROR ADMIN SENDING')

        elif message.text == menu.admin_sending_btn[1]:  # Отложить
            await Admin_sending_messages.next()

            await bot.send_message(
                chat_id=chat_id,
                text="""
Введите дату начала рассылке в формате: ГОД-МЕСЯЦ-ДЕНЬ ЧАСЫ:МИНУТЫ

Например 2020-09-13 02:28 - рассылка будет сделана 13 числа в 2:28
"""
            )

        elif message.text == menu.admin_sending_btn[2]:
            await bot.send_message(
                message.chat.id,
                text='Рассылка отменена',
                reply_markup=menu.main_menu()
            )
            await bot.send_message(
                message.chat.id,
                text='Меню админа',
                reply_markup=menu.admin_menu()
            )
            await state.finish()
        else:
            await bot.send_message(
                message.chat.id,
                text='Не верная команда, повторите попытку',
                reply_markup=menu.admin_sending())


@dp.message_handler(state=Admin_sending_messages.set_down_sending)
async def admin_sending_messages_3(message: types.Message, state: FSMContext):
    try:
        async with state.proxy() as data:
            data['date'] = message.text
            date = datetime.fromisoformat(data['date'])

            await Admin_sending_messages.next()

            await bot.send_message(
                chat_id=message.chat.id,
                text=f'Для подтверждения рассылки в {date} отправьте +'
            )
    except:
        await state.finish()
        await message.answer('⚠️ ERROR ⚠️')


@dp.message_handler(state=Admin_sending_messages.set_down_sending_confirm)
async def admin_sending_messages_4(message: types.Message, state: FSMContext):
    if message.text == '+':
        async with state.proxy() as data:
            data['type_sending'] = 'text'
            data['photo'] = random.randint(111111, 9999999)

            func.add_sending(data)

            await bot.send_message(
                chat_id=message.chat.id,
                text=f'Рассылка запланирована в {data["date"]}',
                reply_markup=menu.admin_menu()
            )
    else:
        bot.send_message(message.chat.id, text='Рассылка отменена', reply_markup=menu.admin_menu())

    await state.finish()


@dp.message_handler(state=Admin_create_cupons.admin_create_cupons, content_types=['document'])
async def admin_create_cupons(message: types.Message, state: FSMContext):
    try:
        file_name = f'docs/promo_{random.randint(0, 999999999999999)}.txt'
        await message.document.download(file_name)
        await message.answer('Загружаем....')
        func.admin_add_cupons(message.caption, file_name)
        await message.answer('Купон добавлен, название: ' + message.text.split("\n")[0], reply_markup=menu.admin_menu())
    except Exception as e:
        print(e)
        await message.answer('Купон добавлен, название: ' + message.text.split("\n")[0], reply_markup=menu.admin_menu())
        await state.finish()
        




@dp.message_handler(state=Activate_promocode.activate_promocode)
async def activate_promocode(message: types.Message, state: FSMContext):
    try:
        answer = func.activate_promocode(message.text,message.chat.id)
        await message.answer(answer)
        await state.finish()
    except Exception as e:
        print(e)
        await state.finish()


@dp.message_handler(state=Admin_buttons.admin_buttons_del)
async def admin_buttons_del(message: types.Message, state: FSMContext):
    try:
        func.admin_del_btn(message.text)

        await message.answer('Кнопка удалена', reply_markup=menu.admin_menu())
        await state.finish()
    except Exception as e:
        await state.finish()
        await message.answer('⚠️ ERROR ⚠️')


@dp.message_handler(state=Admin_buttons.admin_buttons_add)
async def admin_buttons_add(message: types.Message, state: FSMContext):
    try:
        async with state.proxy() as data:
            data['name'] = message.text

        await Admin_buttons.next()
        await message.answer('Введите текст кнопки')

    except Exception as e:
        await state.finish()
        await message.answer('⚠️ ERROR ⚠️')


@dp.message_handler(state=Admin_buttons.admin_buttons_add_text)
async def admin_buttons_add_text(message: types.Message, state: FSMContext):
    try:
        async with state.proxy() as data:
            data['text'] = message.text

        await Admin_buttons.next()
        await message.answer('Отправьте фото для кнопки')

    except Exception as e:
        await state.finish()
        await message.answer('⚠️ ERROR ⚠️')


@dp.message_handler(state=Admin_buttons.admin_buttons_add_photo, content_types=['photo'])
async def admin_buttons_add_photo(message: types.Message, state: FSMContext):
    try:
        async with state.proxy() as data:
            data['photo'] = random.randint(111111111, 999999999)

        await message.photo[-1].download(f'photos/{data["photo"]}.jpg')

        with open(f'photos/{data["photo"]}.jpg', 'rb') as photo:
            await message.answer_photo(photo, data['text'])

        await Admin_buttons.next()
        await message.answer('Для создания кнопки напишите +')

    except Exception as e:
        await state.finish()
        await message.answer('⚠️ ERROR ⚠️')


@dp.message_handler(state=Admin_buttons.admin_buttons_add_confirm)
async def admin_buttons_add_confirm(message: types.Message, state: FSMContext):
    if message.text == '+':
        async with state.proxy() as data:
            func.admin_add_btn(data["name"], data["text"], data["photo"])

            await message.answer('Кнопка создана', reply_markup=menu.admin_menu())
    else:
        await message.answer('Создание кнопки отменено')

    await state.finish()


@dp.message_handler(state=AdminDelSubdirectory.confirm)
async def admin_subdirectory_del(message: types.Message, state: FSMContext):
    if message.text == '+':
        async with state.proxy() as data:
            await Catalog().del_subdirectory(data['subdirectory_id'])

            await message.answer('Вы успешно удалили подкаталог')
    else:
        await message.answer('Удаление каталога отменено')

    await state.finish()



async def sending_check(wait_for):
    while True:
        await asyncio.sleep(wait_for)

        try:
            info = func.sending_check()

            if info != False:
                users = func.get_users_list()

                start_time = time.time()
                amount_message = 0
                amount_bad = 0

                if info[0] == 'text':
                    try:
                        m = await bot.send_message(
                            chat_id=config.config('admin_id_manager').split(':')[0],
                            text=f'✅ Рассылка в процессе',
                            reply_markup=menu.admin_sending_info(0, 0, 0))
                        msg_id = m['message_id']
                    except:
                        pass

                    for i in range(len(users)):
                        try:
                            await bot.send_message(users[i][0], info[1], reply_markup=menu.to_close)
                            amount_message += 1
                        except Exception as e:
                            amount_bad += 1


                    try:
                        await bot.edit_message_text(chat_id=config.config('admin_id_manager').split(':')[0],
                                                    message_id=msg_id,
                                                    text='✅ Рассылка завершена',
                                                    reply_markup=menu.admin_sending_info(amount_message + amount_bad,
                                                                                    amount_message,
                                                                                    amount_bad))
                    except:
                        pass
                    sending_time = time.time() - start_time

                    try:
                        await bot.send_message(
                            chat_id=config.config('admin_id_manager').split(':')[0],
                            text=f'✅ Рассылка окончена\n'
                                 f'👍 Отправлено: {amount_message}\n'
                                 f'👎 Не отправлено: {amount_bad}\n'
                                 f'🕐 Время выполнения рассылки - {sending_time} секунд'

                        )
                    except:
                        print('ERROR ADMIN SENDING')

                elif info[0] == 'photo':
                    try:
                        m = await bot.send_message(
                            chat_id=config.config('admin_id_manager').split(':')[0],
                            text=f'✅ Рассылка в процессе',
                            reply_markup=menu.admin_sendingadmin_sending_info)
                        msg_id = m['message_id']
                    except:
                        pass

                    for i in range(len(users)):
                        try:
                            with open(f'photos/{info[2]}.jpg', 'rb') as photo:
                                await bot.send_photo(
                                    chat_id=users[i][0],
                                    photo=photo,
                                    caption=info[1],
                                    reply_markup=menu.to_close
                                )
                            amount_message += 1
                        except:
                            amount_bad += 1

                    try:
                        await bot.edit_message_text(chat_id=config.config('admin_id_manager').split(':')[0],
                                                    message_id=msg_id,
                                                    text='✅ Рассылка завершена',
                                                    reply_markup=menu.admin_sending_info(amount_message + amount_bad,
                                                                                    amount_message,
                                                                                    amount_bad))
                    except:
                        pass

                    sending_time = time.time() - start_time

                    try:
                        await bot.send_message(
                            chat_id=config.config('admin_id_manager').split(':')[0],
                            text=f'✅ Рассылка окончена\n'
                                 f'👍 Отправлено: {amount_message}\n'
                                 f'👎 Не отправлено: {amount_bad}\n'
                                 f'🕐 Время выполнения рассылки - {sending_time} секунд'

                        )
                    except:
                        print('ERROR ADMIN SENDING')

            else:
                pass
        except Exception as e:
            traceback.print_exc(e)


async def check_qiwi(wait_for):
    while True:
        try:
            data = func.get_payments_history()
            payment_code_list = func.get_list_payments_code()

            for i in range(len(data)):
                for j in payment_code_list:
                    if time.time() - float(j[2]) > 3600:
                        func.del_purchase_ticket(j[0])
                    elif data[i]['comment'] == j[1]:
                        if str(data[i]['sum']['currency']) == '643':
                            deposit = float(data[i]["sum"]["amount"])
                            func.del_purchase_ticket(j[0])
                            
                            User(j[0]).update_balance(deposit)
                            try:
                                User(j[0]).give_ref_reward(float(deposit))
                            except:
                                print('pizdos2')

                            

                            conn, cursor = connect()

                            try:
                                cursor.execute(
                                    f'INSERT INTO deposit_logs VALUES ("{j[0]}", "qiwi", "{deposit}", "{datetime.now()}")')
                                conn.commit()
                            except Exception as e:
                                print('e2 ')

                            try:
                                chat = User(j[0])
                                await bot.send_message(chat_id=config.config('channel_id_main_logs'), text=texts.logs.format(
                                    'QIWI',
                                    chat.first_name,
                                    f'@{chat.username}',
                                    j[0],
                                    datetime.now(),
                                    f'❕ Кошелек: +{data[i]["personId"]}\n❕ Комментарий: {data[i]["comment"]}',
                                    deposit
                                ))
                            except Exception as e:
                                print('e 3')

                            try:
                                await bot.send_message(
                                    chat_id=j[0],
                                    text=f'✅ Вам зачислено +{deposit}'
                                )
                            except Exception as e:
                                pass

        except Exception as e:
            pass

        await asyncio.sleep(wait_for)


async def check_payouts(wait_for):
    while True:
        try:
            await asyncio.sleep(wait_for)

            conn, cursor = connect()

            cursor.execute(f'SELECT * FROM payouts')
            payouts = cursor.fetchall()

            if len(payouts) > 0:
                for i in payouts:
                    if i[1] == 'bad':
                        cursor.execute(f'DELETE FROM payouts WHERE user_id = "{i[0]}"')
                        conn.commit()

                        await bot.send_message(chat_id=i[0], text=f'✅ Ваш чек проверен, на ваш баланс начислено 0 ₽',
                                               reply_markup=menu.to_close)
                    else:
                        cursor.execute(f'DELETE FROM payouts WHERE user_id = "{i[0]}"')
                        conn.commit()

                        User(i[0]).update_balance(i[1])
                        try:
                            User(i[0]).give_ref_reward(float(i[1]))
                        except:
                            print('pizdos')     
                        await bot.send_message(chat_id=i[0],
                                               text=f'✅ Ваш чек проверен, на ваш баланс начислено +{i[1]} ₽',
                                               reply_markup=menu.to_close)
                        
                        try:
                            await bot.send_message(chat_id=config.config('channel_id_main_logs'), text=texts.logs.format(
                                'BANKER',
                                User(i[0]).first_name,
                                User(i[0]).username,
                                i[0],
                                datetime.now(),
                                f'❕ Чек: {i[2]}',
                                i[1]
                            ))
                        except:
                            pass
        except:
            pass



if __name__ == '__main__':
    threading.Thread(target=btc.check_btc).start()

    loop = asyncio.get_event_loop()
    
    loop.create_task(sending_check(10))
    loop.create_task(check_payouts(5))
    loop.create_task(check_qiwi(10))

    executor.start_polling(dp, skip_updates=True)
