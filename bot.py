#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import logging
from typing import Dict, List, Union, Tuple
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, MenuButtonCommands
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
# Maps: admin_msg_id -> original_user_id
forwarded_messages: Dict[int, int] = {}

# Maps: user_id -> last_admin_id_who_replied
user_to_admin_map: Dict[int, int] = {}

# Maps: admin_msg_id -> original_msg_id (user's message ID)
original_messages: Dict[int, int] = {}

# Maps: admin messages sent to users -> admin_id
admin_messages_to_users: Dict[int, int] = {}

# Maps: admin_id -> last_info_message_id
admin_info_messages: Dict[int, int] = {}

async def set_menu_button(application: Application) -> None:
    """Set the menu button to show commands."""
    await application.bot.set_chat_menu_button(
        menu_button=MenuButtonCommands(type="commands")
    )
    logger.info("Menu button set to commands")

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

async def handle_user_message(update: Update, context: CallbackContext) -> None:
    """Handle all messages from users (both new messages and replies)."""
    # Skip messages from admins in this handler
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
                # Send user info as a new message
                info_msg = await context.bot.send_message(
                    chat_id=admin_id, 
                    text=f"↩️ {user.first_name} replied to your message:"
                )
                
                # Store this info message ID
                admin_info_messages[admin_id] = info_msg.message_id
                
                # Send the actual message content as a reply to the info message
                admin_msg = await context.bot.send_message(
                    chat_id=admin_id,
                    text=message.text,
                    reply_to_message_id=info_msg.message_id
                )
                
                # Store the mapping between admin message ID and original user ID
                forwarded_messages[admin_msg.message_id] = user_id
                
                # Store the mapping between admin message ID and original message ID
                original_messages[admin_msg.message_id] = message.message_id
                
                # Confirm receipt to the user
                await message.reply_text("✅ تم إرسال ردك للمشرف")
                
                # Log the successful reply
                logger.info(f"User {user_id} replied to admin {admin_id}, message sent")
                
            except Exception as e:
                logger.error(f"Failed to send reply to admin {admin_id}: {e}")
                await message.reply_text("❌ حدث خطأ في إرسال ردك")
            
            return
    
    # If not a reply or reply to non-admin message, treat as a new message
    # and forward to all admins
    for admin_id in ADMIN_IDS:
        try:
            # First send user info
            user_info = f"👤 Message from: {user.first_name} {user.last_name if user.last_name else ''} (@{user.username if user.username else 'No username'})\n"
            user_info += f"🆔 User ID: {user.id}"
            
            info_msg = await context.bot.send_message(chat_id=admin_id, text=user_info)
            
            # Store this info message ID
            admin_info_messages[admin_id] = info_msg.message_id
            
            # Then send the actual message as a reply to the info message
            admin_msg = await context.bot.send_message(
                chat_id=admin_id,
                text=message.text,
                reply_to_message_id=info_msg.message_id
            )
            
            # Store the mapping between admin message ID and original user ID
            forwarded_messages[admin_msg.message_id] = user_id
            
            # Store the mapping between admin message ID and original message ID
            original_messages[admin_msg.message_id] = message.message_id
            
            # Update the last admin who received a message from this user
            user_to_admin_map[user_id] = admin_id
            
        except Exception as e:
            logger.error(f"Failed to send message to admin {admin_id}: {e}")
    
    # Confirm receipt to the user
    await message.reply_text("تم استلام رسالتك وسيتم الرد عليك في أقرب وقت ✅")

async def handle_admin_reply(update: Update, context: CallbackContext) -> None:
    """Handle replies from admins to forward them back to the original user."""
    # Only process replies from admins
    admin_id = update.effective_user.id
    if admin_id not in ADMIN_IDS:
        return
    
    # Check if this is a reply to a message
    if not update.message.reply_to_message:
        return
    
    replied_msg_id = update.message.reply_to_message.message_id
    
    # Check if the admin is replying to a user message or to the info message
    if replied_msg_id in forwarded_messages:
        # Admin is replying directly to the user message
        original_user_id = forwarded_messages[replied_msg_id]
        original_msg_id = original_messages.get(replied_msg_id)
    elif admin_id in admin_info_messages and replied_msg_id == admin_info_messages[admin_id]:
        # Admin is replying to the info message
        # Try to find the next message from this user
        for msg_id, user_id in forwarded_messages.items():
            if user_id not in ADMIN_IDS:
                original_user_id = user_id
                original_msg_id = original_messages.get(msg_id)
                break
        else:
            # Could not find a user message
            await update.message.reply_text("❌ لا يمكن العثور على المستخدم الأصلي لهذه الرسالة")
            return
    else:
        # Not a reply to a user message or info message
        return
    
    try:
        # Get the original message ID if available
        
        # Forward the admin's reply to the original user
        if original_msg_id:
            # Reply directly to the user's original message
            sent_msg = await context.bot.send_message(
                chat_id=original_user_id,
                text=update.message.text,
                reply_to_message_id=original_msg_id
            )
        else:
            # Fallback if original message ID is not available
            sent_msg = await context.bot.send_message(
                chat_id=original_user_id,
                text=update.message.text
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

async def setup_commands(application: Application) -> None:
    """Set bot commands that will appear in the menu."""
    commands = [
        ("start", "بدء المحادثة مع البوت"),
        ("help", "عرض المساعدة"),
    ]
    
    await application.bot.set_my_commands(commands)
    logger.info("Bot commands have been set")

def main() -> None:
    """Start the bot."""
    # Keep the bot alive
    keep_alive()
    
    # Create the Application
    application = Application.builder().token(BOT_TOKEN).build()

    # Add command handlers
    application.add_handler(CommandHandler("start", start_command))
    
    # Add message handlers
    application.add_handler(MessageHandler(filters.REPLY & filters.TEXT & ~filters.COMMAND & filters.User(ADMIN_IDS), handle_admin_reply))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND & ~filters.ChatType.CHANNEL & ~filters.ChatType.GROUP, handle_user_message))

    # Setup bot on startup
    application.post_init = setup_commands
    application.post_shutdown = set_menu_button
    
    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    if not BOT_TOKEN:
        logger.error("BOT_TOKEN environment variable is not set!")
        exit(1)
    if not ADMIN_IDS:
        logger.warning("ADMIN_IDS environment variable is not set or empty. No admins configured!")
    main()