import time
from datetime import datetime, timezone

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext, CommandHandler, CallbackQueryHandler

import shivu
from shivu import (application, collection, user_collection, pm_users,
                   top_global_groups_collection, group_user_totals_collection,
                   sudo_users_collection, OWNER_ID)

BOT_START_TIME = time.time()


def get_uptime() -> str:
    seconds = int(time.time() - BOT_START_TIME)
    hours, remainder = divmod(seconds, 3600)
    minutes, secs = divmod(remainder, 60)
    return f"{hours}h {minutes}m {secs}s"


async def admin(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id

    if str(user_id) not in shivu.sudo_users and str(user_id) != str(OWNER_ID):
        await update.message.reply_text("❌ This command is only for admins/GMs.")
        return

    total_characters = await collection.count_documents({})
    total_users = await user_collection.count_documents({})
    total_pm_users = await pm_users.count_documents({})
    total_groups = len(await top_global_groups_collection.distinct("group_id"))
    total_gms = len(shivu.sudo_users)

    is_owner = str(user_id) == str(OWNER_ID)

    text = (
        f"🛡️ <b>Admin Panel</b>\n"
        f"{'👑 You are the Owner' if is_owner else '⭐ You are a GM'}\n\n"
        f"📊 <b>Bot Statistics</b>\n"
        f"├ 🎴 Characters in DB: <b>{total_characters}</b>\n"
        f"├ 👥 Total Users: <b>{total_users}</b>\n"
        f"├ 💬 PM Users: <b>{total_pm_users}</b>\n"
        f"├ 🌐 Total Groups: <b>{total_groups}</b>\n"
        f"├ ⭐ GMs: <b>{total_gms}</b>\n"
        f"└ ⏱️ Uptime: <b>{get_uptime()}</b>\n"
    )

    keyboard = []
    if is_owner:
        keyboard = [
            [
                InlineKeyboardButton("📋 GM List", callback_data="admin_gmlist"),
                InlineKeyboardButton("📢 Broadcast", callback_data="admin_broadcast_info"),
            ],
            [
                InlineKeyboardButton("📁 Export Users", callback_data="admin_export_users"),
                InlineKeyboardButton("📁 Export Groups", callback_data="admin_export_groups"),
            ],
        ]
    else:
        keyboard = [
            [InlineKeyboardButton("🔄 Refresh Stats", callback_data="admin_refresh")],
        ]

    reply_markup = InlineKeyboardMarkup(keyboard) if keyboard else None
    await update.message.reply_text(text, parse_mode="HTML", reply_markup=reply_markup)


async def admin_callback(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    user_id = query.from_user.id

    if str(user_id) not in shivu.sudo_users and str(user_id) != str(OWNER_ID):
        await query.answer("❌ Not authorized.", show_alert=True)
        return

    await query.answer()

    if query.data == "admin_refresh":
        total_characters = await collection.count_documents({})
        total_users = await user_collection.count_documents({})
        total_pm_users = await pm_users.count_documents({})
        total_groups = len(await top_global_groups_collection.distinct("group_id"))
        total_gms = len(shivu.sudo_users)
        is_owner = str(user_id) == str(OWNER_ID)

        text = (
            f"🛡️ <b>Admin Panel</b>\n"
            f"{'👑 You are the Owner' if is_owner else '⭐ You are a GM'}\n\n"
            f"📊 <b>Bot Statistics</b>\n"
            f"├ 🎴 Characters in DB: <b>{total_characters}</b>\n"
            f"├ 👥 Total Users: <b>{total_users}</b>\n"
            f"├ 💬 PM Users: <b>{total_pm_users}</b>\n"
            f"├ 🌐 Total Groups: <b>{total_groups}</b>\n"
            f"├ ⭐ GMs: <b>{total_gms}</b>\n"
            f"└ ⏱️ Uptime: <b>{get_uptime()}</b>\n"
        )
        keyboard = [[InlineKeyboardButton("🔄 Refresh Stats", callback_data="admin_refresh")]]
        await query.edit_message_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data == "admin_gmlist":
        if not shivu.sudo_users:
            await query.edit_message_text("No GMs found.", parse_mode="HTML")
            return
        gm_list = "\n".join([f"• <code>{uid}</code>" for uid in shivu.sudo_users])
        keyboard = [[InlineKeyboardButton("⬅️ Back", callback_data="admin_back")]]
        await query.edit_message_text(
            f"👑 <b>GM List:</b>\n{gm_list}",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    elif query.data == "admin_broadcast_info":
        keyboard = [[InlineKeyboardButton("⬅️ Back", callback_data="admin_back")]]
        await query.edit_message_text(
            "📢 <b>Broadcast</b>\n\nReply to any message with /broadcast to forward it to all users and groups.",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    elif query.data in ("admin_export_users", "admin_export_groups"):
        keyboard = [[InlineKeyboardButton("⬅️ Back", callback_data="admin_back")]]
        cmd = "/list" if query.data == "admin_export_users" else "/groups"
        await query.edit_message_text(
            f"📁 Use <code>{cmd}</code> in PM to export the file.",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    elif query.data == "admin_back":
        total_characters = await collection.count_documents({})
        total_users = await user_collection.count_documents({})
        total_pm_users = await pm_users.count_documents({})
        total_groups = len(await top_global_groups_collection.distinct("group_id"))
        total_gms = len(shivu.sudo_users)
        is_owner = str(user_id) == str(OWNER_ID)

        text = (
            f"🛡️ <b>Admin Panel</b>\n"
            f"{'👑 You are the Owner' if is_owner else '⭐ You are a GM'}\n\n"
            f"📊 <b>Bot Statistics</b>\n"
            f"├ 🎴 Characters in DB: <b>{total_characters}</b>\n"
            f"├ 👥 Total Users: <b>{total_users}</b>\n"
            f"├ 💬 PM Users: <b>{total_pm_users}</b>\n"
            f"├ 🌐 Total Groups: <b>{total_groups}</b>\n"
            f"├ ⭐ GMs: <b>{total_gms}</b>\n"
            f"└ ⏱️ Uptime: <b>{get_uptime()}</b>\n"
        )
        keyboard = [
            [
                InlineKeyboardButton("📋 GM List", callback_data="admin_gmlist"),
                InlineKeyboardButton("📢 Broadcast", callback_data="admin_broadcast_info"),
            ],
            [
                InlineKeyboardButton("📁 Export Users", callback_data="admin_export_users"),
                InlineKeyboardButton("📁 Export Groups", callback_data="admin_export_groups"),
            ],
        ]
        await query.edit_message_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))


application.add_handler(CommandHandler("admin", admin, block=False))
application.add_handler(CallbackQueryHandler(admin_callback, pattern="^admin_", block=False))
