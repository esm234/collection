#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import logging
from typing import Dict, List, Union, Tuple
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackContext,
    filters,
)
from keep_alive import keep_alive

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Bot configuration
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_IDS = [int(admin_id) for admin_id in os.getenv("ADMIN_IDS", "").split(",") if admin_id]

# In-memory storage
# Maps: forwarded_msg_id -> original_user_id
forwarded_messages: Dict[int, int] = {}

# Maps: user_id -> last_admin_id_who_replied
user_to_admin_map: Dict[int, int] = {}

# Maps: user_message_id -> (admin_id, admin_message_id)
user_message_map: Dict[int, Tuple[int, int]] = {}

async def start_command(update: Update, context: CallbackContext) -> None:
    """Send welcome message when the command /start is issued."""
    user = update.effective_user
    first_name = user.first_name
    
    # Create inline keyboard with buttons
    keyboard = [
        [
            InlineKeyboardButton("جروب المناقشة", url="https://t.me/example_group"),
            InlineKeyboardButton("القناة الرئيسية", url="https://t.me/example_channel"),
        ],
        [
            InlineKeyboardButton("بوت الملفات", url="https://t.me/example_files_bot"),
            InlineKeyboardButton("الموقع الإلكتروني", url="https://example.com"),
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Welcome message with user's first name
    welcome_message = (
        f"مرحباً بك {first_name} في بوت الدعم الفني لـ THE LAST DANCE\n\n"
        "البوت مخصص لـ :\n"
        " • الاستفسار عن شيء يخص القدرات أو الدورة\n"
        " • إرسال الاقتراحات و الأفكار\n"
        " • إرسال ملاحظات بخصوص الملفات و الاختبارات\n\n"
        "أرسل رسالتك وسوف يتم الرد عليك في أقرب وقت 🫡"
    )
    
    await update.message.reply_text(welcome_message, reply_markup=reply_markup)

async def forward_to_admins(update: Update, context: CallbackContext) -> None:
    """Forward user messages to all admin users."""
    # Skip messages from admins to avoid loops
    if update.effective_user.id in ADMIN_IDS:
        return
    
    user = update.effective_user
    user_id = user.id
    user_info = f"👤 Message from: {user.first_name} {user.last_name if user.last_name else ''} (@{user.username if user.username else 'No username'})\n"
    user_info += f"🆔 User ID: {user.id}\n\n"
    user_info += "📝 Message:"
    
    # Check if this is a reply to an admin's message
    if update.message.reply_to_message and user_id in user_to_admin_map:
        # This is a reply to an admin, send it only to that admin
        admin_id = user_to_admin_map[user_id]
        try:
            # First send user info
            await context.bot.send_message(chat_id=admin_id, text=f"↩️ {user.first_name} replied to your message:\n\n")
            
            # Then forward the actual message
            forwarded_msg = await update.message.forward(chat_id=admin_id)
            
            # Store the mapping between forwarded message ID and original user ID
            forwarded_messages[forwarded_msg.message_id] = user_id
            
            # Confirm receipt to the user
            await update.message.reply_text("✅ تم إرسال ردك للمشرف")
            
        except Exception as e:
            logger.error(f"Failed to forward reply to admin {admin_id}: {e}")
            await update.message.reply_text("❌ حدث خطأ في إرسال ردك")
            
    else:
        # Regular message, forward to all admins
        for admin_id in ADMIN_IDS:
            try:
                # First send user info
                admin_msg = await context.bot.send_message(chat_id=admin_id, text=user_info)
                
                # Then forward the actual message
                forwarded_msg = await update.message.forward(chat_id=admin_id)
                
                # Store the mapping between forwarded message ID and original user ID
                forwarded_messages[forwarded_msg.message_id] = user_id
                
            except Exception as e:
                logger.error(f"Failed to forward message to admin {admin_id}: {e}")
        
        # Confirm receipt to the user
        await update.message.reply_text("تم استلام رسالتك وسيتم الرد عليك في أقرب وقت ✅")

async def handle_admin_reply(update: Update, context: CallbackContext) -> None:
    """Handle replies from admins to forward them back to the original user."""
    # Only process replies from admins
    admin_id = update.effective_user.id
    if admin_id not in ADMIN_IDS:
        return
    
    # Check if this is a reply to a forwarded message
    if not update.message.reply_to_message:
        return
    
    replied_msg_id = update.message.reply_to_message.message_id
    
    # Check if we have the original user ID for this forwarded message
    if replied_msg_id in forwarded_messages:
        original_user_id = forwarded_messages[replied_msg_id]
        
        try:
            # Forward the admin's reply to the original user
            sent_msg = await context.bot.send_message(
                chat_id=original_user_id,
                text=f"🧑‍💻 رد من فريق الدعم:\n\n{update.message.text}"
            )
            
            # Store the mapping of user to admin for future replies
            user_to_admin_map[original_user_id] = admin_id
            
            # Store the message mapping
            user_message_map[sent_msg.message_id] = (admin_id, update.message.message_id)
            
            await update.message.reply_text("✅ تم إرسال ردك للمستخدم")
            
        except Exception as e:
            logger.error(f"Failed to send admin reply to user {original_user_id}: {e}")
            await update.message.reply_text(f"❌ فشل إرسال الرد: {e}")
    else:
        await update.message.reply_text("❌ لا يمكن العثور على المستخدم الأصلي لهذه الرسالة")

def main() -> None:
    """Start the bot."""
    # Keep the bot alive
    keep_alive()
    
    # Create the Application
    application = Application.builder().token(BOT_TOKEN).build()

    # Add command handlers
    application.add_handler(CommandHandler("start", start_command))
    
    # Add message handlers
    application.add_handler(MessageHandler(filters.REPLY & filters.TEXT & ~filters.COMMAND & ~filters.ChatType.CHANNEL & ~filters.ChatType.GROUP, handle_admin_reply))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND & ~filters.ChatType.CHANNEL & ~filters.ChatType.GROUP, forward_to_admins))

    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    if not BOT_TOKEN:
        logger.error("BOT_TOKEN environment variable is not set!")
        exit(1)
    if not ADMIN_IDS:
        logger.warning("ADMIN_IDS environment variable is not set or empty. No admins configured!")
    main()