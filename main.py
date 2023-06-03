import time
import random
import json
import os
#import keep_alive
from aiogram import Dispatcher, Bot, types, executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, BotCommand, ChatMember
import asyncio
import logging
import aiofiles

BOT_TOKEN = "6230729020:AAGYqxDdbBaUIE7kbvHRhBMLECbuKamCwAs"
SAVE_FILENAME = "save.txt"
DEFAULT_SCAN_DELAY = 1

delay_sec_between_msgs = 3

users = {}

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)


async def save_data():
    """ old realisation
    file = open(SAVE_FILENAME, "w")
    file.write(json.dumps(users))
    file.close()
    """

    async with aiofiles.open(SAVE_FILENAME, mode='w') as f:
        await f.write(json.dumps(users))

    print(users)
    print(json.dumps(users))
    print("added")


async def add_data(key: str, id):
    added = True
    if key in users.keys():
        find = False
        for i in users[key][1::]:
            if id == i[0]:
                find = True
                break
        if not find:
            users[key] += [[id, 0]]
            await save_data()
        else:
            added = False
    else:
        users[key] = [-1, [id, 0]]
        await save_data()
    return added


def check_time(key):
    canScan = False
    if users[key][0] == -1 or time.time() - users[key][0] >= DEFAULT_SCAN_DELAY:
        canScan = True
        users[key][0] = time.time()
    return canScan


async def get_mention(message: types.Message, id=-1):
    if id == -1:
        id = message.from_user.id
    info = await bot.get_chat_member(chat_id=message.chat.id, user_id=id)
    if "username" in info.user.iter_keys():
        name = info.user.username
    else:
        name = info.user.first_name
    return "[" + name + "](tg://user?id=" + str(id) + ")"


def wipe(chat_id: str):
    if chat_id in users.keys():
        users[chat_id][0] = -1
        for i in users[chat_id][1::]:
            i[1] = 0
        return True
    else:
        return False


async def get_top(msg: types.Message):
    chat_id = str(msg.chat.id)
    _list = sorted(users[chat_id][1::], key=lambda x: x[1])[::-1]
    """
    ln = 10
    if len(_list) < 10:
        ln = len(_list)
    """
    res_str = ""
    # for i in range(ln): old
    for i in range(len(_list)):
        """
        info = await bot.get_chat_member(chat_id=msg.chat.id, user_id=_list[i][0])
        if "username" in info.user.iter_keys():
            name = info.user.username
        else:
            name = info.user.first_name
        mention = get_mention(msg.chat.id, _list[i][0])
        """
        mention = await get_mention(msg, _list[i][0])
        res_str += f"{i+1}. {mention} - {_list[i][1]} раз(а)\n"
    return res_str[:len(res_str) - 1]


async def set_commands(bot: Bot):
    commands = [
        BotCommand(command="/addme", description="стать участником"),
        BotCommand(command="/gaybomba", description="найти гомосека"),
        BotCommand(command="/top", description="топ пидоров"),
        BotCommand(command="/wipe", description="вайп топа (для админов)"),
    ]
    await bot.set_my_commands(commands)


async def main():

    dp = Dispatcher(bot=bot, storage=MemoryStorage())

    await set_commands(bot)

    register_common_handlers(dp)
    register_game_handlers(dp)

    #keep_alive.keep_alive()
    await dp.start_polling()


async def handle_welcome(message: types.Message):
    if message.chat.type == 'group' or message.chat.type == 'supergroup':
        await message.reply(
            "Ну че фраерочки, вот и я до вас добрался!\n\n"
            "Скажите спасибо, что живы еще, но это пока нахуй. Дальше только хуже."
            "\n\n"
            "Моя задача на вас - каждый день напоминать, кто тут по фамилии табуретка\n\n"
            "Напишите /gaybomba, и я мигом посажу одного из вас на бутылку, уебки"
            "\n\n"
            "/top - топ опущенных в этой группе"
            "\n\n"
            "/wipe - очистить топ пидоров (для админов чата)")
        await asyncio.sleep(1)
        await bot.send_message(
            message.chat.id,
            text="Все, кто хочет участвовать в этом мракобесье - \n"
            "напишите сюда команду: \n"
            "/addme")
        #await asyncio.sleep(1)
        #await bot.send_message(message.chat.id, text=f"/start {message.chat.id} ")
    elif message.from_user:
        pass
        """
        text = message.text.split()
        #print(text)
        if len(text) == 2 and text[1][1::].isdigit():
            print(text[1])
            if await add_data(text[1], message.from_user.id):
                await message.reply("Ну все, ты добавлен. \n\n\n\n\n\nНу ты и еблан, конечно)))ы")
            else:
                await message.reply("Ты и так уже зареган, дурашка")
        else:
            await message.reply("Ты мне какую-то хуйню прислал."
                                "\nПеределывай, балда ебаная")
        """


