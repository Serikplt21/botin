from aiogram.dispatcher.filters.state import State, StatesGroup


class Admin_give_balance(StatesGroup):
    user_id = State()
    balance = State()
    confirm = State()


class Email_sending_photo(StatesGroup):
    photo = State()
    text = State()
    action = State()
    set_down_sending = State()
    set_down_sending_confirm = State()


class Admin_sending_messages(StatesGroup):
    text = State()
    action = State()
    set_down_sending = State()
    set_down_sending_confirm = State()


class Admin_buttons(StatesGroup):
    admin_buttons_del = State()
    admin_buttons_add = State()
    admin_buttons_add_text = State()
    admin_buttons_add_photo = State()
    admin_buttons_add_confirm = State()

class Admin_create_cupons(StatesGroup):
    admin_create_cupons = State()


class Activate_promocode(StatesGroup):
    activate_promocode = State()

class Buy(StatesGroup):
    confirm = State()


class Admin_product_upload(StatesGroup):
    download = State()
    confirm = State()


class Pay(StatesGroup):
    confirm = State()


class AdminCatalogAdd(StatesGroup):
    name = State()
    photo = State()


class AdminCatalogDel(StatesGroup):
    confirm = State()


class AdminAddProduct(StatesGroup):
    name = State()
    description = State()
    price = State()
    confirm = State()


class AdminDelProduct(StatesGroup):
    confirm = State()


class AdminUploadProduct(StatesGroup):
    upload = State()
    confirm = State()


class AdminAddSubdirectory(StatesGroup):
    name = State()
    photo = State()


class AdminDelSubdirectory(StatesGroup):
    confirm = State()
