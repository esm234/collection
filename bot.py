#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import logging
from typing import Dict, List, Union, Tuple, Set
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, MenuButtonCommands
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackContext,
    filters,
)
import telegram

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

# Maps: user_id -> admin_id who is handling this user
user_handlers: Dict[int, int] = {}

# Maps: admin_msg_id -> original_msg_id (user's message ID)
original_messages: Dict[int, int] = {}

# Maps: user message ID -> admin who sent the message
admin_messages_to_users: Dict[int, int] = {}

# Maps: admin_id -> last_info_message_id
admin_info_messages: Dict[int, int] = {}

# Maps: user_message_id -> admin_message_id (for reply tracking)
user_to_admin_messages: Dict[int, int] = {}

# Maps: admin_message_id -> user_message_id (for reply tracking)
admin_to_user_messages: Dict[int, int] = {}

# Maps: admin_id -> admin name
admin_names: Dict[int, str] = {}

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
    
    # Reset any previous handler for this user
    if update.effective_user.id in user_handlers:
        del user_handlers[update.effective_user.id]
    
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
            
            # Mark this admin as the handler for this user
            user_handlers[user_id] = admin_id
            
            try:
                # Find the original admin message ID that this is a reply to
                admin_msg_id = None
                for a_msg_id, u_msg_id in admin_to_user_messages.items():
                    if u_msg_id == replied_msg_id:
                        admin_msg_id = a_msg_id
                        break
                
                # Send the user's reply to the admin
                if admin_msg_id:
                    # Reply directly to the admin's original message
                    admin_msg = await context.bot.send_message(
                        chat_id=admin_id,
                        text=message.text,
                        reply_to_message_id=admin_msg_id
                    )
                else:
                    # Fallback if we can't find the original admin message
                    admin_msg = await context.bot.send_message(
                        chat_id=admin_id,
                        text=message.text
                    )
                
                # Store the mapping between admin message ID and original user ID
                forwarded_messages[admin_msg.message_id] = user_id
                
                # Store the mapping between admin message ID and original message ID
                original_messages[admin_msg.message_id] = message.message_id
                
                # Store the mapping between user message and this admin message
                user_to_admin_messages[message.message_id] = admin_msg.message_id
                
                # Confirm receipt to the user
                await message.reply_text("✅ تم إرسال ردك للمشرف")
                
                # Log the successful reply
                logger.info(f"User {user_id} replied to admin {admin_id}, message sent")
                
            except Exception as e:
                logger.error(f"Failed to send reply to admin {admin_id}: {e}")
                await message.reply_text("❌ حدث خطأ في إرسال ردك")
            
            return
    
    # If not a reply or reply to non-admin message, treat as a new message
    
    # Check if this user already has a handler (admin)
    if user_id in user_handlers:
        # Only send to the assigned admin
        admin_id = user_handlers[user_id]
        
        try:
            # Send user message directly to the assigned admin
            admin_msg = await context.bot.send_message(
                chat_id=admin_id,
                text=message.text
            )
            
            # Store the mapping between admin message ID and original user ID
            forwarded_messages[admin_msg.message_id] = user_id
            
            # Store the mapping between admin message ID and original message ID
            original_messages[admin_msg.message_id] = message.message_id
            
            # Store the mapping between user message and this admin message
            user_to_admin_messages[message.message_id] = admin_msg.message_id
            
            # Confirm receipt to the user
            await message.reply_text("✅ تم إرسال رسالتك للمشرف")
            
        except Exception as e:
            logger.error(f"Failed to send message to admin {admin_id}: {e}")
            await message.reply_text("❌ حدث خطأ في إرسال رسالتك")
        
        return
    
    # If no handler assigned yet, forward to all admins
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
            
            # Store the mapping between user message and this admin message
            user_to_admin_messages[message.message_id] = admin_msg.message_id
            
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
    
    # Store admin name for future reference
    admin_name = update.effective_user.first_name
    admin_names[admin_id] = admin_name
    
    # Check if this is a reply to a message
    if not update.message.reply_to_message:
        return
    
    replied_msg_id = update.message.reply_to_message.message_id
    
    # Check if the admin is replying to a user message or to the info message
    if replied_msg_id in forwarded_messages:
        # Admin is replying directly to the user message
        original_user_id = forwarded_messages[replied_msg_id]
        original_msg_id = original_messages.get(replied_msg_id)
        
        # Mark this admin as the handler for this user
        user_handlers[original_user_id] = admin_id
        
    elif admin_id in admin_info_messages and replied_msg_id == admin_info_messages[admin_id]:
        # Admin is replying to the info message
        # Try to find the next message from this user
        for msg_id, user_id in forwarded_messages.items():
            if user_id not in ADMIN_IDS:
                original_user_id = user_id
                original_msg_id = original_messages.get(msg_id)
                
                # Mark this admin as the handler for this user
                user_handlers[original_user_id] = admin_id
                
                break
        else:
            # Could not find a user message
            await update.message.reply_text("❌ لا يمكن العثور على المستخدم الأصلي لهذه الرسالة")
            return
    else:
        # Not a reply to a user message or info message
        return
    
    try:
        # Forward the admin's reply to the original user
        if original_msg_id:
            # Reply directly to the user's original message without any prefix text
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
        user_handlers[original_user_id] = admin_id
        
        # Store the message mapping for tracking replies - use sent_msg.message_id as key
        admin_messages_to_users[sent_msg.message_id] = admin_id
        
        # Store the mapping between admin message and user message
        admin_to_user_messages[update.message.message_id] = sent_msg.message_id
        
        # Notify other admins that this conversation is being handled
        for other_admin_id in ADMIN_IDS:
            if other_admin_id != admin_id:
                try:
                    await context.bot.send_message(
                        chat_id=other_admin_id,
                        text=f"ℹ️ المستخدم {original_user_id} يتم التعامل معه حالياً بواسطة المشرف {admin_name}"
                    )
                except Exception as e:
                    logger.error(f"Failed to notify admin {other_admin_id}: {e}")
        
        # Log the successful admin reply
        logger.info(f"Admin {admin_id} replied to user {original_user_id}, message sent")
        
        await update.message.reply_text("✅ تم إرسال ردك للمستخدم")
        
    except Exception as e:
        logger.error(f"Failed to send admin reply to user {original_user_id}: {e}")
        await update.message.reply_text(f"❌ فشل إرسال الرد: {e}")