async def handle_adding_player(message: types.Message):
    if message.chat.type == 'group' or message.chat.type == 'supergroup':
        if await add_data(str(message.chat.id), message.from_user.id):
            await bot.send_message(message.chat.id,
                                   text="Еще один добавился...")
        else:
            mention = await get_mention(message)
            await bot.send_message(
                message.chat.id,
                text="{0}, ты и так уже есть, дурень".format(mention),
                parse_mode="Markdown")


async def handle_wipe(message: types.Message):
    if message.chat.type == 'group' or message.chat.type == 'supergroup':
        info = await bot.get_chat_member(chat_id=message.chat.id,
                                         user_id=message.from_user.id)
        if info.is_chat_admin():
            if wipe(str(message.chat.id)):
                await bot.send_message(message.chat.id,
                                       text="Вайп прошел успешно")
            else:
                await bot.send_message(
                    message.chat.id,
                    text="Какая-то хуйня с вайпом. Мб участников нет")


async def tell_gay(message: types.Message, player_id: int):
    mention = await get_mention(message, player_id)
    await bot.send_message(message.chat.id,
                           text="Ищу фраерочка на вечерочек...")
    await asyncio.sleep(delay_sec_between_msgs)
    await bot.send_message(message.chat.id,
                           text="Пидарок найден: {0}".format(mention),
                           parse_mode="Markdown")


async def handle_find_gay(message: types.Message):
    print(message.chat.type)
    if message.chat.type == 'group' or message.chat.type == 'supergroup':
        msgid = str(message.chat.id)
        await add_data(str(message.chat.id), message.from_user.id)
        #if msgid in users.keys():
        print(msgid)
        if len(users[msgid]) > 2:
            if check_time(msgid):
                list_id = random.randint(1, len(users[msgid]) - 1)
                #player = users[msgid][random.randint(1, len(users[msgid]) - 1)]
                #print(player)
                users[msgid][list_id][1] += 1  #player[1] += 1
                #users[msgid][player]
                coro_objs = [
                    save_data(),
                    tell_gay(message, users[msgid][list_id][0])
                ]
                await asyncio.gather(*coro_objs)
            else:
                diff = users[msgid][0] + DEFAULT_SCAN_DELAY - time.time()
                hours = diff // 3600
                mins = (diff - hours * 3600) // 60
                secs = diff - mins * 60 - hours * 3600
                if hours == 0 and mins == 0:
                    await bot.send_message(
                        message.chat.id,
                        text=
                        f"Следующий запрос будет доступен через {int(secs)} "
                        f"сек ")
                else:
                    await bot.send_message(
                        message.chat.id,
                        text=
                        f"Следующий запрос будет доступен через {int(hours)} "
                        f"ч "
                        f"{int(mins)} мин")
        else:
            await bot.send_message(
                message.chat.id,
                text="Аче игрок-то всего один???!!!\n"
                "Нечего одного гонять по кругу. Добавляйтесь еще:\n"
                "/addme")  # ЗАМЕНИТЬ НА КОМАНДУ ДЛЯ ДОБАВЛЕНИЯ!!!
            #await asyncio.sleep(1)
            #await bot.send_message(message.chat.id, text=f"/start {message.chat.id}")
        """
        else:
            await bot.send_message(message.chat.id, text="А хули никто не написал мне в личку???!!!\n\n"
                                                         "А ну ка скинули мне - "
                                                         "@gaypredictor_bot")
            await asyncio.sleep(1)
            await bot.send_message(message.chat.id, text=f"/start {message.chat.id}")
        """


async def handle_top(message: types.Message):
    if message.chat.type == 'group' or message.chat.type == 'supergroup':
        msgid = str(message.chat.id)
        if msgid in users.keys():
            if len(users[msgid]) > 2:
                res_txt = await get_top(message)
                await bot.send_message(message.chat.id,
                                       text=f"Топ пидоров:\n{res_txt}",
                                       parse_mode="Markdown")
            else:
                await bot.send_message(
                    message.chat.id,
                    text=
                    "Да у вас участников-то недостаточно, дебики.\nДобавляйтесь нахуй все -\n/addme")
        else:
            await bot.send_message(
                message.chat.id,
                text="Никто, блять, не добавился в эту залупу.\nА ну-ка в темпе вальса написали сюда /addme\nЖИВО ЕПТА")


def register_common_handlers(dp: Dispatcher):
    dp.register_message_handler(handle_welcome, commands=["start"])


def register_game_handlers(dp: Dispatcher):
    dp.register_message_handler(handle_adding_player, commands=["addme"])
    dp.register_message_handler(handle_wipe, commands=["wipe"])
    dp.register_message_handler(handle_find_gay, commands=["gaybomba"])
    dp.register_message_handler(handle_top, commands=["top"])


if __name__ == '__main__':
    with open(SAVE_FILENAME, "r") as file:
        data = file.readline()
    if data != "":
        users = json.loads(data)
        print(users)
    asyncio.run(main())
