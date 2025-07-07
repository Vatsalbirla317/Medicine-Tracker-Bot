import logging
import os
from datetime import time
from zoneinfo import ZoneInfo

from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# --- Configuration ---
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
GROUP_CHAT_ID = str(os.environ.get("GROUP_CHAT_ID"))
LOCAL_TIMEZONE = ZoneInfo("Asia/Kolkata")

# --- Bot's Memory (Upgraded) ---
# Instead of True/False, we store None or a dictionary with details.
bot_memory = {
    "morning_dose": None,
    "evening_dose": None
}

# --- Keywords the bot understands ---
DONE_TRIGGERS = ["done","given", "yes", "yep", "took them", "i did", "ho gaya", "le li", "liya", "dawa li", "dawa le li", "dawa ho gaya", "dawa le liya", "medicine taken"]
QUESTION_TRIGGERS = ["status", "medicine taken?", "did he take", "meds update" ,"baba ki dawai ka status", "dawa ka status", "dawa update", "medicine status", "meds status"]

# --- Bot Logic ---

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)


def remove_job_if_exists(name: str, context: ContextTypes.DEFAULT_TYPE) -> bool:
    current_jobs = context.job_queue.get_jobs_by_name(name)
    if not current_jobs:
        return False
    for job in current_jobs:
        job.schedule_removal()
    return True

# The next four functions are updated to check 'is None' instead of 'not boolean'
async def send_morning_reminder(context: ContextTypes.DEFAULT_TYPE):
    if bot_memory["morning_dose"] is None:
        logger.info("Sending MORNING reminder.")
        await context.bot.send_message(chat_id=GROUP_CHAT_ID, text="☀️ **Reminder (10:00 AM):** Time for the morning medicine!")
        context.job_queue.run_once(send_morning_follow_up, 30 * 60, name="morning_follow_up")

async def send_morning_follow_up(context: ContextTypes.DEFAULT_TYPE):
    if bot_memory["morning_dose"] is None:
        logger.info("Sending MORNING FOLLOW-UP.")
        await context.bot.send_message(chat_id=GROUP_CHAT_ID, text="⏰ **Follow-Up:** The morning medicine has not been marked as taken yet.")

async def send_evening_reminder(context: ContextTypes.DEFAULT_TYPE):
    if bot_memory["evening_dose"] is None:
        logger.info("Sending EVENING reminder.")
        await context.bot.send_message(chat_id=GROUP_CHAT_ID, text="🌙 **Reminder (7:30 PM):** Time for the evening medicine!")
        context.job_queue.run_once(send_evening_follow_up, 30 * 60, name="evening_follow_up")

async def send_evening_follow_up(context: ContextTypes.DEFAULT_TYPE):
    if bot_memory["evening_dose"] is None:
        logger.info("Sending EVENING FOLLOW-UP.")
        await context.bot.send_message(chat_id=GROUP_CHAT_ID, text="⏰ **Follow-Up:** The evening medicine has not been marked as taken yet.")

