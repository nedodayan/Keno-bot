from aiogram import Router, types
from aiogram.filters import Command
from config import ADMIN_IDS
import database.db as db

admin_router = Router()

def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS

@admin_router.message(Command("addbalance"))
async def cmd_add_balance(message: types.Message):
    if not is_admin(message.from_user.id):
        return
    parts = message.text.split()
    if len(parts) != 3:
        await message.reply("Usage: `/addbalance <user_id> <amount>`")
        return
    try:
        user_id = int(parts[1])
        amount = float(parts[2])
        await db.update_balance(user_id, amount)
        await message.reply(f"✅ Added {amount:.2f} Birr to user `{user_id}`.")
    except ValueError:
        await message.reply("Invalid numbers provided.")

@admin_router.message(Command("removebalance"))
async def cmd_remove_balance(message: types.Message):
    if not is_admin(message.from_user.id):
        return
    parts = message.text.split()
    if len(parts) != 3:
        await message.reply("Usage: `/removebalance <user_id> <amount>`")
        return
    try:
        user_id = int(parts[1])
        amount = float(parts[2])
        await db.update_balance(user_id, -amount)
        await message.reply(f"✅ Deducted {amount:.2f} Birr from user `{user_id}`.")
    except ValueError:
        await message.reply("Invalid numbers.")

@admin_router.message(Command("setbalance"))
async def cmd_set_balance(message: types.Message):
    if not is_admin(message.from_user.id):
        return
    parts = message.text.split()
    if len(parts) != 3:
        await message.reply("Usage: `/setbalance <user_id> <amount>`")
        return
    try:
        user_id = int(parts[1])
        amount = float(parts[2])
        await db.set_balance(user_id, amount)
        await message.reply(f"✅ User `{user_id}` balance set to {amount:.2f} Birr.")
    except ValueError:
        await message.reply("Invalid input.")

@admin_router.message(Command("stats"))
async def cmd_stats(message: types.Message):
    if not is_admin(message.from_user.id):
        return
    stats = await db.get_global_stats()
    text = (
        "📊 **System Statistics**\n\n"
        f"• Total Registered Users: `{stats['total_users']}`\n"
        f"• Total Games Played: `{stats['total_games']}`\n"
        f"• Circulating User Balances: `{stats['total_balance']:.2f} Birr`\n"
        f"• Total Deposited: `{stats['total_deposited']:.2f} Birr`\n"
        f"• Total Withdrawn: `{stats['total_withdrawn']:.2f} Birr`"
    )
    await message.reply(text, parse_mode="Markdown")

@admin_router.message(Command("userinfo"))
async def cmd_user_info(message: types.Message):
    if not is_admin(message.from_user.id):
        return
    parts = message.text.split()
    if len(parts) != 2:
        await message.reply("Usage: `/userinfo <user_id>`")
        return
    user = await db.get_user(int(parts[1]))
    if not user:
        await message.reply("User not found.")
        return
    await message.reply(
        f"👤 **User Info**:\n"
        f"• ID: `{user['user_id']}`\n"
        f"• Username: @{user['username'] or 'N/A'}\n"
        f"• Balance: `{user['balance']:.2f} Birr`\n"
        f"• Games Played: `{user['games_played']}`\n"
        f"• Joined: `{user['joined_at']}`",
        parse_mode="Markdown"
    )

@admin_router.callback_query(lambda c: c.data.startswith("admin_"))
async def handle_admin_tx_review(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id):
        return
    action, tx_id = callback.data.replace("admin_", "").split("_")
    tx_id = int(tx_id)
    new_status = "approved" if action == "approve" else "rejected"
    await db.update_transaction_status(tx_id, new_status)
    await callback.message.edit_text(f"{callback.message.text}\n\n**STATUS UPDATED:** {new_status.upper()}", parse_mode="Markdown")