async def release_user_command(update: Update, context: CallbackContext) -> None:
    """Release a user from being handled by an admin."""
    # Only process commands from admins
    admin_id = update.effective_user.id
    if admin_id not in ADMIN_IDS:
        return
    
    # Check if there's a user ID in the command arguments
    if not context.args or not context.args[0].isdigit():
        await update.message.reply_text("❌ يرجى تحديد معرف المستخدم الذي تريد تحريره. مثال: /release 123456789")
        return
    
    user_id = int(context.args[0])
    
    # Check if this user is being handled
    if user_id in user_handlers:
        handler_admin_id = user_handlers[user_id]
        
        # Check if the requesting admin is the handler
        if handler_admin_id == admin_id:
            # Get admin name
            admin_name = admin_names.get(admin_id, "المشرف")
            
            # Notify the user that they are being released
            try:
                await context.bot.send_message(
                    chat_id=user_id,
                    text=f"⚠️ المشرف {admin_name} غير متوفر حالياً. سيتم تحويلك لمشرف آخر في أقرب وقت."
                )
            except Exception as e:
                logger.error(f"Failed to notify user {user_id} about release: {e}")
            
            # Remove the handler
            del user_handlers[user_id]
            
            # Notify all admins
            for admin_id in ADMIN_IDS:
                try:
                    await context.bot.send_message(
                        chat_id=admin_id,
                        text=f"ℹ️ المستخدم {user_id} متاح الآن للرد من قبل أي مشرف"
                    )
                except Exception as e:
                    logger.error(f"Failed to notify admin {admin_id}: {e}")
            
            await update.message.reply_text(f"✅ تم تحرير المستخدم {user_id} وأصبح متاحاً للرد من قبل أي مشرف")
        else:
            admin_name = admin_names.get(handler_admin_id, "مشرف آخر")
            await update.message.reply_text(f"❌ لا يمكنك تحرير هذا المستخدم لأنه يتم التعامل معه حالياً بواسطة {admin_name}")
    else:
        await update.message.reply_text(f"ℹ️ المستخدم {user_id} غير مخصص لأي مشرف حالياً")

async def setup_commands(application: Application) -> None:
    """Set bot commands that will appear in the menu."""
    # Commands for regular users
    user_commands = [
        ("start", "بدء المحادثة مع البوت"),
        ("help", "عرض المساعدة"),
    ]
    
    # Commands for admin users (including release command)
    admin_commands = [
        ("start", "بدء المحادثة مع البوت"),
        ("help", "عرض المساعدة"),
        ("release", "تحرير مستخدم من المشرف الحالي")
    ]
    
    # Set commands for regular users (globally)
    await application.bot.set_my_commands(user_commands)
    
    # Set admin-specific commands for each admin
    for admin_id in ADMIN_IDS:
        try:
            await application.bot.set_my_commands(
                admin_commands,
                scope=telegram.BotCommandScopeChat(chat_id=admin_id)
            )
        except Exception as e:
            logger.error(f"Failed to set admin commands for admin {admin_id}: {e}")
    
    logger.info("Bot commands have been set")

def main() -> None:
    """Start the bot."""
    # Create the Application
    application = Application.builder().token(BOT_TOKEN).build()

    # Add command handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("release", release_user_command))
    
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