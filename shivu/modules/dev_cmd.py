from telegram import Update
from telegram.ext import CallbackContext, CommandHandler

import shivu
from shivu import application, sudo_users_collection, OWNER_ID


async def addgm(update: Update, context: CallbackContext) -> None:
    if str(update.effective_user.id) != str(OWNER_ID):
        await update.message.reply_text("❌ Only the owner can add GMs.")
        return

    if not context.args:
        await update.message.reply_text("Usage: /addgm <user_id>")
        return

    user_id = context.args[0]

    if user_id in shivu.sudo_users:
        await update.message.reply_text(f"✅ {user_id} is already a GM.")
        return

    await sudo_users_collection.update_one(
        {"_id": "sudo_list"},
        {"$addToSet": {"users": user_id}},
        upsert=True
    )
    shivu.sudo_users.append(user_id)
    await update.message.reply_text(f"✅ {user_id} has been added as GM.\nThey can now use /upload, /delete, /ping and other sudo commands.")


async def removegm(update: Update, context: CallbackContext) -> None:
    if str(update.effective_user.id) != str(OWNER_ID):
        await update.message.reply_text("❌ Only the owner can remove GMs.")
        return

    if not context.args:
        await update.message.reply_text("Usage: /removegm <user_id>")
        return

    user_id = context.args[0]

    if str(user_id) == str(OWNER_ID):
        await update.message.reply_text("❌ Cannot remove the owner from GM list.")
        return

    if user_id not in shivu.sudo_users:
        await update.message.reply_text(f"❌ {user_id} is not a GM.")
        return

    await sudo_users_collection.update_one(
        {"_id": "sudo_list"},
        {"$pull": {"users": user_id}}
    )
    shivu.sudo_users.remove(user_id)
    await update.message.reply_text(f"✅ {user_id} has been removed from GM list.")


async def listgm(update: Update, context: CallbackContext) -> None:
    if str(update.effective_user.id) != str(OWNER_ID):
        await update.message.reply_text("❌ Only the owner can view the GM list.")
        return

    if not shivu.sudo_users:
        await update.message.reply_text("No GMs found.")
        return

    gm_list = "\n".join([f"• <code>{uid}</code>" for uid in shivu.sudo_users])
    await update.message.reply_text(f"<b>👑 GM List:</b>\n{gm_list}", parse_mode="HTML")


application.add_handler(CommandHandler("addgm", addgm, block=False))
application.add_handler(CommandHandler("removegm", removegm, block=False))
application.add_handler(CommandHandler("listgm", listgm, block=False))
