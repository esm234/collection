#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import logging
from typing import Dict, List, Union, Tuple
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackContext,
    filters,
    ConversationHandler,
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

# Conversation states
CHOOSING_MESSAGE_TYPE = 0
TYPING_MESSAGE = 1

# Message types
MESSAGE_TYPES = {
    "استفسار": "استفسار عن القدرات أو الدورة",
    "اقتراح": "اقتراح أو فكرة",
    "ملاحظة": "ملاحظة بخصوص الملفات أو الاختبارات",
    "أخرى": "رسالة أخرى"
}

# In-memory storage
# Maps: forwarded_msg_id -> original_user_id
forwarded_messages: Dict[int, int] = {}

# Maps: user_id -> last_admin_id_who_replied
user_to_admin_map: Dict[int, int] = {}

# Maps: admin messages sent to users -> admin_id
admin_messages_to_users: Dict[int, int] = {}

# Maps: user_id -> message_type
user_message_type: Dict[int, str] = {}

async def start_command(update: Update, context: CallbackContext) -> int:
    """Send welcome message when the command /start is issued."""
    user = update.effective_user
    first_name = user.first_name
    
    # Create inline keyboard with buttons for links
    inline_keyboard = [
        [
            InlineKeyboardButton("جروب المناقشة", url="https://t.me/example_group"),
            InlineKeyboardButton("القناة الرئيسية", url="https://t.me/example_channel"),
        ],
        [
            InlineKeyboardButton("بوت الملفات", url="https://t.me/example_files_bot"),
            InlineKeyboardButton("الموقع الإلكتروني", url="https://example.com"),
        ],
    ]
    inline_markup = InlineKeyboardMarkup(inline_keyboard)
    
    # Welcome message with user's first name
    welcome_message = (
        f"مرحباً بك {first_name} في بوت الدعم الفني لـ THE LAST DANCE\n\n"
        "البوت مخصص لـ :\n"
        " • الاستفسار عن شيء يخص القدرات أو الدورة\n"
        " • إرسال الاقتراحات و الأفكار\n"
        " • إرسال ملاحظات بخصوص الملفات و الاختبارات\n\n"
        "يرجى اختيار نوع الرسالة التي تريد إرسالها:"
    )
    
    # Create reply keyboard for message type selection
    reply_keyboard = [
        ['استفسار', 'اقتراح'],
        ['ملاحظة', 'أخرى']
    ]
    markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True)
    
    # Send welcome message with inline buttons for links
    await update.message.reply_text(welcome_message, reply_markup=markup)
    
    return CHOOSING_MESSAGE_TYPE

async def message_type_selected(update: Update, context: CallbackContext) -> int:
    """Handle the message type selection."""
    user = update.effective_user
    message_type = update.message.text
    
    if message_type not in MESSAGE_TYPES:
        await update.message.reply_text(
            "الرجاء اختيار نوع الرسالة من القائمة.",
            reply_markup=ReplyKeyboardMarkup([
                ['استفسار', 'اقتراح'],
                ['ملاحظة', 'أخرى']
            ], one_time_keyboard=True, resize_keyboard=True)
        )
        return CHOOSING_MESSAGE_TYPE
    
    # Store the selected message type for this user
    user_message_type[user.id] = message_type
    
    # Ask for the actual message
    await update.message.reply_text(
        f"تم اختيار: {MESSAGE_TYPES[message_type]}\n\n"
        "الرجاء كتابة رسالتك الآن:"
    )
    
    return TYPING_MESSAGE

async def handle_user_message(update: Update, context: CallbackContext) -> int:
    """Handle the user's message after selecting a type."""
    user = update.effective_user
    user_id = user.id
    message = update.message
    
    # Check if this is a reply to an admin's message
    if message.reply_to_message:
        replied_msg_id = message.reply_to_message.message_id
        
        # Check if this is a reply to a message sent by an admin through the bot
        if replied_msg_id in admin_messages_to_users:
            admin_id = admin_messages_to_users[replied_msg_id]
            
            try:
                # Send user info
                await context.bot.send_message(
                    chat_id=admin_id, 
                    text=f"↩️ {user.first_name} replied to your message:\n\n"
                )
                
                # Forward the actual message
                forwarded_msg = await message.forward(chat_id=admin_id)
                
                # Store the mapping between forwarded message ID and original user ID
                forwarded_messages[forwarded_msg.message_id] = user_id
                
                # Confirm receipt to the user
                await message.reply_text("✅ تم إرسال ردك للمشرف")
                
                # Log the successful reply
                logger.info(f"User {user_id} replied to admin {admin_id}, message forwarded")
                
            except Exception as e:
                logger.error(f"Failed to forward reply to admin {admin_id}: {e}")
                await message.reply_text("❌ حدث خطأ في إرسال ردك")
            
            return ConversationHandler.END
    
    # Get message type if available
    message_type = user_message_type.get(user_id, "رسالة")
    
    # Prepare user info based on message type
    user_info = f"👤 Message from: {user.first_name} {user.last_name if user.last_name else ''} (@{user.username if user.username else 'No username'})\n"
    user_info += f"🆔 User ID: {user.id}\n"
    user_info += f"📝 Type: {message_type}\n\n"
    user_info += "📄 Message:"
    
    # Forward to all admins
    for admin_id in ADMIN_IDS:
        try:
            # First send user info
            await context.bot.send_message(chat_id=admin_id, text=user_info)
            
            # Then forward the actual message
            forwarded_msg = await message.forward(chat_id=admin_id)
            
            # Store the mapping between forwarded message ID and original user ID
            forwarded_messages[forwarded_msg.message_id] = user_id
            
            # Update the last admin who received a message from this user
            user_to_admin_map[user_id] = admin_id
            
        except Exception as e:
            logger.error(f"Failed to forward message to admin {admin_id}: {e}")
    
    # Confirm receipt to the user with custom message based on message type
    confirmation_messages = {
        "استفسار": "تم استلام استفسارك وسيتم الرد عليك في أقرب وقت ✅",
        "اقتراح": "شكراً لك! تم استلام اقتراحك وسيتم مراجعته من قبل الفريق ✅",
        "ملاحظة": "تم استلام ملاحظتك بخصوص الملفات/الاختبارات وسيتم العمل عليها ✅",
        "أخرى": "تم استلام رسالتك وسيتم الرد عليك في أقرب وقت ✅"
    }
    
    confirmation = confirmation_messages.get(message_type, "تم استلام رسالتك وسيتم الرد عليك في أقرب وقت ✅")
    await message.reply_text(confirmation)
    
    # Reset the conversation
    return ConversationHandler.END

