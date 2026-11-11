from aiogram import Router, types, F
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from config import INITIAL_BONUS, WITHDRAWAL_THRESHOLD, PAYMENT_INSTRUCTIONS, ADMIN_IDS
from keyboards.inline import main_menu_keyboard, admin_action_keyboard
import database.db as db

user_router = Router()

class DepositForm(StatesGroup):
    details = State()

class WithdrawForm(StatesGroup):
    details = State()

@user_router.message(CommandStart())
async def cmd_start(message: types.Message):
    user = await db.get_user(message.from_user.id)
    if not user:
        await db.create_user(message.from_user.id, message.from_user.username or "", INITIAL_BONUS)
        welcome = (
            f"🎉 Welcome to **Ethiopian Keno**!\n\n"
            f"🎁 You received a **{int(INITIAL_BONUS)} Birr Free Bonus** to test your luck!\n\n"
            f"⚠️ **Notice**: This 50 Birr is promotional play money. Withdrawals are unlocked once your balance reaches **{int(WITHDRAWAL_THRESHOLD)} Birr**."
        )
    else:
        welcome = f"👋 Welcome back, **{message.from_user.first_name}**!"

    user = await db.get_user(message.from_user.id)
    kb = main_menu_keyboard(user['balance'], WITHDRAWAL_THRESHOLD)
    await message.answer(welcome, reply_markup=kb, parse_mode="Markdown")

@user_router.callback_query(F.data == "menu_main")
async def nav_main(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    user = await db.get_user(callback.from_user.id)
    kb = main_menu_keyboard(user['balance'], WITHDRAWAL_THRESHOLD)
    await callback.message.edit_text("🏠 **Main Menu**\nSelect an option below:", reply_markup=kb, parse_mode="Markdown")

@user_router.callback_query(F.data == "menu_balance")
async def nav_balance(callback: types.CallbackQuery):
    user = await db.get_user(callback.from_user.id)
    bal = user['balance']
    status = "🔓 Eligible for withdrawal" if bal >= WITHDRAWAL_THRESHOLD else f"🔒 Locked until {int(WITHDRAWAL_THRESHOLD)} Birr"
    text = (
        f"💳 **Your Wallet**\n\n"
        f"• Current Balance: `{bal:.2f} Birr`\n"
        f"• Withdrawal Status: {status}\n\n"
        f"💡 Minimum bet is 10 Birr."
    )
    kb = types.InlineKeyboardMarkup(inline_keyboard=[[types.InlineKeyboardButton(text="🔙 Back", callback_data="menu_main")]])
    await callback.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")

@user_router.callback_query(F.data == "locked_withdraw")
async def nav_locked_withdraw(callback: types.CallbackQuery):
    await callback.answer(f"Withdrawal threshold is {int(WITHDRAWAL_THRESHOLD)} Birr. Keep playing to reach the goal!", show_alert=True)

@user_router.callback_query(F.data == "menu_deposit")
async def nav_deposit(callback: types.CallbackQuery, state: FSMContext):
    kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="📤 Submit Deposit Reference", callback_data="deposit_submit")],
        [types.InlineKeyboardButton(text="🔙 Back", callback_data="menu_main")]
    ])
    await callback.message.edit_text(PAYMENT_INSTRUCTIONS, reply_markup=kb, parse_mode="Markdown")

