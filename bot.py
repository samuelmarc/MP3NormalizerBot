from pyrogram import Client, filters
from pyrogram.types import Message, CallbackQuery
from pyrogram.enums import ParseMode
from config import Config
import logging
import database
import i18n
from pyroaddon.helpers import ikb
import os
from asyncio.exceptions import TimeoutError
import asyncio
from pydub import AudioSegment
import re


i18n.load_path.append('langs')
i18n.set('enable_memoization', True)
i18n.set('encoding', 'UTF-8')


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


async def _(lang: str, key: str, **kwargs):
    i18n.set('locale', lang)
    text_in_lang = i18n.t(f'langs.{key}', **kwargs)
    return text_in_lang


def audio_norm(path_file, vol):
    sound = AudioSegment.from_file(path_file)
    change_in_dBFS = vol - sound.dBFS
    norm_sound = sound.apply_gain(change_in_dBFS)
    norm_sound.export(path_file)
    return 1


mp3normalizer = Client(name='mp3normalizer', api_id=Config.API_ID, api_hash=Config.API_HASH, bot_token=Config.BOT_TOKEN, parse_mode=ParseMode.MARKDOWN)


async def progress(current: int, total: int, m, lang, key):
    div = current / total
    per = int(div * 100)
    text = await _(lang, key, progr=per)
    await m.edit(text)


async def settings_main(mc: Message or CallbackQuery):
    user_id = mc.from_user.id
    user_lang = await database.get_user_lang(user_id)
    _settings = await _(user_lang, 'settings')
    _lang_btn = await _(user_lang, 'set_lang_btn')
    _vol_btn = await _(user_lang, 'set_vol_btn')
    btns = ikb([
        [(_lang_btn, 'set_lang_main')],
        [(_vol_btn, 'set_vol')]
    ])
    if type(mc) == Message:
        await mc.reply(_settings, reply_markup=btns)
    elif type(mc) == CallbackQuery:
        await mc.edit_message_text(_settings, reply_markup=btns)


@mp3normalizer.on_message(filters.command("start") & filters.private)
async def start(__, m: Message):
    user_lang = await database.get_user_lang(m.from_user.id)
    text = await _(user_lang, 'start', user_mention=m.from_user.mention)
    await m.reply(text)


@mp3normalizer.on_message(filters.command("repository") & filters.private)
async def repo(__, m: Message):
    text = f"🗂 **Below you can access the bot's public repository.**"
    btn = ikb([[('🌐 Repository', 'https://github.com/samuelmarc/MP3NormalizerBot', 'url')]])
    await m.reply(text, reply_markup=btn)


@mp3normalizer.on_message(filters.audio & filters.private)
async def audio_normalizer(__, m: Message):
    vol = await database.get_vol(m.from_user.id)
    user_lang = await database.get_user_lang(m.from_user.id)
    text = await _(user_lang, 'down', progr='1')
    init_m = await m.reply(text)
    path_file = await m.download(progress=progress, progress_args=(init_m, user_lang, 'down'))
    text = await _(user_lang, 'def_vol')
    await init_m.edit(text)
    try:
        blocking_coro = asyncio.to_thread(audio_norm, path_file, vol)
        result = await blocking_coro
        await m.reply_audio(f"downloads/{m.audio.file_name}", progress=progress, progress_args=(init_m, user_lang, 'upl'))
        await init_m.delete()
        os.remove(path_file)
    except:
        if os.path.exists(path_file):
            os.remove(path_file)


@mp3normalizer.on_message(filters.command("settings") & filters.private)
async def settings(__, m: Message):
    await settings_main(mc=m)


@mp3normalizer.on_callback_query(filters.regex('settings_main'))
async def back_settings(__, call: CallbackQuery):
    await settings_main(mc=call)


@mp3normalizer.on_callback_query(filters.regex('set_lang_main'))
async def set_lang_main(__, call: CallbackQuery):
    user_lang = await database.get_user_lang(call.from_user.id)
    _set_lang_main = await _(user_lang, 'set_lang_main')
    _back_btn = await _(user_lang, 'back_btn')
    btns = ikb([
        [('🇧🇷 Português (Brasil)', 'set_lang=pt-br')],
        [('🇺🇸 English (United States)', 'set_lang=en-us')],
        [('🇪🇸 Español', 'set_lang=es')],
        [('🇫🇷 Français', 'set_lang=fr')],
        [(_back_btn, 'settings_main')]
    ])
    await call.edit_message_text(_set_lang_main, reply_markup=btns)


@mp3normalizer.on_callback_query(filters.regex('set_lang=(.+)'))
async def set_lang(__, call: CallbackQuery):
    user_id = call.from_user.id
    user_lang = await database.get_user_lang(user_id)
    new_lang = call.matches[0].group(1)
    if user_lang == new_lang:
        _same_lang = await _(user_lang, 'same_lang')
        await call.answer(_same_lang, show_alert=True)
    else:
        col = database.users_col
        await col.update_one({'user_id': user_id}, {'$set': {'lang': new_lang}})
        _lang_def = await _(new_lang, 'lang_def')
        await call.answer(_lang_def, show_alert=True)
        await settings_main(mc=call)


@mp3normalizer.on_callback_query(filters.regex('set_vol'))
async def set_vol(__, call: CallbackQuery):
    user_id = call.from_user.id
    user_lang = await database.get_user_lang(user_id)
    _vol_set = await _(user_lang, 'set_vol_main')
    try:
        now_vol = await call.message.chat.ask(_vol_set, filters=filters.text, timeout=30)
    except TimeoutError:
        _set_vol_es = await _(user_lang, 'set_vol_es')
        await call.message.reply(_set_vol_es)
        return
    now_vol = now_vol.text
    try:
        now_vol = float(now_vol)
    except:
        _num_not_valid = await _(user_lang, 'num_not_valid')
        await call.message.reply(_num_not_valid)
        return
    ac_vol = await database.get_vol(user_id)
    if now_vol == ac_vol:
        _num_vol_same = await _(user_lang, 'num_vol_same')
        await call.message.reply(_num_vol_same)
    else:
        col = database.users_col
        await col.update_one({'user_id': user_id}, {'$set': {'vol': now_vol}})
        _set_vol_sus = await _(user_lang, 'set_vol_sus')
        await call.message.reply(_set_vol_sus)


mp3normalizer.run()