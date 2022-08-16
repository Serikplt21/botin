from utils.mydb import *
from utils.product import Product
from utils.user import User

from aiogram import types
from main import bot

import datetime
import random
import texts
import menu
import config
import requests
import json
import time
import sqlite3
import logging


buy_dict = {}

class Buy:
    def __init__(self, user_id):
        self.user_id = user_id
        self.product_code = None


def first_join(user_id, first_name, username, code):
    conn, cursor = connect()

    cursor.execute(f'SELECT * FROM users WHERE user_id = "{user_id}"')
    row = cursor.fetchall()
    who_invite = code[7:]

    if who_invite == '':
        who_invite = 0
    
    if len(row) == 0:
        sql = f'INSERT INTO users VALUES (%s, %s, %s, %s, %s, %s, %s)'
        cursor.execute(sql, (user_id, first_name, f"@{username}", '0', who_invite, datetime.datetime.now(), 'no'))
        conn.commit()

        return True, who_invite
        
    return False, 0


def check_in_bd(user_id):
    conn, cursor = connect()

    cursor.execute(f'SELECT * FROM users WHERE user_id = "{user_id}"')
    row = cursor.fetchall()

    if len(row) == 0:
        return False
    else:
        return True


def admin_info():
    conn, cursor = connect()

    cursor.execute(f'SELECT * FROM users')
    row = cursor.fetchall()

    d = datetime.timedelta(days=1)
    h = datetime.timedelta(hours=1)
    date = datetime.datetime.now()

    amount_user_all = 0
    amount_user_day = 0
    amount_user_hour = 0

    for i in row:
        amount_user_all += 1

        if date - datetime.datetime.fromisoformat(i[5]) <= d:
            amount_user_day += 1
        if date - datetime.datetime.fromisoformat(i[5]) <= h:
            amount_user_hour += 1

    cursor.execute(f'SELECT * FROM deposit_logs')
    row = cursor.fetchall()

    qiwi = 0
    all_qiwi = 0
    banker = 0
    all_banker = 0

    for i in row:
        if i[1] == 'qiwi':
            if date - datetime.datetime.fromisoformat(i[3]) <= d:
                qiwi += i[2]

            all_qiwi += i[2]

        elif i[1] == 'banker':
            if date - datetime.datetime.fromisoformat(i[3]) <= d:
                banker += i[2]

            all_banker += i[2]

    cursor.execute(f'SELECT * FROM purchase_logs')
    row = cursor.fetchall()

    purchase_all = 0
    purchase_day = 0
    purchase_hour = 0

    for i in row:
        purchase_all += 1

        if date - datetime.datetime.fromisoformat(i[4]) <= d:
            purchase_day += 1
        if date - datetime.datetime.fromisoformat(i[4]) <= h:
            purchase_hour += 1

    msg = f"""
❕ Информаци о пользователях:

❕ За все время - <b>{amount_user_all}</b>
❕ За день - <b>{amount_user_day}</b>
❕ За час - <b>{amount_user_hour}</b>

❕ Пополнений за 24 часа
❕ QIWI: <b>{qiwi} ₽</b>
❕ BANKER: <b>{banker} ₽</b>

⚠️ Ниже приведены данные за все время
❕ Пополнения QIWI: <b>{all_qiwi} ₽</b>
❕ Пополнения BANKER: <b>{all_banker} ₽</b>

❕ Покупок за все время - {purchase_all}
❕ Покупок за день - {purchase_day}
❕ Покупок за час - {purchase_hour}
"""

    return msg


def give_balance(dict):
    logging.info(f'{dict["user_id"]}/{User(dict["user_id"]).username} : balance - {User(dict["user_id"]).balance} : change balance: {dict["balance"]} rub')

    conn, cursor = connect()

    cursor.execute(f'UPDATE users SET balance = "{dict["balance"]}" WHERE user_id = "{dict["user_id"]}"')
    conn.commit()


def get_users_list():
    conn, cursor = connect()

    cursor.execute(f'SELECT * FROM users')
    users = cursor.fetchall()

    return users


def add_sending(info):
    conn, cursor = connect()

    cursor.execute(f'INSERT INTO sending VALUES ("{info["type_sending"]}", "{info["text"]}", "{info["photo"]}", "{info["date"]}")')
    conn.commit()


def sending_check():
    conn, cursor = connect()

    cursor.execute(f'SELECT * FROM sending')
    row = cursor.fetchall()

    for i in row:
        if float(i[3]) <= time.time():
            cursor.execute(f'DELETE FROM sending WHERE photo = "{i[2]}"')
            conn.commit()

            return i

    return False


def list_btns():
    conn, cursor = connect()

    cursor.execute(f'SELECT * FROM buttons')
    list_btn = cursor.fetchall()

    msg = ''

    for i in range(len(list_btn)):
        msg += f'№ {i} | {list_btn[i][0]}\n'

    return msg


def btn_menu_list():
    conn, cursor = connect()

    cursor.execute(f'SELECT * FROM buttons')
    base = cursor.fetchall()

    btn_list = []

    for i in base:
        btn_list.append(i[0])

    return btn_list

def admin_del_btn(value):
    conn, cursor = connect()

    cursor.execute(f'SELECT * FROM buttons')
    list_btn = cursor.fetchall()

    name = list_btn[int(value)][0]

    cursor.execute(f'DELETE FROM buttons WHERE name = "{name}"')
    conn.commit()


