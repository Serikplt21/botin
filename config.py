import configparser
import os
import time

path = 'config.cfg'

def create_config():

    config = configparser.ConfigParser()
    config.add_section("Settings")
    config.set("Settings", "bot_token", "token")
    config.set("Settings", "admin_id_own", "0:1")
    config.set("Settings", "admin_id_manager", "0:1")
    config.set("Settings", "channel_id_logs", "0")
    config.set("Settings", "channel_id_main_logs", "0")
    config.set("Settings", "qiwi_number", "0")
    config.set("Settings", "qiwi_token", "0")
    config.set("Settings", "bot_login", "bot_login")
    config.set("Settings", "ref_percent", "10")
    config.set("Settings", "channel_id", "-100")

    
    with open(path, "w") as config_file:
        config.write(config_file)


def check_config_file():
    if not os.path.exists(path):
        create_config()
        
        print('Config created')
        time.sleep(3)
        exit(0)


def config(what):
    
    config = configparser.ConfigParser()
    config.read(path)

    value = config.get("Settings", what)

    return value

check_config_file()