@user_router.callback_query(F.data == "deposit_submit")
async def deposit_submit(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(DepositForm.details)
    await callback.message.edit_text(
        "📝 Enter the amount deposited and transaction reference / phone number:\n\n*Example:* `100 Birr via Telebirr ref #TX1234567`",
        parse_mode="Markdown"
    )

@user_router.message(DepositForm.details)
async def process_deposit_input(message: types.Message, state: FSMContext):
    tx_id = await db.create_transaction(message.from_user.id, "deposit", 0.0, message.text)
    await state.clear()
    await message.reply("✅ Deposit request sent to admin for confirmation. Your balance will be credited soon!")

    # Notify admins
    for admin_id in ADMIN_IDS:
        try:
            await message.bot.send_message(
                admin_id,
                f"📥 **New Deposit Request #{tx_id}**\nUser: `{message.from_user.id}` (@{message.from_user.username})\nDetails: {message.text}",
                reply_markup=admin_action_keyboard(tx_id),
                parse_mode="Markdown"
            )
        except Exception:
            pass

@user_router.callback_query(F.data == "menu_withdraw")
async def nav_withdraw(callback: types.CallbackQuery, state: FSMContext):
    user = await db.get_user(callback.from_user.id)
    if user['balance'] < WITHDRAWAL_THRESHOLD:
        await callback.answer(f"Minimum withdrawal is {WITHDRAWAL_THRESHOLD} Birr.", show_alert=True)
        return
    await state.set_state(WithdrawForm.details)
    await callback.message.edit_text("💸 Enter the amount and your payment details (Telebirr/Bank Account):\n\n*Example:* `2000 Birr to Telebirr 0911000000 Abebe`", parse_mode="Markdown")

@user_router.message(WithdrawForm.details)
async def process_withdraw_input(message: types.Message, state: FSMContext):
    user = await db.get_user(message.from_user.id)
    if user['balance'] < WITHDRAWAL_THRESHOLD:
        await message.reply("Insufficient balance to complete withdrawal.")
        await state.clear()
        return

    tx_id = await db.create_transaction(message.from_user.id, "withdrawal", user['balance'], message.text)
    await state.clear()
    await message.reply("✅ Withdrawal request submitted to admins for manual transfer.")

    for admin_id in ADMIN_IDS:
        try:
            await message.bot.send_message(
                admin_id,
                f"📤 **Withdrawal Request #{tx_id}**\nUser: `{message.from_user.id}` (@{message.from_user.username})\nBalance: {user['balance']} Birr\nDetails: {message.text}",
                reply_markup=admin_action_keyboard(tx_id),
                parse_mode="Markdown"
            )
        except Exception:
            pass

@user_router.callback_query(F.data == "menu_leaderboard")
async def nav_leaderboard(callback: types.CallbackQuery):
    top = await db.get_leaderboard(10)
    lines = ["🏆 **Top Balances**\n"]
    for idx, u in enumerate(top, 1):
        name = u['username'] if u['username'] else "Anonymous"
        lines.append(f"{idx}. @{name} — `{u['balance']:.2f} Birr` ({u['games_played']} games)")
    kb = types.InlineKeyboardMarkup(inline_keyboard=[[types.InlineKeyboardButton(text="🔙 Back", callback_data="menu_main")]])
    await callback.message.edit_text("\n".join(lines), reply_markup=kb, parse_mode="Markdown")

@user_router.callback_query(F.data == "menu_history")
async def nav_history(callback: types.CallbackQuery):
    games = await db.get_recent_games(callback.from_user.id, 10)
    if not games:
        text = "No games played yet. Click 'Play Keno' to start!"
    else:
        text = "📜 **Your Last 10 Games**\n\n"
        for g in games:
            win_sym = "🟢" if g['payout'] > 0 else "🔴"
            text += f"{win_sym} Bet: {g['bet_amount']} ETB | Spots: {g['spots_count']} | Hits: {g['matched_count']} | Payout: **+{g['payout']:.2f} ETB**\n"
    kb = types.InlineKeyboardMarkup(inline_keyboard=[[types.InlineKeyboardButton(text="🔙 Back", callback_data="menu_main")]])
    await callback.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")

@user_router.callback_query(F.data == "menu_help")
async def nav_help(callback: types.CallbackQuery):
    rules = (
        "📖 **Keno Rules & Payout Structure**\n\n"
        "1. Pick between 1 to 10 numbers out of 80.\n"
        "2. The bot randomly draws 20 winning numbers.\n"
        "3. Match your chosen numbers to win multipliers on your bet.\n\n"
        "💰 **Economy & Free Bonus**:\n"
        "• New users receive a **50 Birr bonus** for play.\n"
        "• Bonus cannot be withdrawn directly.\n"
        f"• Withdrawals unlock strictly at **{int(WITHDRAWAL_THRESHOLD)} Birr**.\n"
        "• Deposit via Telebirr or Bank if you run low."
    )
    kb = types.InlineKeyboardMarkup(inline_keyboard=[[types.InlineKeyboardButton(text="🔙 Back", callback_data="menu_main")]])
    await callback.message.edit_text(rules, reply_markup=kb, parse_mode="Markdown")

@user_router.callback_query(F.data == "menu_support")
async def nav_support(callback: types.CallbackQuery):
    kb = types.InlineKeyboardMarkup(inline_keyboard=[[types.InlineKeyboardButton(text="🔙 Back", callback_data="menu_main")]])
    await callback.message.edit_text("💬 For deposits, manual checks, or issues, reach out to our admin desk: @YourTelegramAdmin", reply_markup=kb)