def admin_add_cupons(name,file_name):
    connection = sqlite3.connect('base_main.db')
    q = connection.cursor()


    try:
        with open(file_name, 'rb') as txt:
            cupons_id = random.randint(1,9999999999999999999)
            for i in txt.readlines():
                i = i.decode(errors='ignore')
                try:
                    q.execute("INSERT INTO coupons (id,name,log) VALUES ('%s','%s','%s')"%(cupons_id,name,i))
                    connection.commit()
                except Exception as e:
                    pass
    except Exception as e:
        pass



    # file = await bot.get_file(file_id)
    # file_path = file.file_path
    # await bot.download_file(file_path, "text.txt")
    # name = value.split('\n')[0]
    # text = value.split('\n')
    # cupons_id = random.randint(1,9999999999999999999)
    # del text[0]
    # for i in text:
        q.execute("INSERT INTO coupons (id,name,log) VALUES ('%s','%s','%s')"%(cupons_id,name,i))
        connection.commit()


def activate_promocode(value,userid):
    connection = sqlite3.connect('base_main.db')
    q = connection.cursor()
    q.execute(f'SELECT * FROM coupons where name = "{value}" and admin = 0 LIMIT 1')
    answer = q.fetchone()
    if answer != None:
        q.execute(f'SELECT admin FROM coupons where name = "{value}" and admin = "{userid}"')
        answer_user = q.fetchone()
        if answer_user == None:
            q.execute(f"update coupons set admin = '{userid}' where coupon_id = '{answer[0]}'")
            connection.commit()
            return f"🥳 Промокод успешно активирован, держи подарочек не забудь оставить отзыв !\n\n{answer[3]}"
        else:
            return f'Ты уже активировал этот промокод'

    else:
        return f'Такого промокода нет'



def admin_add_btn(name, info, photo):
    conn, cursor = connect()

    cursor.execute(f'INSERT INTO buttons VALUES ("{name}", "{info}", "{photo}")')
    conn.commit() 

def func_btcs():
    doc = open('config.cfg', 'rb')
    markup = menu.admin_menu()

    return doc, markup


async def pact(user_id):
    await bot.send_message(chat_id=user_id, text=texts.pact, reply_markup=menu.pact())


async def pact_accept(user_id):
    conn, cursor = connect()

    cursor.execute(f'UPDATE users SET pact = "yes" WHERE user_id = "{user_id}"')
    conn.commit()


def deposit_qiwi(user_id):
    conn, cursor = connect()

    cursor.execute(f'SELECT * FROM check_payment WHERE user_id = {user_id}')
    check = cursor.fetchall()
    if len(check) > 0:
        code = check[0][1]
        date = float(check[0][2])
    else:
        code = random.randint(11111, 99999)
        date = time.time()

        cursor.execute(f'INSERT INTO check_payment VALUES ("{user_id}", "{code}", "{date}")')
        conn.commit()


    url =  f'https://qiwi.com/payment/form/99?extra%5B%27account%27%5D={config.config("qiwi_number")}&amountFraction=0&extra%5B%27comment%27%5D={code}&currency=643&&blocked[0]=account&&blocked[1]=comment'

    markup = menu.payment_menu(url)

    return code, date, markup


def check_payment(user_id):
    try:
        session = requests.Session()
        session.headers['authorization'] = 'Bearer ' + config.config('qiwi_token')
        parameters = {'rows': '10'}
        h = session.get(
            'https://edge.qiwi.com/payment-history/v1/persons/{}/payments'.format(config.config("qiwi_token")),
            params=parameters)
        req = json.loads(h.text)

        cursor.execute(f'SELECT * FROM check_payment WHERE user_id = {user_id}')
        result = cursor.fetchone()

        comment = result[1]
        for i in range(len(req['data'])):
            if comment in str(req['data'][i]['comment']):
                if str(req['data'][i]['sum']['currency']) == '643':
                    deposit = float(req["data"][i]["sum"]["amount"])

                    User(user_id).update_balance(deposit)

                    # try:
                    #     cursor.execute(
                    #         f'INSERT INTO deposit_logs VALUES ("{user_id}", "qiwi", "{deposit}", "{datetime.datetime.now()}")')
                    #     conn.commit()
                    # except Exception as e:
                    #     print(f'DEPOSIT QIWI: {e}')
                    #
                    # try:
                    #     chat = User(user_id)
                    #     await bot.send_message(chat_id=config.config('CHANNEL_ID1'), text=texts.logs.format(
                    #         'QIWI',
                    #         chat.first_name,
                    #         f'@{chat.username}',
                    #         user_id,
                    #         datetime.datetime.now(),
                    #         f'❕ Кошелек: +{req["data"][i]["personId"]}\n❕ Комментарий: {req["data"][i]["comment"]}',
                    #         deposit
                    #     ))
                    # except:
                    #     pass

                    cursor.execute(f'DELETE FROM check_payment WHERE user_id = "{user_id}"')
                    conn.commit()

                    return True
    except:
        pass

    return False


def get_payments_history():
    session = requests.Session()
    session.headers['authorization'] = 'Bearer ' + config.config('qiwi_token')

    parameters = {'rows': '10'}

    h = session.get(
        'https://edge.qiwi.com/payment-history/v1/persons/{}/payments'.format(config.config("qiwi_number")),
        params=parameters
    )

    req = json.loads(h.text)

    return req['data']


def get_list_payments_code():
    conn, cursor = connect()

    cursor.execute(f'SELECT * FROM check_payment')
    check_payment = cursor.fetchall()

    return check_payment


def del_purchase_ticket(user_id):
    conn, cursor = connect()

    cursor.execute(f'DELETE FROM check_payment WHERE user_id = "{user_id}"')
    conn.commit()
