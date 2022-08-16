import datetime

admin_spam_dict = {}
class AdminSpam:
    def __init__(self, user_id):
        self.user_id = user_id
        self.date = []
        self.status = True
        self.ban_date = None


async def test(data, bot):
    try:
        admin_spam_dict[data.from_user.id]
    except KeyError:
        admin = AdminSpam(data.from_user.id)
        admin_spam_dict[data.from_user.id] = admin

    admin = admin_spam_dict[data.from_user.id]

    if admin.status is False:
        if datetime.datetime.now() - admin.ban_date > datetime.timedelta(seconds=10):
            admin.status = True
            return True
        else:
            return False

    admin.date.append(data.date)

    if len(admin.date) > 3:
        del admin.date[0]

    if len(admin.date) >= 3:
        if admin.date[2] - admin.date[0] < datetime.timedelta(seconds=1.5):
            admin.status = False
            admin.ban_date = datetime.datetime.now()

            try:
                await bot.send_message(data.from_user.id, text='❌ Вы забанены на 10 секунд!\n❕ Причина: SPAM')
            except:
                pass

            return False
        return True
    else:
        return True
