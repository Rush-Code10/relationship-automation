import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
import sys
import os
sys.path.append(os.path.dirname(__file__))

from src.pipeline import run_pipeline
from src.state.tracker import StateTracker
from src.automation.actions import generate_action_message

# Enable logging
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

# Your bot token from BotFather
TOKEN = "YOUR_BOT_TOKEN_HERE"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Welcome! Use /run to execute the relationship automation pipeline.")

async def run(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Running pipeline... This may take a moment.")
    try:
        # Run the pipeline (you may want to pass a custom config path)
        df, scores_df, actions, tracker = run_pipeline("config/config.yaml")
        if not actions:
            await update.message.reply_text("No actions generated.")
            return

        # Send each action as a separate message with inline feedback buttons
        for action in actions:
            msg = generate_action_message(action)
            # Create inline keyboard: Accept / Dismiss
            keyboard = [
                [
                    InlineKeyboardButton("✅ Accept", callback_data=f"accept_{action['contact']}_{action['type']}"),
                    InlineKeyboardButton("❌ Dismiss", callback_data=f"dismiss_{action['contact']}_{action['type']}")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            # Add extra info
            extra = f"\n🧠 Reason: {action['reason']}"
            if action.get('details'):
                extra += f"\n📝 Details: {', '.join(str(d) for d in action['details'][:2])}"
            await update.message.reply_text(msg + extra, reply_markup=reply_markup)

    except Exception as e:
        logger.exception("Error running pipeline")
        await update.message.reply_text(f"Error: {str(e)}")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data.split('_')
    feedback = data[0]          # accept or dismiss
    contact = data[1]
    action_type = '_'.join(data[2:])  # in case action type has underscores

    # Here you would need to map this feedback to a specific action ID.
    # For simplicity, we'll just acknowledge.
    await query.edit_message_text(text=f"Feedback recorded: {feedback} for {contact} - {action_type}")

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("run", run))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.run_polling()

if __name__ == "__main__":
    main()