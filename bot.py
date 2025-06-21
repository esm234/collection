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
import json
from datetime import datetime

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Bot configuration
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_GROUP_ID = int(os.getenv("ADMIN_GROUP_ID", "0"))

# In-memory storage
# Maps: group_msg_id -> original_user_id
forwarded_messages: Dict[int, int] = {}

# Maps: group_msg_id -> original_msg_id (user's message ID)
original_messages: Dict[int, int] = {}

# Maps: user message ID -> group message ID (for tracking)
user_to_group_messages: Dict[int, int] = {}

# Maps: group_message_id -> user_message_id (for tracking)
group_to_user_messages: Dict[int, int] = {}

# User tracking
active_users: Dict[int, dict] = {}
USERS_FILE = "users_data.json"

# Load existing users data if available
def load_users_data():
    try:
        if os.path.exists(USERS_FILE):
            with open(USERS_FILE, 'r', encoding='utf-8') as file:
                return json.load(file)
        return {}
    except Exception as e:
        logger.error(f"Failed to load users data: {e}")
        return {}

# Save users data to file
def save_users_data():
    try:
        with open(USERS_FILE, 'w', encoding='utf-8') as file:
            json.dump(active_users, file, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Failed to save users data: {e}")

# Initialize users data
active_users = load_users_data()

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
            InlineKeyboardButton("جروب المناقشة", url="https://t.me/ourgoul1"),
            InlineKeyboardButton("القناة الرئيسية", url="https://t.me/our_goal_is_success"),
        ],
        [
            InlineKeyboardButton("بوت الملفات", url="https://t.me/our_goal_bot"),
            InlineKeyboardButton("الموقع الإلكتروني", url="https://ourgoal.site"),
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
    
    # Track user
    user_id = user.id
    if str(user_id) not in active_users:
        active_users[str(user_id)] = {
            "first_name": user.first_name,
            "last_name": user.last_name or "",
            "username": user.username or "",
            "first_seen": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "last_active": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "message_count": 0
        }
    else:
        active_users[str(user_id)]["last_active"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    save_users_data()
    
    await update.message.reply_text(welcome_message, reply_markup=reply_markup)

async def stats_command(update: Update, context: CallbackContext) -> None:
    """Show bot statistics."""
    # Only process if message is from the admin group
    if update.effective_chat.id != ADMIN_GROUP_ID:
        return
    
    # Count total users and active users (active in the last 30 days)
    total_users = len(active_users)
    
    # Generate stats message
    stats_message = f"📊 <b>إحصائيات البوت</b>\n\n"
    stats_message += f"👥 <b>إجمالي المستخدمين:</b> {total_users}\n"
    
    # Total messages processed
    total_messages = sum(user.get("message_count", 0) for user in active_users.values())
    stats_message += f"💬 <b>إجمالي الرسائل:</b> {total_messages}\n\n"
    
    # Show the most recent users
    stats_message += "<b>آخر المستخدمين النشطين:</b>\n"
    
    # Sort users by last active time (most recent first)
    recent_users = sorted(
        active_users.items(),
        key=lambda x: x[1].get("last_active", ""),
        reverse=True
    )[:10]  # Get top 10
    
    for i, (user_id, user_data) in enumerate(recent_users, 1):
        name = user_data.get("first_name", "")
        username = user_data.get("username", "")
        last_active = user_data.get("last_active", "")
        msg_count = user_data.get("message_count", 0)
        
        username_text = f" (@{username})" if username else ""
        stats_message += f"{i}. {name}{username_text} - {msg_count} رسالة - آخر نشاط: {last_active}\n"
    
    await update.message.reply_text(stats_message, parse_mode="HTML")

async def forward_to_admin_group(update: Update, context: CallbackContext, user_id: int, message_text: str = None) -> None:
    """Forward a message to the admin group and handle the mapping."""
    message = update.message
    
    # Forward the message directly to the admin group
    try:
        forwarded_msg = await context.bot.forward_message(
            chat_id=ADMIN_GROUP_ID,
            from_chat_id=message.chat_id,
            message_id=message.message_id
        )
        
        # Store mappings
        forwarded_messages[forwarded_msg.message_id] = user_id
        original_messages[forwarded_msg.message_id] = message.message_id
        user_to_group_messages[message.message_id] = forwarded_msg.message_id
        
        return forwarded_msg
    except Exception as e:
        logger.error(f"Failed to forward message: {e}")
        raise e

async def handle_user_message(update: Update, context: CallbackContext) -> None:
    """Handle all messages from users and forward them to the admin group."""
    # Skip messages from the admin group
    if update.effective_chat.id == ADMIN_GROUP_ID:
        return
    
    user = update.effective_user
    user_id = user.id
    message = update.message
    
    # Track user activity
    str_user_id = str(user_id)
    if str_user_id not in active_users:
        active_users[str_user_id] = {
            "first_name": user.first_name,
            "last_name": user.last_name or "",
            "username": user.username or "",
            "first_seen": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "last_active": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "message_count": 1
        }
    else:
        active_users[str_user_id]["last_active"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        active_users[str_user_id]["message_count"] = active_users[str_user_id].get("message_count", 0) + 1
    
    save_users_data()
    
    # Check if this is a reply to a message from the bot
    if message.reply_to_message:
        replied_msg_id = message.reply_to_message.message_id
        
        # Try to find the original group message this is a reply to
        group_msg_id = None
        for g_msg_id, u_msg_id in group_to_user_messages.items():
            if u_msg_id == replied_msg_id:
                group_msg_id = g_msg_id
                break
        
        if group_msg_id:
            try:
                # Send as a reply to the original message in the group
                user_name = f"{user.first_name} {user.last_name if user.last_name else ''}"
                
                if message.text:
                    # For text messages
                    reply_text = f"<b>رد من المستخدم {user_name}:</b>\n{message.text}"
                    group_msg = await context.bot.send_message(
                        chat_id=ADMIN_GROUP_ID,
                        text=reply_text,
                        reply_to_message_id=group_msg_id,
                        parse_mode="HTML"
                    )
                elif message.photo:
                    # For photos
                    caption = f"<b>رد من المستخدم {user_name}:</b>\n{message.caption or ''}"
                    group_msg = await context.bot.send_photo(
                        chat_id=ADMIN_GROUP_ID,
                        photo=message.photo[-1].file_id,
                        caption=caption,
                        reply_to_message_id=group_msg_id,
                        parse_mode="HTML"
                    )
                elif message.document:
                    # For documents
                    caption = f"<b>رد من المستخدم {user_name}:</b>\n{message.caption or ''}"
                    group_msg = await context.bot.send_document(
                        chat_id=ADMIN_GROUP_ID,
                        document=message.document.file_id,
                        caption=caption,
                        reply_to_message_id=group_msg_id,
                        parse_mode="HTML"
                    )
                elif message.video:
                    # For videos
                    caption = f"<b>رد من المستخدم {user_name}:</b>\n{message.caption or ''}"
                    group_msg = await context.bot.send_video(
                        chat_id=ADMIN_GROUP_ID,
                        video=message.video.file_id,
                        caption=caption,
                        reply_to_message_id=group_msg_id,
                        parse_mode="HTML"
                    )
                elif message.voice:
                    # For voice messages
                    caption = f"<b>رد من المستخدم {user_name}:</b>\n{message.caption or ''}"
                    group_msg = await context.bot.send_voice(
                        chat_id=ADMIN_GROUP_ID,
                        voice=message.voice.file_id,
                        caption=caption,
                        reply_to_message_id=group_msg_id,
                        parse_mode="HTML"
                    )
                elif message.audio:
                    # For audio messages
                    caption = f"<b>رد من المستخدم {user_name}:</b>\n{message.caption or ''}"
                    group_msg = await context.bot.send_audio(
                        chat_id=ADMIN_GROUP_ID,
                        audio=message.audio.file_id,
                        caption=caption,
                        reply_to_message_id=group_msg_id,
                        parse_mode="HTML"
                    )
                elif message.sticker:
                    # For stickers
                    # First send the "reply from user" message
                    info_msg = await context.bot.send_message(
                        chat_id=ADMIN_GROUP_ID,
                        text=f"<b>رد من المستخدم {user_name}:</b>",
                        reply_to_message_id=group_msg_id,
                        parse_mode="HTML"
                    )
                    # Then send the sticker
                    group_msg = await context.bot.send_sticker(
                        chat_id=ADMIN_GROUP_ID,
                        sticker=message.sticker.file_id,
                        reply_to_message_id=info_msg.message_id
                    )
                else:
                    # For other types
                    reply_text = f"<b>رد من المستخدم {user_name}:</b>\n⚠️ نوع رسالة غير مدعوم"
                    group_msg = await context.bot.send_message(
                        chat_id=ADMIN_GROUP_ID,
                        text=reply_text,
                        reply_to_message_id=group_msg_id,
                        parse_mode="HTML"
                    )
                
                # Store mappings
                forwarded_messages[group_msg.message_id] = user_id
                original_messages[group_msg.message_id] = message.message_id
                user_to_group_messages[message.message_id] = group_msg.message_id
                
                # Confirm receipt to the user
                await message.reply_text("✅ تم إرسال ردك للمشرفين")
                
                logger.info(f"User {user_id} replied to a message, sent to admin group")
                
            except Exception as e:
                logger.error(f"Failed to send reply to admin group: {e}")
                await message.reply_text("❌ حدث خطأ في إرسال ردك")
            
            return
    
    # If not a reply or couldn't find the original message, treat as a new message
    try:
        await forward_to_admin_group(update, context, user_id)
        
        # Confirm receipt to the user
        await message.reply_text("تم استلام رسالتك وسيتم الرد عليك في أقرب وقت ✅")
        
        logger.info(f"User {user_id} sent a new message, forwarded to admin group")
        
    except Exception as e:
        logger.error(f"Failed to forward message to admin group: {e}")
        await message.reply_text("❌ حدث خطأ في إرسال رسالتك")

async def handle_admin_group_reply(update: Update, context: CallbackContext) -> None:
    """Handle replies from the admin group to forward them back to the original user."""
    # Only process messages from the admin group
    if update.effective_chat.id != ADMIN_GROUP_ID:
        return
    
    # Check if this is a reply to a message
    if not update.message.reply_to_message:
        return
    
    replied_msg_id = update.message.reply_to_message.message_id
    
    # Check if the admin is replying to a user message
    if replied_msg_id in forwarded_messages:
        # Admin is replying directly to the user message
        original_user_id = forwarded_messages[replied_msg_id]
        original_msg_id = original_messages.get(replied_msg_id)
        
    else:
        # Check if there's a forwarded message that's a reply to this message
        # This handles the case when admin replies to the user info message
        for msg_id, user_id in forwarded_messages.items():
            try:
                # Try to find messages that were sent as replies to the message the admin is replying to
                msg = await context.bot.get_chat_message(
                    chat_id=ADMIN_GROUP_ID,
                    message_id=msg_id
                )
                
                if msg.reply_to_message and msg.reply_to_message.message_id == replied_msg_id:
                    original_user_id = user_id
                    original_msg_id = original_messages.get(msg_id)
                    break
            except Exception as e:
                logger.error(f"Error checking message {msg_id}: {e}")
                continue
        else:
            # Could not find a user message
            await update.message.reply_text("❌ لا يمكن العثور على المستخدم الأصلي لهذه الرسالة")
            return
    
    try:
        # Forward the admin's reply to the original user
        message = update.message
        
        # Forward the message to the user
        sent_msg = await context.bot.copy_message(
            chat_id=original_user_id,
            from_chat_id=ADMIN_GROUP_ID,
            message_id=message.message_id,
            reply_to_message_id=original_msg_id if original_msg_id else None
        )
        
        # Store the mapping between group message and user message
        group_to_user_messages[update.message.message_id] = sent_msg.message_id
        
        # Log the successful admin reply
        logger.info(f"Admin replied to user {original_user_id}, message sent")
        
        # React to the admin's message to indicate it was sent
        try:
            await update.message.react("✅")
        except Exception as e:
            logger.error(f"Failed to react to admin message: {e}")
        
    except Exception as e:
        logger.error(f"Failed to send admin reply to user {original_user_id}: {e}")
        await update.message.reply_text(f"❌ فشل إرسال الرد: {e}")

async def setup_commands(application: Application) -> None:
    """Set bot commands that will appear in the menu."""
    # Commands for regular users
    user_commands = [
        ("start", "بدء المحادثة مع البوت"),
        ("help", "عرض المساعدة"),
    ]
    
    # Set commands for regular users (globally)
    await application.bot.set_my_commands(user_commands)
    
    logger.info("Bot commands have been set")

def main() -> None:
    """Start the bot."""
    # Create the Application
    application = Application.builder().token(BOT_TOKEN).build()

    # Add command handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("stats", stats_command))
    
    # Add message handlers for admin group
    application.add_handler(MessageHandler(
        filters.REPLY & ~filters.COMMAND & filters.Chat(chat_id=ADMIN_GROUP_ID),
        handle_admin_group_reply
    ))
    
    # Add message handlers for user messages (all types)
    application.add_handler(MessageHandler(
        ~filters.COMMAND & ~filters.ChatType.CHANNEL & ~filters.ChatType.GROUP,
        handle_user_message
    ))

    # Setup bot on startup
    application.post_init = setup_commands
    application.post_shutdown = set_menu_button
    
    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    if not BOT_TOKEN:
        logger.error("BOT_TOKEN environment variable is not set!")
        exit(1)
    if not ADMIN_GROUP_ID or ADMIN_GROUP_ID == 0:
        logger.error("ADMIN_GROUP_ID environment variable is not set or invalid!")
        exit(1)
    main() 