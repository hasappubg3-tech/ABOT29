from .shared import *

def build_kb(uid, pid=None):
    btns = get_buttons(pid)
    admin = is_admin(uid)
    rows = []
    current_row = []
    last_bid_in_row = None
    for i, b in enumerate(btns):
        if i > 0 and b.get('new_row', 1):
            if current_row:
                if admin and last_bid_in_row is not None:
                    current_row.append(KeyboardButton(_plus_label(last_bid_in_row)))
                rows.append(current_row)
            current_row = []
        current_row.append(KeyboardButton(b['label']))
        last_bid_in_row = b['id']
    if current_row:
        if admin and last_bid_in_row is not None:
            current_row.append(KeyboardButton(_plus_label(last_bid_in_row)))
        rows.append(current_row)
    if admin and not btns:
        rows.append([KeyboardButton(BTN_PLUS)])
    if admin:
        rows.append([KeyboardButton(BTN_ADD)])
    if pid is not None:
        rows.append([KeyboardButton(BTN_BACK)])
    if admin:
        rows.append([KeyboardButton(BTN_SETTINGS)])
    return ReplyKeyboardMarkup(rows, resize_keyboard=True) if (rows or admin) else None

def is_bot_button_text(text: str, pid=None) -> bool:
    if not text:
        return False
    if text in SPECIAL_BTNS or _parse_plus(text) is not None:
        return True
    return any(b["label"] == text for b in get_buttons(pid))

def kb_manage(pid=None):
    ctx = "r" if pid is None else str(pid)
    rows = []
    btns = get_buttons(pid)
    for b in btns:
        rows.append([
            InlineKeyboardButton(b['label'], callback_data=f"e_{b['id']}"),
            InlineKeyboardButton("🗑", callback_data=f"confirm_x_{b['id']}"),
            InlineKeyboardButton("➕", callback_data=f"plus_{b['id']}"),
        ])
    rows.append([InlineKeyboardButton("➕ إضافة", callback_data=f"plus_e_{ctx}")])
    if len(btns) >= 2:
        rows.append([InlineKeyboardButton("🔀 تبديل موضع زرين", callback_data=f"swp_start_{ctx}")])
    if pid is not None:
        b = get_btn(pid); back = b["parent_id"] if b else None
        rows.append([InlineKeyboardButton("رجوع", callback_data="m_r" if back is None else f"m_{back}")])
    return InlineKeyboardMarkup(rows)

def kb_add_type():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📂 قائمة", callback_data="pt_m"), InlineKeyboardButton("📄 محتوى", callback_data="pt_c")],
        [InlineKeyboardButton("📊 كويز", callback_data="pt_q"), InlineKeyboardButton("📝 اختبار", callback_data="pt_e")],
        [InlineKeyboardButton("⭐ مميز (للمشرفين فقط)", callback_data="pt_s")],
        [InlineKeyboardButton("❌ إلغاء", callback_data="pt_cancel")],
    ])

def kb_settings():
    global_cap = get_global_caption()
    cap_btns = get_caption_buttons()
    notif1_on  = get_setting("notif_enabled", "1") == "1"
    notif1_msg = get_setting("notif_message", "")
    cap_label    = "✏️ تغيير كليشة الكلام" if global_cap else "📌 كليشة الكلام"
    capbtn_label = f"🔗 كليشة الأزرار ({len(cap_btns)} زر)" if cap_btns else "🔗 كليشة الأزرار"
    notif1_icon  = "✅" if (notif1_on and notif1_msg) else "⭕"
    start_label  = "✏️ تعديل رسالة البداية"
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("👥 المشرفون", callback_data="st_admins")],
        [InlineKeyboardButton("💾 النسخ الاحتياطي", callback_data="st_backup_menu")],
        [InlineKeyboardButton(start_label, callback_data="st_startmsg")],
        [InlineKeyboardButton(cap_label, callback_data="st_caption")],
        [InlineKeyboardButton(capbtn_label, callback_data="st_capbtn")],
        [InlineKeyboardButton(f"📢 رسالة الاشتراك {notif1_icon}", callback_data="st_notif1")],
        [InlineKeyboardButton("📊 الإحصائيات", callback_data="st_stats")],
        [InlineKeyboardButton("🔥 الملفات الترند", callback_data="st_trending_0")],
        [InlineKeyboardButton("📡 الإذاعة", callback_data="st_broadcast")],
        [InlineKeyboardButton("💬 العبارات التحفيزية", callback_data="st_phrases")],
        [InlineKeyboardButton("⭐ الأزرار المميزة", callback_data="st_specials")],
    ])
