from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def main_menu_keyboard(balance: float, threshold: float) -> InlineKeyboardMarkup:
    withdraw_btn = (
        InlineKeyboardButton(text="💸 Withdraw", callback_data="menu_withdraw")
        if balance >= threshold
        else InlineKeyboardButton(text=f"🔒 Withdraw (Locked < {int(threshold)} ETB)", callback_data="locked_withdraw")
    )
    
    keyboard = [
        [InlineKeyboardButton(text="🎰 Play Keno", callback_data="game_start")],
        [InlineKeyboardButton(text="💰 Balance", callback_data="menu_balance"), InlineKeyboardButton(text="📥 Deposit", callback_data="menu_deposit")],
        [withdraw_btn],
        [InlineKeyboardButton(text="📜 History", callback_data="menu_history"), InlineKeyboardButton(text="🏆 Leaderboard", callback_data="menu_leaderboard")],
        [InlineKeyboardButton(text="ℹ️ Rules & Help", callback_data="menu_help"), InlineKeyboardButton(text="💬 Support", callback_data="menu_support")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def numbers_selection_keyboard(page: int, selected: list[int]) -> InlineKeyboardMarkup:
    # 80 numbers divided into 4 pages of 20 numbers each
    start_num = (page - 1) * 20 + 1
    end_num = page * 20
    keyboard = []
    row = []

    for n in range(start_num, end_num + 1):
        label = f"✅ {n}" if n in selected else f"{n}"
        row.append(InlineKeyboardButton(text=label, callback_data=f"num_{n}"))
        if len(row) == 5:
            keyboard.append(row)
            row = []

    # Page controls
    nav_row = []
    if page > 1:
        nav_row.append(InlineKeyboardButton(text="⬅️ Prev", callback_data=f"page_{page-1}"))
    nav_row.append(InlineKeyboardButton(text=f"P {page}/4", callback_data="noop"))
    if page < 4:
        nav_row.append(InlineKeyboardButton(text="Next ➡️", callback_data=f"page_{page+1}"))
    keyboard.append(nav_row)

    # Actions
    keyboard.append([
        InlineKeyboardButton(text=f"Selected: {len(selected)}/10", callback_data="noop"),
        InlineKeyboardButton(text="🎲 Quick Pick", callback_data="num_quickpick")
    ])
    keyboard.append([
        InlineKeyboardButton(text="🧹 Clear", callback_data="num_clear"),
        InlineKeyboardButton(text="➡️ Next: Set Bet", callback_data="num_proceed")
    ])
    keyboard.append([InlineKeyboardButton(text="🔙 Back to Menu", callback_data="menu_main")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def bet_selection_keyboard() -> InlineKeyboardMarkup:
    presets = [10, 20, 50, 100, 200, 500]
    keyboard = []
    row = []
    for bet in presets:
        row.append(InlineKeyboardButton(text=f"{bet} Birr", callback_data=f"bet_{bet}"))
        if len(row) == 3:
            keyboard.append(row)
            row = []
    keyboard.append([InlineKeyboardButton(text="🔙 Cancel", callback_data="game_cancel")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def admin_action_keyboard(tx_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="✅ Approve", callback_data=f"admin_approve_{tx_id}"),
        InlineKeyboardButton(text="❌ Reject", callback_data=f"admin_reject_{tx_id}")
    ]])
