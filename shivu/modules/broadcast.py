from telegram import Update
from telegram.ext import CallbackContext, CommandHandler
from telegram.error import Forbidden, BadRequest

from shivu import application, top_global_groups_collection, pm_users, OWNER_ID


async def broadcast(update: Update, context: CallbackContext) -> None:
    if str(update.effective_user.id) != str(OWNER_ID):
        await update.message.reply_text("You are not authorized to use this command.")
        return

    message_to_broadcast = update.message.reply_to_message

    if message_to_broadcast is None:
        await update.message.reply_text(
            "⚠️ Please <b>reply to a message</b> with /broadcast to forward it.",
            parse_mode="HTML"
        )
        return

    status_msg = await update.message.reply_text("📢 Broadcasting... please wait.")

    all_chats = await top_global_groups_collection.distinct("group_id")
    all_users = await pm_users.distinct("_id")
    targets = list(set(all_chats + all_users))

    sent = 0
    failed = 0
    blocked = 0
    stale_removed = 0

    for chat_id in targets:
        try:
            await context.bot.forward_message(
                chat_id=chat_id,
                from_chat_id=message_to_broadcast.chat_id,
                message_id=message_to_broadcast.message_id
            )
            sent += 1
        except Forbidden:
            blocked += 1
            stale_removed += 1
            await pm_users.delete_one({"_id": chat_id})
            await top_global_groups_collection.delete_one({"group_id": chat_id})
        except BadRequest:
            failed += 1
            stale_removed += 1
            await pm_users.delete_one({"_id": chat_id})
            await top_global_groups_collection.delete_one({"group_id": chat_id})
        except Exception:
            failed += 1

    await status_msg.edit_text(
        f"📢 <b>Broadcast Complete!</b>\n\n"
        f"✅ Sent: <b>{sent}</b>\n"
        f"🚫 Blocked/Left: <b>{blocked}</b>\n"
        f"❌ Failed: <b>{failed}</b>\n"
        f"🗑️ Stale records cleaned: <b>{stale_removed}</b>\n\n"
        f"<i>Stale entries (old users/groups from before this bot) are removed automatically.</i>",
        parse_mode="HTML"
    )


application.add_handler(CommandHandler("broadcast", broadcast, block=False))