async def handle_direct_message(update: Update, context: CallbackContext) -> None:
    """Handle direct messages outside the conversation flow."""
    # Skip messages from admins
    if update.effective_user.id in ADMIN_IDS:
        return
    
    user = update.effective_user
    user_id = user.id
    message = update.message
    
    # Check if this is a reply to an admin's message
    if message.reply_to_message:
        replied_msg_id = message.reply_to_message.message_id
        
        # Check if this is a reply to a message sent by an admin through the bot
        if replied_msg_id in admin_messages_to_users:
            admin_id = admin_messages_to_users[replied_msg_id]
            
            try:
                # Send user info
                await context.bot.send_message(
                    chat_id=admin_id, 
                    text=f"↩️ {user.first_name} replied to your message:\n\n"
                )
                
                # Forward the actual message
                forwarded_msg = await message.forward(chat_id=admin_id)
                
                # Store the mapping between forwarded message ID and original user ID
                forwarded_messages[forwarded_msg.message_id] = user_id
                
                # Confirm receipt to the user
                await message.reply_text("✅ تم إرسال ردك للمشرف")
                
                # Log the successful reply
                logger.info(f"User {user_id} replied to admin {admin_id}, message forwarded")
                
            except Exception as e:
                logger.error(f"Failed to forward reply to admin {admin_id}: {e}")
                await message.reply_text("❌ حدث خطأ في إرسال ردك")
            
            return
    
    # For direct messages, treat as regular message
    user_info = f"👤 Message from: {user.first_name} {user.last_name if user.last_name else ''} (@{user.username if user.username else 'No username'})\n"
    user_info += f"🆔 User ID: {user.id}\n\n"
    user_info += "📝 Message (direct):"
    
    # Forward to all admins
    for admin_id in ADMIN_IDS:
        try:
            # First send user info
            await context.bot.send_message(chat_id=admin_id, text=user_info)
            
            # Then forward the actual message
            forwarded_msg = await message.forward(chat_id=admin_id)
            
            # Store the mapping between forwarded message ID and original user ID
            forwarded_messages[forwarded_msg.message_id] = user_id
            
            # Update the last admin who received a message from this user
            user_to_admin_map[user_id] = admin_id
            
        except Exception as e:
            logger.error(f"Failed to forward message to admin {admin_id}: {e}")
    
    # Confirm receipt to the user
    await message.reply_text("تم استلام رسالتك وسيتم الرد عليك في أقرب وقت ✅")

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
            
            # Store the message mapping for tracking replies
            admin_messages_to_users[sent_msg.message_id] = admin_id
            
            # Log the successful admin reply
            logger.info(f"Admin {admin_id} replied to user {original_user_id}, message sent")
            
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

    # Add conversation handler for message type selection
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start_command)],
        states={
            CHOOSING_MESSAGE_TYPE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, message_type_selected)
            ],
            TYPING_MESSAGE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_user_message)
            ],
        },
        fallbacks=[CommandHandler("start", start_command)],
    )
    
    application.add_handler(conv_handler)
    
    # Add message handlers for admin replies and direct messages
    application.add_handler(MessageHandler(filters.REPLY & filters.TEXT & ~filters.COMMAND & filters.User(ADMIN_IDS), handle_admin_reply))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND & ~filters.ChatType.CHANNEL & ~filters.ChatType.GROUP, handle_direct_message))

    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    if not BOT_TOKEN:
        logger.error("BOT_TOKEN environment variable is not set!")
        exit(1)
    if not ADMIN_IDS:
        logger.warning("ADMIN_IDS environment variable is not set or empty. No admins configured!")
    main()