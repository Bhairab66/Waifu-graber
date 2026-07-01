import aiohttp
from pymongo import ReturnDocument

from telegram import Update
from telegram.ext import CommandHandler, CallbackContext

from shivu import application, sudo_users, collection, db, CHARA_CHANNEL_ID, SUPPORT_CHAT

WRONG_FORMAT_TEXT = """Wrong ❌️ format...

<b>Option 1</b> — Send image URL:
<code>/upload img_url | Character Name | Anime Name | rarity</code>

<b>Option 2</b> — Reply to a photo:
<code>/upload Character Name | Anime Name | rarity</code>

<b>Rarity map:</b>
1 ⚪ Common  |  2 🟣 Rare  |  3 🟡 Legendary  |  4 🟢 Medium

<b>Example:</b>
<code>/upload https://i.imgur.com/abc.jpg | Itachi Uchiha | Naruto | 3</code>"""

RARITY_MAP = {
    1: "⚪ Common",
    2: "🟣 Rare",
    3: "🟡 Legendary",
    4: "🟢 Medium"
}


async def get_next_sequence_number(sequence_name):
    sequence_collection = db.sequences
    sequence_document = await sequence_collection.find_one_and_update(
        {'_id': sequence_name},
        {'$inc': {'sequence_value': 1}},
        return_document=ReturnDocument.AFTER
    )
    if not sequence_document:
        await sequence_collection.insert_one({'_id': sequence_name, 'sequence_value': 0})
        return 0
    return sequence_document['sequence_value']


async def resolve_url(url: str) -> str:
    """Follow redirects and return the final URL."""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, allow_redirects=True, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                return str(resp.url)
    except Exception:
        return url


async def upload(update: Update, context: CallbackContext) -> None:
    if str(update.effective_user.id) not in sudo_users:
        await update.message.reply_text('Ask My Owner...')
        return

    try:
        raw = ' '.join(context.args)
        parts = [p.strip() for p in raw.split('|')]

        img_url = None
        reply_photo = update.message.reply_to_message

        # Option 2: reply to a photo — /upload Name | Anime | rarity
        if reply_photo and reply_photo.photo:
            if len(parts) != 3:
                await update.message.reply_text(WRONG_FORMAT_TEXT, parse_mode='HTML')
                return
            character_name_raw, anime_raw, rarity_raw = parts
            photo_file = await reply_photo.photo[-1].get_file()
            img_url = photo_file.file_path

        # Option 1: URL provided — /upload url | Name | Anime | rarity
        else:
            if len(parts) != 4:
                await update.message.reply_text(WRONG_FORMAT_TEXT, parse_mode='HTML')
                return
            url_raw, character_name_raw, anime_raw, rarity_raw = parts
            img_url = await resolve_url(url_raw.strip())

        character_name = character_name_raw.strip().title()
        anime = anime_raw.strip().title()

        try:
            rarity = RARITY_MAP[int(rarity_raw.strip())]
        except (KeyError, ValueError):
            await update.message.reply_text(
                '❌ Invalid rarity. Use: 1 (Common), 2 (Rare), 3 (Legendary), 4 (Medium)',
                parse_mode='HTML'
            )
            return

        char_id = str(await get_next_sequence_number('character_id')).zfill(2)

        character = {
            'img_url': img_url,
            'name': character_name,
            'anime': anime,
            'rarity': rarity,
            'id': char_id
        }

        try:
            message = await context.bot.send_photo(
                chat_id=CHARA_CHANNEL_ID,
                photo=img_url,
                caption=(
                    f'<b>Character Name:</b> {character_name}\n'
                    f'<b>Anime Name:</b> {anime}\n'
                    f'<b>Rarity:</b> {rarity}\n'
                    f'<b>ID:</b> {char_id}\n'
                    f'Added by <a href="tg://user?id={update.effective_user.id}">{update.effective_user.first_name}</a>'
                ),
                parse_mode='HTML'
            )
            character['message_id'] = message.message_id
        except Exception:
            pass

        await collection.insert_one(character)
        await update.message.reply_text(
            f'✅ <b>Character Added!</b>\n\n'
            f'📛 <b>Name:</b> {character_name}\n'
            f'🎭 <b>Anime:</b> {anime}\n'
            f'✨ <b>Rarity:</b> {rarity}\n'
            f'🆔 <b>ID:</b> {char_id}',
            parse_mode='HTML'
        )

    except Exception as e:
        await update.message.reply_text(
            f'❌ Upload failed: {str(e)}\n\nContact support: {SUPPORT_CHAT}'
        )