async def handle_group_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    This function now reads and writes the detailed memory.
    """
    message_text = update.message.text.lower()
    user = update.message.from_user
    current_hour = update.message.date.astimezone(LOCAL_TIMEZONE).hour

    # --- Interaction 1: Status Checks (Upgraded to show details) ---
    if any(trigger in message_text for trigger in QUESTION_TRIGGERS):
        # Morning status
        if morning_log := bot_memory["morning_dose"]:
            morning_status = f"✅ Given by {morning_log['by']} at {morning_log['at']}"
        else:
            morning_status = "⏰ Pending"
        # Evening status
        if evening_log := bot_memory["evening_dose"]:
            evening_status = f"✅ Given by {evening_log['by']} at {evening_log['at']}"
        else:
            evening_status = "⏰ Pending"
            
        status_message = (f"**Today's Medicine Status:**\n\n"
                        f"☀️ Morning: {morning_status}\n"
                        f"🌙 Evening: {evening_status}")
        await update.message.reply_text(status_message)
        return

    # --- Interaction 2: Confirming a Dose ---
    is_reply_to_bot = (
        update.message.reply_to_message and
        update.message.reply_to_message.from_user.id == context.bot.id
    )

    if is_reply_to_bot and any(trigger in message_text for trigger in DONE_TRIGGERS):
        confirmation_time = update.message.date.astimezone(LOCAL_TIMEZONE).strftime("%I:%M %p")
        log_details = {"by": user.first_name, "at": confirmation_time}
        keyword_used = False

        if "morning" in message_text:
            keyword_used = True
            if bot_memory["morning_dose"] is None:
                bot_memory["morning_dose"] = log_details
                remove_job_if_exists("morning_follow_up", context)
                await update.message.reply_text(f"✅ Morning medicine confirmed by {user.first_name} at {confirmation_time}.")
            else: # This is the new logic for an already-logged dose
                await update.message.reply_text(f"FYI, the morning dose was already logged by {bot_memory['morning_dose']['by']} at {bot_memory['morning_dose']['at']}.")

        elif "evening" in message_text:
            keyword_used = True
            if bot_memory["evening_dose"] is None:
                bot_memory["evening_dose"] = log_details
                remove_job_if_exists("evening_follow_up", context)
                await update.message.reply_text(f"🌙 Evening medicine confirmed by {user.first_name} at {confirmation_time}.")
            else: # New logic
                await update.message.reply_text(f"FYI, the evening dose was already logged by {bot_memory['evening_dose']['by']} at {bot_memory['evening_dose']['at']}.")
        
        if not keyword_used:
            if 5 <= current_hour < 17:
                if bot_memory["morning_dose"] is None:
                    bot_memory["morning_dose"] = log_details
                    remove_job_if_exists("morning_follow_up", context)
                    await update.message.reply_text(f"✅ Morning medicine confirmed by {user.first_name} at {confirmation_time}.")
                else: # New logic
                    await update.message.reply_text(f"FYI, the morning dose was already logged by {bot_memory['morning_dose']['by']} at {bot_memory['morning_dose']['at']}.")
            else:
                if bot_memory["evening_dose"] is None:
                    bot_memory["evening_dose"] = log_details
                    remove_job_if_exists("evening_follow_up", context)
                    await update.message.reply_text(f"🌙 Evening medicine confirmed by {user.first_name} at {confirmation_time}.")
                else: # New logic
                    await update.message.reply_text(f"FYI, the evening dose was already logged by {bot_memory['evening_dose']['by']} at {bot_memory['evening_dose']['at']}.")

# This function is updated to reset the memory to None
async def reset_all_statuses(context: ContextTypes.DEFAULT_TYPE):
    bot_memory["morning_dose"] = None
    bot_memory["evening_dose"] = None
    logger.info("--- RESET --- All statuses reset for the new day.")
    await context.bot.send_message(chat_id=GROUP_CHAT_ID, text="🌅 **New Day!** All medicine reminders have been reset.")


async def test_morning_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("OK, triggering the morning reminder sequence now...")
    await send_morning_reminder(context)

async def test_evening_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("OK, triggering the evening reminder sequence now...")
    await send_evening_reminder(context)

async def test_reset_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("OK, triggering the daily reset now...")
    await reset_all_statuses(context)

def main():
    if not TELEGRAM_TOKEN or not GROUP_CHAT_ID:
        logger.error("FATAL: TELEGRAM_TOKEN or GROUP_CHAT_ID environment variable not set!")
        return

    application = Application.builder().token(TELEGRAM_TOKEN).build()
    
    application.job_queue.run_daily(send_morning_reminder, time(hour=10, minute=0, tzinfo=LOCAL_TIMEZONE), name="daily_morning_reminder")
    application.job_queue.run_daily(send_evening_reminder, time(hour=19, minute=30, tzinfo=LOCAL_TIMEZONE), name="daily_evening_reminder")
    application.job_queue.run_daily(reset_all_statuses, time(hour=0, minute=5, tzinfo=LOCAL_TIMEZONE), name="daily_reset")

    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND & filters.Chat(int(GROUP_CHAT_ID)), handle_group_messages))
    
    application.add_handler(CommandHandler("test_morning", test_morning_command, filters=filters.ChatType.PRIVATE))
    application.add_handler(CommandHandler("test_evening", test_evening_command, filters=filters.ChatType.PRIVATE))
    application.add_handler(CommandHandler("test_reset", test_reset_command, filters=filters.ChatType.PRIVATE))

    logger.info("Automated Medicine Bot (Final, with Detailed Logging) is starting...")
    application.run_polling()

if __name__ == "__main__":
    main()