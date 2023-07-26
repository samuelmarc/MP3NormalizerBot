from config import Config
import logging
from motor.motor_asyncio import AsyncIOMotorClient


print("Connecting to the database...")


mgclient = AsyncIOMotorClient(Config.MONGO_URI)
db = mgclient.mp3gain
users_col = db.users


print("Database connected...")


async def get_vol(user_id: int):
    '''
    :param user_id: the user_id of user
    :return: returns the volume defined by the user, if the user is not registered, one is created with the defined volume pattern and in the pt-br language
    '''
    user = await users_col.find_one({'user_id': user_id})
    if user:
        return user['vol']
    else:
        await users_col.insert_one({'user_id': user_id, 'lang': 'pt-br', 'vol': Config.DEFAULT_VOL})
        return Config.DEFAULT_VOL


async def get_user_lang(user_id: int):
    '''
    :param user_id: the user_id of user
    :return: returns the language defined by the user, if the user is not registered, one is created with the defined volume pattern and in the pt-br language
    '''
    user = await users_col.find_one({'user_id': user_id})
    if user:
        return user['lang']
    else:
        await users_col.insert_one({'user_id': user_id, 'lang': 'pt-br', 'vol': Config.DEFAULT_VOL})
        return "pt-br"
