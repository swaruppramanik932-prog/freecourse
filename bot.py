
import logging
import os
from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup,
    ReplyKeyboardMarkup, KeyboardButton
)
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes, ConversationHandler
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = "8619982542:AAH4fTVME2Mrgg0CvKNHvJvlGnvQyRZ-ouo"
ADMIN_CHAT_ID = "6901201338"
CHANNEL_USERNAME = "@lootera_boss"

# States
(CHECK_JOIN, SELECT_PLATFORM, SELECT_PW_COURSE, SELECT_SE_COURSE,
 SELECT_OTHER_COURSE, AWAITING_CUSTOM_COURSE, AWAITING_SCREENSHOT,
 AWAITING_FEEDBACK) = range(8)

PLATFORMS = {
    "pw": "📚 PW (Physics Wallah)",
    "unacademy": "🎓 Unacademy",
    "kgs": "📖 KGS",
    "target": "🎯 Target Class 10",
    "iit_jee": "⚡ IIT JEE Academy",
    "byju": "🏫 BYJU'S",
    "vedantu": "💻 Vedantu",
    "toprankers": "🏆 Top Rankers",
    "software_engineer": "💼 Software Engineering",
    "other": "➕ Other",
}

PW_COURSES = ["JEE", "NEET", "GATE", "Other"]
SE_COURSES = ["Data Analyst", "MERN Stack", "Full Stack", "Other"]


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton("✅ Join Channel", url=f"t.me/lootera_boss")],
                [InlineKeyboardButton("🔄 I've Joined — Verify Me", callback_data="verify_join")]]
    await update.message.reply_text(
        "👋 Welcome! To access our courses, please first join our official channel:\n\n"
        f"👉 {CHANNEL_USERNAME}\n\n"
        "After joining, click the verify button below.",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return CHECK_JOIN


async def verify_join(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    try:
        member = await context.bot.get_chat_member(CHANNEL_USERNAME, query.from_user.id)
        if member.status in ["member", "administrator", "creator"]:
            await query.edit_message_text("✅ Verified! Now select a course platform:")
            return await show_platforms(update, context)
        else:
            raise Exception("Not a member")
    except Exception:
        keyboard = [[InlineKeyboardButton("📢 Join Channel", url=f"https://t.me/{CHANNEL_USERNAME.lstrip('@')}")],
                    [InlineKeyboardButton("🔄 Try Again", callback_data="verify_join")]]
        await query.edit_message_text(
            "❌ You haven't joined our channel yet.\nPlease join and try again.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return CHECK_JOIN


async def show_platforms(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = []
    for key, label in PLATFORMS.items():
        keyboard.append([InlineKeyboardButton(label, callback_data=f"platform_{key}")])
    msg = InlineKeyboardMarkup(keyboard)
    if update.callback_query:
        await update.callback_query.message.reply_text("📚 Select your course platform:", reply_markup=msg)
    else:
        await update.message.reply_text("📚 Select your course platform:", reply_markup=msg)
    return SELECT_PLATFORM


async def platform_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    platform = query.data.replace("platform_", "")
    context.user_data["platform"] = platform

    if platform == "pw":
        keyboard = [[InlineKeyboardButton(c, callback_data=f"pwcourse_{c}")] for c in PW_COURSES]
        await query.edit_message_text(
            "📚 PW Courses — Select your stream:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return SELECT_PW_COURSE

    elif platform == "software_engineer":
        keyboard = [[InlineKeyboardButton(c, callback_data=f"secourse_{c}")] for c in SE_COURSES]
        await query.edit_message_text(
            "💼 Software Engineering — Select your course:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return SELECT_SE_COURSE

    elif platform == "other":
        await query.edit_message_text("✏️ Please type your course/platform name:")
        return AWAITING_CUSTOM_COURSE

    else:
        label = PLATFORMS.get(platform, platform)
        context.user_data["course"] = label
        await query.edit_message_text(
            f"✅ Selected: *{label}*\n\n"
            "📸 Please upload a screenshot of your payment with your *name visible* in the image.",
            parse_mode="Markdown"
        )
        return AWAITING_SCREENSHOT


async def pw_course_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    course = query.data.replace("pwcourse_", "")

    if course == "Other":
        await query.edit_message_text("✏️ Please type your PW course name:")
        return AWAITING_CUSTOM_COURSE

    context.user_data["course"] = f"PW - {course}"
    await query.edit_message_text(
        f"✅ Selected: *PW - {course}*\n\n"
        "📸 Upload a screenshot of your payment (with your name visible).",
        parse_mode="Markdown"
    )
    return AWAITING_SCREENSHOT


async def se_course_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    course = query.data.replace("secourse_", "")

    if course == "Other":
        await query.edit_message_text("✏️ Please type your Software Engineering course name:")
        return AWAITING_CUSTOM_COURSE

    context.user_data["course"] = f"Software Engineering - {course}"
    await query.edit_message_text(
        f"✅ Selected: *Software Engineering - {course}*\n\n"
        "📸 Upload a screenshot of your payment (with your name visible).",
        parse_mode="Markdown"
    )
    return AWAITING_SCREENSHOT


async def custom_course_entered(update: Update, context: ContextTypes.DEFAULT_TYPE):
    course = update.message.text.strip()
    context.user_data["course"] = course
    await update.message.reply_text(
        f"✅ Course noted: *{course}*\n\n"
        "📸 Upload a screenshot of your payment (with your name visible).",
        parse_mode="Markdown"
    )
    return AWAITING_SCREENSHOT


async def screenshot_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    course = context.user_data.get("course", "Unknown")
    platform = context.user_data.get("platform", "Unknown")

    if update.message.photo:
        file_id = update.message.photo[-1].file_id
        caption = (
            f"🆕 *New Course Request*\n"
            f"👤 Name: {user.full_name}\n"
            f"🆔 User ID: `{user.id}`\n"
            f"📱 Username: @{user.username or 'N/A'}\n"
            f"📚 Platform: {platform}\n"
            f"📖 Course: {course}"
        )
        keyboard = [[InlineKeyboardButton(
            "📨 Send Course Link", callback_data=f"sendlink_{user.id}"
        )]]
        await context.bot.send_photo(
            chat_id=ADMIN_CHAT_ID,
            photo=file_id,
            caption=caption,
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        await update.message.reply_text(
            "✅ Your payment screenshot has been submitted!\n\n"
            "⏳ Our admin will review and send you the course link shortly.\n"
            "Please wait..."
        )
        return ConversationHandler.END
    else:
        await update.message.reply_text("⚠️ Please send a photo/screenshot, not a file or text.")
        return AWAITING_SCREENSHOT


async def admin_send_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    target_user_id = int(query.data.replace("sendlink_", ""))
    context.user_data["send_link_to"] = target_user_id
    await query.message.reply_text(
        f"✏️ Reply with the course link to send to user `{target_user_id}`:",
        parse_mode="Markdown"
    )


async def send_link_to_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if "send_link_to" in context.user_data:
        target = context.user_data.pop("send_link_to")
        link = update.message.text.strip()
        try:
            keyboard = [[InlineKeyboardButton("⭐ Leave Feedback", callback_data="give_feedback")]]
            await context.bot.send_message(
                chat_id=target,
                text=f"🎉 *Your course link is ready!*\n\n🔗 {link}\n\n"
                     "Enjoy learning! Feel free to leave feedback below.",
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            await update.message.reply_text(f"✅ Link sent to user {target}.")
        except Exception as e:
            await update.message.reply_text(f"❌ Failed to send: {e}")


async def feedback_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    keyboard = [
        [InlineKeyboardButton("⭐", callback_data="fb_1"), InlineKeyboardButton("⭐⭐", callback_data="fb_2"),
         InlineKeyboardButton("⭐⭐⭐", callback_data="fb_3")],
        [InlineKeyboardButton("⭐⭐⭐⭐", callback_data="fb_4"), InlineKeyboardButton("⭐⭐⭐⭐⭐", callback_data="fb_5")],
        [InlineKeyboardButton("✏️ Write Custom Feedback", callback_data="fb_custom")]
    ]
    await query.message.reply_text(
        "📝 Please share your feedback:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return AWAITING_FEEDBACK


async def feedback_rating(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "fb_custom":
        await query.edit_message_text("✏️ Please type your feedback:")
        return AWAITING_FEEDBACK

    rating_map = {"fb_1": "⭐ 1/5", "fb_2": "⭐⭐ 2/5", "fb_3": "⭐⭐⭐ 3/5",
                  "fb_4": "⭐⭐⭐⭐ 4/5", "fb_5": "⭐⭐⭐⭐⭐ 5/5"}
    rating = rating_map.get(query.data, query.data)
    user = query.from_user

    await context.bot.send_message(
        chat_id=ADMIN_CHAT_ID,
        text=f"💬 *Feedback Received*\n"
             f"👤 {user.full_name} (@{user.username or 'N/A'})\n"
             f"⭐ Rating: {rating}",
        parse_mode="Markdown"
    )
    await query.edit_message_text("🙏 Thank you for your feedback! We appreciate it.")
    return ConversationHandler.END


async def feedback_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    text = update.message.text
    await context.bot.send_message(
        chat_id=ADMIN_CHAT_ID,
        text=f"💬 *Feedback Received*\n"
             f"👤 {user.full_name} (@{user.username or 'N/A'})\n"
             f"📝 {text}",
        parse_mode="Markdown"
    )
    await update.message.reply_text("🙏 Thank you for your feedback!")
    return ConversationHandler.END


def main():
    app = Application.builder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            CHECK_JOIN: [CallbackQueryHandler(verify_join, pattern="^verify_join$")],
            SELECT_PLATFORM: [CallbackQueryHandler(platform_selected, pattern="^platform_")],
            SELECT_PW_COURSE: [CallbackQueryHandler(pw_course_selected, pattern="^pwcourse_")],
            SELECT_SE_COURSE: [CallbackQueryHandler(se_course_selected, pattern="^secourse_")],
            AWAITING_CUSTOM_COURSE: [MessageHandler(filters.TEXT & ~filters.COMMAND, custom_course_entered)],
            AWAITING_SCREENSHOT: [MessageHandler(filters.PHOTO, screenshot_received),
                                   MessageHandler(filters.TEXT & ~filters.COMMAND, screenshot_received)],
            AWAITING_FEEDBACK: [
                CallbackQueryHandler(feedback_rating, pattern="^fb_"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, feedback_text)
            ],
        },
        fallbacks=[CommandHandler("start", start)],
        allow_reentry=True
    )

    app.add_handler(conv_handler)
    app.add_handler(CallbackQueryHandler(admin_send_link, pattern="^sendlink_"))
    app.add_handler(CallbackQueryHandler(feedback_prompt, pattern="^give_feedback$"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, send_link_to_user))

    logger.info("Bot started...")
    app.run_polling()


if __name__ == "__main__":
    main()