async def delete(update: Update, context: CallbackContext) -> None:
    if str(update.effective_user.id) not in sudo_users:
        await update.message.reply_text('Ask my Owner to use this Command...')
        return

    try:
        args = context.args
        if len(args) != 1:
            await update.message.reply_text('Incorrect format... Please use: /delete ID')
            return

        character = await collection.find_one_and_delete({'id': args[0]})

        if character:
            try:
                await context.bot.delete_message(chat_id=CHARA_CHANNEL_ID, message_id=character['message_id'])
            except Exception:
                pass
            await update.message.reply_text('✅ Character deleted successfully.')
        else:
            await update.message.reply_text('❌ Character not found with that ID.')
    except Exception as e:
        await update.message.reply_text(f'Error: {str(e)}')


async def update_character(update: Update, context: CallbackContext) -> None:
    if str(update.effective_user.id) not in sudo_users:
        await update.message.reply_text('You do not have permission to use this command.')
        return

    try:
        args = context.args
        if len(args) < 3:
            await update.message.reply_text('Incorrect format. Please use: /update id field new_value')
            return

        char_id = args[0]
        field = args[1]
        new_value_raw = ' '.join(args[2:])

        character = await collection.find_one({'id': char_id})
        if not character:
            await update.message.reply_text('❌ Character not found.')
            return

        valid_fields = ['img_url', 'name', 'anime', 'rarity']
        if field not in valid_fields:
            await update.message.reply_text(f'Invalid field. Use one of: {", ".join(valid_fields)}')
            return

        if field in ['name', 'anime']:
            new_value = new_value_raw.title()
        elif field == 'rarity':
            try:
                new_value = RARITY_MAP[int(new_value_raw)]
            except (KeyError, ValueError):
                await update.message.reply_text('Invalid rarity. Use 1, 2, 3, or 4.')
                return
        else:
            new_value = new_value_raw

        await collection.find_one_and_update({'id': char_id}, {'$set': {field: new_value}})

        if field == 'img_url':
            try:
                await context.bot.delete_message(chat_id=CHARA_CHANNEL_ID, message_id=character['message_id'])
                message = await context.bot.send_photo(
                    chat_id=CHARA_CHANNEL_ID,
                    photo=new_value,
                    caption=(
                        f'<b>Character Name:</b> {character["name"]}\n'
                        f'<b>Anime Name:</b> {character["anime"]}\n'
                        f'<b>Rarity:</b> {character["rarity"]}\n'
                        f'<b>ID:</b> {character["id"]}\n'
                        f'Updated by <a href="tg://user?id={update.effective_user.id}">{update.effective_user.first_name}</a>'
                    ),
                    parse_mode='HTML'
                )
                await collection.find_one_and_update({'id': char_id}, {'$set': {'message_id': message.message_id}})
            except Exception:
                pass
        else:
            try:
                await context.bot.edit_message_caption(
                    chat_id=CHARA_CHANNEL_ID,
                    message_id=character['message_id'],
                    caption=(
                        f'<b>Character Name:</b> {character["name"]}\n'
                        f'<b>Anime Name:</b> {character["anime"]}\n'
                        f'<b>Rarity:</b> {character["rarity"]}\n'
                        f'<b>ID:</b> {character["id"]}\n'
                        f'Updated by <a href="tg://user?id={update.effective_user.id}">{update.effective_user.first_name}</a>'
                    ),
                    parse_mode='HTML'
                )
            except Exception:
                pass

        await update.message.reply_text(f'✅ Character <b>{char_id}</b> updated: <b>{field}</b> → <code>{new_value}</code>', parse_mode='HTML')

    except Exception as e:
        await update.message.reply_text(f'❌ Update failed: {str(e)}')


application.add_handler(CommandHandler('upload', upload, block=False))
application.add_handler(CommandHandler('delete', delete, block=False))
application.add_handler(CommandHandler('update', update_character, block=False))
