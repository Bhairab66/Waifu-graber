import random
from datetime import datetime, timezone
from html import escape

from telegram import Update
from telegram.ext import CallbackContext, CommandHandler

from shivu import application, collection, user_collection, db

claim_collection = db['daily_claims']
weekly_collection = db['weekly_claims']

DAILY_COOLDOWN_HOURS = 24
WEEKLY_COOLDOWN_HOURS = 168  # 7 days

RARITY_WEIGHTS = [
    ("⚪ Common",    40),
    ("🟢 Medium",    30),
    ("🟣 Rare",      20),
    ("🟡 Legendary", 10),
]

RARITY_LABELS = {
    "⚪ Common":    "⚪ Common    — 40% chance",
    "🟢 Medium":   "🟢 Medium    — 30% chance",
    "🟣 Rare":     "🟣 Rare      — 20% chance",
    "🟡 Legendary":"🟡 Legendary — 10% chance",
}


def weighted_rarity() -> str:
    rarities = [r for r, _ in RARITY_WEIGHTS]
    weights  = [w for _, w in RARITY_WEIGHTS]
    return random.choices(rarities, weights=weights, k=1)[0]


async def pick_character(all_characters: list, rarity: str):
    pool = [c for c in all_characters if c.get("rarity") == rarity]
    if pool:
        return random.choice(pool)
    return random.choice(all_characters)


def time_remaining_text(seconds: float) -> str:
    hours   = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    return f"{hours}h {minutes}m"


async def ensure_user(user_id, username, first_name, character):
    user = await user_collection.find_one({"id": user_id})
    if user:
        await user_collection.update_one({"id": user_id}, {"$push": {"characters": character}})
    else:
        await user_collection.insert_one({
            "id": user_id,
            "username": username,
            "first_name": first_name,
            "characters": [character],
        })


async def claim(update: Update, context: CallbackContext) -> None:
    user_id    = update.effective_user.id
    first_name = escape(update.effective_user.first_name)
    username   = update.effective_user.username
    now        = datetime.now(timezone.utc)

    data = await claim_collection.find_one({"user_id": user_id})
    if data:
        last = data["last_claim"]
        if last.tzinfo is None:
            last = last.replace(tzinfo=timezone.utc)
        remaining = DAILY_COOLDOWN_HOURS * 3600 - (now - last).total_seconds()
        if remaining > 0:
            await update.message.reply_text(
                f"⏳ <b>Already claimed today!</b>\n\n"
                f"Come back in <b>{time_remaining_text(remaining)}</b> for your next free character.\n\n"
                f"💡 Try /weekly for your weekly bonus!",
                parse_mode="HTML"
            )
            return

    all_characters = await collection.find({}).to_list(length=None)
    if not all_characters:
        await update.message.reply_text("❌ No characters in the database yet. Ask the owner to upload some!")
        return

    rarity    = weighted_rarity()
    character = await pick_character(all_characters, rarity)

    await ensure_user(user_id, username, update.effective_user.first_name, character)
    await claim_collection.update_one(
        {"user_id": user_id},
        {"$set": {"last_claim": now}},
        upsert=True
    )

    await update.message.reply_photo(
        photo=character["img_url"],
        caption=(
            f"🎁 <b>Daily Reward!</b>\n\n"
            f"<a href='tg://user?id={user_id}'>{first_name}</a> rolled the gacha!\n\n"
            f"📛 <b>Name:</b> {character['name']}\n"
            f"🎭 <b>Anime:</b> {character['anime']}\n"
            f"✨ <b>Rarity:</b> {character['rarity']}\n\n"
            f"<b>Drop Rates:</b>\n"
            f"⚪ Common — 40%  |  🟢 Medium — 30%\n"
            f"🟣 Rare — 20%  |  🟡 Legendary — 10%\n\n"
            f"⏳ Next daily in <b>24h</b> · Use /weekly for 3 bonus characters!"
        ),
        parse_mode="HTML"
    )


async def weekly(update: Update, context: CallbackContext) -> None:
    user_id    = update.effective_user.id
    first_name = escape(update.effective_user.first_name)
    username   = update.effective_user.username
    now        = datetime.now(timezone.utc)

    data = await weekly_collection.find_one({"user_id": user_id})
    if data:
        last = data["last_claim"]
        if last.tzinfo is None:
            last = last.replace(tzinfo=timezone.utc)
        remaining = WEEKLY_COOLDOWN_HOURS * 3600 - (now - last).total_seconds()
        if remaining > 0:
            days    = int(remaining // 86400)
            hours   = int((remaining % 86400) // 3600)
            minutes = int((remaining % 3600) // 60)
            await update.message.reply_text(
                f"⏳ <b>Weekly already claimed!</b>\n\n"
                f"Come back in <b>{days}d {hours}h {minutes}m</b> for your next weekly bonus.\n\n"
                f"💡 Don't forget your /claim every day!",
                parse_mode="HTML"
            )
            return

    all_characters = await collection.find({}).to_list(length=None)
    if not all_characters:
        await update.message.reply_text("❌ No characters in the database yet. Ask the owner to upload some!")
        return

    # Pick 3 characters with weighted rarity
    chosen = []
    for _ in range(3):
        rarity    = weighted_rarity()
        character = await pick_character(all_characters, rarity)
        chosen.append(character)
        await ensure_user(user_id, username, update.effective_user.first_name, character)

    await weekly_collection.update_one(
        {"user_id": user_id},
        {"$set": {"last_claim": now}},
        upsert=True
    )

    # Send each character as a photo, summary as last message
    for i, character in enumerate(chosen, 1):
        await update.message.reply_photo(
            photo=character["img_url"],
            caption=(
                f"🎀 <b>Weekly Reward — Character {i}/3</b>\n\n"
                f"📛 <b>Name:</b> {character['name']}\n"
                f"🎭 <b>Anime:</b> {character['anime']}\n"
                f"✨ <b>Rarity:</b> {character['rarity']}"
            ),
            parse_mode="HTML"
        )

    names = " · ".join([f"<b>{c['name']}</b>" for c in chosen])
    await update.message.reply_text(
        f"🎊 <b>Weekly Bonus Complete!</b>\n\n"
        f"<a href='tg://user?id={user_id}'>{first_name}</a> collected 3 characters:\n"
        f"{names}\n\n"
        f"<b>Drop Rates:</b>\n"
        f"⚪ Common — 40%  |  🟢 Medium — 30%\n"
        f"🟣 Rare — 20%  |  🟡 Legendary — 10%\n\n"
        f"⏳ Next weekly in <b>7 days</b> · Keep claiming daily too!",
        parse_mode="HTML"
    )


application.add_handler(CommandHandler("claim", claim, block=False))
application.add_handler(CommandHandler("weekly", weekly, block=False))
