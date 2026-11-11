import asyncio
import random
from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from config import MIN_BET, MAX_BET, WITHDRAWAL_THRESHOLD
from keyboards.inline import numbers_selection_keyboard, bet_selection_keyboard, main_menu_keyboard
from utils.keno import draw_numbers, calculate_payout
import database.db as db

game_router = Router()

class KenoState(StatesGroup):
    picking = State()
    betting = State()

@game_router.callback_query(F.data == "game_start")
async def game_start(callback: types.CallbackQuery, state: FSMContext):
    user = await db.get_user(callback.from_user.id)
    if user['balance'] < MIN_BET:
        await callback.answer(
            f"❌ Insufficient balance ({user['balance']:.2f} Birr). Min bet is {MIN_BET} Birr. Please deposit to continue.",
            show_alert=True
        )
        return

    await state.set_state(KenoState.picking)
    await state.update_data(selected=[], page=1)
    kb = numbers_selection_keyboard(1, [])
    await callback.message.edit_text(
        "🎯 **Pick 1 to 10 Numbers (1 - 80)**:\nSelected: `None`",
        reply_markup=kb,
        parse_mode="Markdown"
    )

@game_router.callback_query(KenoState.picking, F.data.startswith("page_"))
async def change_page(callback: types.CallbackQuery, state: FSMContext):
    page = int(callback.data.split("_")[1])
    data = await state.get_data()
    selected = data.get("selected", [])
    await state.update_data(page=page)
    await callback.message.edit_reply_markup(reply_markup=numbers_selection_keyboard(page, selected))

@game_router.callback_query(KenoState.picking, F.data.startswith("num_"))
async def handle_num_click(callback: types.CallbackQuery, state: FSMContext):
    action = callback.data.split("_")[1]
    data = await state.get_data()
    selected = set(data.get("selected", []))
    page = data.get("page", 1)

    if action == "clear":
        selected.clear()
    elif action == "quickpick":
        selected = set(random.sample(range(1, 81), 5))
    elif action == "proceed":
        if len(selected) < 1:
            await callback.answer("Please select at least 1 number!", show_alert=True)
            return
        await state.set_state(KenoState.betting)
        await callback.message.edit_text(
            f"🔢 Your numbers: `{sorted(list(selected))}`\n\nSelect your bet amount:",
            reply_markup=bet_selection_keyboard(),
            parse_mode="Markdown"
        )
        return
    else:
        num = int(action)
        if num in selected:
            selected.remove(num)
        else:
            if len(selected) >= 10:
                await callback.answer("Maximum 10 numbers allowed!", show_alert=True)
                return
            selected.add(num)

    await state.update_data(selected=list(selected))
    text = f"🎯 **Pick 1 to 10 Numbers (1 - 80)**:\nSelected: `{sorted(list(selected)) if selected else 'None'}`"
    await callback.message.edit_text(text, reply_markup=numbers_selection_keyboard(page, list(selected)), parse_mode="Markdown")

@game_router.callback_query(KenoState.betting, F.data.startswith("bet_"))
async def execute_draw(callback: types.CallbackQuery, state: FSMContext):
    bet = float(callback.data.split("_")[1])
    user = await db.get_user(callback.from_user.id)

    if user['balance'] < bet:
        await callback.answer(f"Insufficient balance! You have {user['balance']:.2f} Birr.", show_alert=True)
        return

    data = await state.get_data()
    selected = sorted(data.get("selected", []))
    spots = len(selected)

    # Deduct bet immediately
    await db.update_balance(callback.from_user.id, -bet)
    await state.clear()

    # Suspense animation
    for dots in [".", "..", "..."]:
        await callback.message.edit_text(f"🎲 Drawing 20 balls{dots}")
        await asyncio.sleep(0.4)

    drawn = draw_numbers()
    matched = sorted(list(set(selected).intersection(set(drawn))))
    matches_count = len(matched)
    multiplier, payout = calculate_payout(spots, matches_count, bet)

    if payout > 0:
        await db.update_balance(callback.from_user.id, payout)

    await db.record_game(callback.from_user.id, bet, spots, selected, drawn, matches_count, payout)
    refreshed_user = await db.get_user(callback.from_user.id)

    # Format result message
    drawn_str = ", ".join(f"**{n}**" if n in matched else str(n) for n in drawn)
    outcome_banner = f"🎉 **YOU WON {payout:.2f} BIRR!** (x{multiplier})" if payout > 0 else "❌ **NO WIN**"

    result_text = (
        f"{outcome_banner}\n\n"
        f"🎯 Your spots ({spots}): `{selected}`\n"
        f"🎱 Drawn: {drawn_str}\n"
        f"✨ Hits: **{matches_count}** ({matched})\n"
        f"💵 Bet: `{bet:.2f} Birr` | Payout: `{payout:.2f} Birr`\n"
        f"💰 Current Balance: `{refreshed_user['balance']:.2f} Birr`\n"
    )

    if refreshed_user['balance'] < MIN_BET:
        result_text += "\n⚠️ **Balance low!** Top up via Deposit to keep playing."

    kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Play Again", callback_data="game_start")],
        [InlineKeyboardButton(text="🏠 Main Menu", callback_data="menu_main")]
    ])
    await callback.message.edit_text(result_text, reply_markup=kb, parse_mode="Markdown")

@game_router.callback_query(F.data == "game_cancel")
async def game_cancel(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    user = await db.get_user(callback.from_user.id)
    kb = main_menu_keyboard(user['balance'], WITHDRAWAL_THRESHOLD)
    await callback.message.edit_text("Game cancelled.", reply_markup=kb)
