from .shared import *

async def cmd_start(update: Update, ctx):
    uid = update.effective_user.id
    ctx.user_data.clear()
    kb = build_kb(uid)
    start_msg = get_start_message()
    if not kb:
        await update.message.reply_text(f"{start_msg}\n\n👋 لا توجد أزرار متاحة حالياً.")
        return
    await update.message.reply_text(start_msg, reply_markup=kb)
    if not is_admin(uid):
        inc_user_sessions(uid)

async def cmd_myid(update: Update, ctx):
    await update.message.reply_text(f"🆔 `{update.effective_user.id}`", parse_mode="Markdown")

# ── معالج الرسائل الرئيسي ─────────────────────────────────────────
async def on_message(update: Update, ctx):
    m = update.message
    uid = update.effective_user.id
    text = (m.text or "").strip()
    state = ctx.user_data.get("state")
    pid = ctx.user_data.get("pid")
    chat_id = m.chat_id

    track_message(uid)
    _u = update.effective_user
    update_user_info(uid, username=_u.username, first_name=_u.first_name)
    if is_admin(uid) and _u.username:
        update_admin_username(uid, _u.username)
