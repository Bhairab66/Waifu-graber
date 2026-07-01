import random
from datetime import datetime, timezone

from telegram import Update
from telegram.ext import CallbackContext, CommandHandler

from shivu import application, collection, user_collection, db

claim_collection = db['daily_claims']

COOLDOWN_HOURS = 24


async def claim(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
    first_name = update.effective_user.first_name
    username = update.effective_user.username

    now = datetime.now(timezone.utc)

    claim_data = await claim_collection.find_one({"user_id": user_id})

    if claim_data:
        last_claim = claim_data["last_claim"]
        if last_claim.tzinfo is None:
            last_claim = last_claim.replace(tzinfo=timezone.utc)
        diff = (now - last_claim).total_seconds()
        remaining = COOLDOWN_HOURS * 3600 - diff

        if remaining > 0:
            hours = int(remaining // 3600)
            minutes = int((remaining % 3600) // 60)
            await update.message.reply_text(
                f"⏳ You already claimed today!\n\nCome back in <b>{hours}h {minutes}m</b> for your next free character.",
                parse_mode="HTML"
            )
            return

    all_characters = await collection.find({}).to_list(length=None)

    if not all_characters:
        await update.message.reply_text("❌ No characters available to claim right now. Try again later.")
        return

    character = random.choice(all_characters)

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

    await claim_collection.update_one(
        {"user_id": user_id},
        {"$set": {"last_claim": now}},
        upsert=True
    )

    await update.message.reply_photo(
        photo=character["img_url"],
        caption=(
            f"🎁 <b>Daily Claim!</b>\n\n"
            f"<a href='tg://user?id={user_id}'>{first_name}</a> received a free character!\n\n"
            f"📛 <b>Name:</b> {character['name']}\n"
            f"🎭 <b>Anime:</b> {character['anime']}\n"
            f"✨ <b>Rarity:</b> {character['rarity']}\n\n"
            f"Use /harem to see your collection.\n"
            f"⏳ Next claim available in <b>{COOLDOWN_HOURS} hours</b>."
        ),
        parse_mode="HTML"
    )


application.add_handler(CommandHandler("claim", claim, block=False))
