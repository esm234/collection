#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import logging
import uuid
import asyncio
from typing import Dict, List, Union, Tuple, Set
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, MenuButtonCommands, BotCommand, BotCommandScopeAllPrivateChats, BotCommandScopeChat
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackContext,
    CallbackQueryHandler,
    filters,
)
from telegram.constants import ParseMode
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

# Data storage files
DATA_FILE = 'questions_data.json'
REPLIES_FILE = 'replies_data.json'
USERS_FILE = "users_data.json"
BANS_FILE = "banned_users.json"

# In-memory storage for question tracking
questions_data: Dict[str, dict] = {}
replies_data: Dict[str, dict] = {}
waiting_for_broadcast: Dict[int, bool] = {}
banned_users: Dict[str, dict] = {}

# Legacy mappings for backward compatibility
forwarded_messages: Dict[int, int] = {}
original_messages: Dict[int, int] = {}
user_to_group_messages: Dict[int, int] = {}
group_to_user_messages: Dict[int, int] = {}

# User tracking
active_users: Dict[int, dict] = {}

# Load data from files
def load_data(filename: str) -> Dict:
    try:
        if os.path.exists(filename):
            with open(filename, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    except Exception as e:
        logger.error(f"Failed to load {filename}: {e}")
        return {}

# Save data to files
def save_data(data: Dict, filename: str):
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Failed to save {filename}: {e}")

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

# Initialize data
questions_data = load_data(DATA_FILE)
replies_data = load_data(REPLIES_FILE)
banned_users = load_data(BANS_FILE)
active_users = load_users_data()

# Helper functions for question management
def get_user_questions(user_id: int) -> List[Dict]:
    """Get all questions from a specific user"""
    return [q for q in questions_data.values() if q['user_id'] == user_id]

def get_all_user_ids() -> List[int]:
    """Get all unique user IDs who have sent questions"""
    return list(set(q['user_id'] for q in questions_data.values()))

def is_user_banned(user_id: int) -> bool:
    """Check if a user is banned"""
    return str(user_id) in banned_users

def ban_user(user_id: int, admin_id: int, reason: str = "No reason provided") -> bool:
    """Ban a user"""
    try:
        banned_users[str(user_id)] = {
            'banned_at': datetime.now().isoformat(),
            'banned_by': admin_id,
            'reason': reason
        }
        save_data(banned_users, BANS_FILE)
        return True
    except Exception as e:
        logger.error(f"Failed to ban user {user_id}: {e}")
        return False

def unban_user(user_id: int) -> bool:
    """Unban a user"""
    try:
        if str(user_id) in banned_users:
            del banned_users[str(user_id)]
            save_data(banned_users, BANS_FILE)
            return True
        return False
    except Exception as e:
        logger.error(f"Failed to unban user {user_id}: {e}")
        return False

def get_banned_users() -> List[Dict]:
    """Get list of all banned users with details"""
    banned_list = []
    for user_id, ban_data in banned_users.items():
        banned_list.append({
            'user_id': int(user_id),
            'banned_at': ban_data.get('banned_at', 'Unknown'),
            'banned_by': ban_data.get('banned_by', 'Unknown'),
            'reason': ban_data.get('reason', 'No reason provided')
        })
    return banned_list

async def set_menu_button(application: Application) -> None:
    """Set the menu button to show commands."""
    try:
        await application.bot.set_chat_menu_button(
            menu_button=MenuButtonCommands(type="commands")
        )
        logger.info("Menu button set to commands")
    except Exception as e:
        logger.error(f"Failed to set menu button: {e}")

async def start_command(update: Update, context: CallbackContext) -> None:
    """Send welcome message when the command /start is issued."""
    user = update.effective_user
    if not user or not update.message:
        return
    
    # Create inline keyboard with instructions and orders list
    keyboard = [
        [InlineKeyboardButton("📋 قائمة الطلبات", callback_data="orders_list")],
        [InlineKeyboardButton("ℹ️ تعليمات الاستخدام", callback_data="instructions")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    user_name = user.first_name or "المستخدم"
    welcome_message = f"""
🎓 أهلاً وسهلاً {user_name}!

مرحباً بك في **بوت التجميعات** 📚

هذا البوت مخصص لتجميع أسئلة اختبار القدرات الجديدة .

📤 **يمكنك إرسال:**
• النصوص
• الصور
• ملفات PDF
• الرسائل الصوتية

✅ سيتم استلام جميع رسائلك وتوجيهها للفريق المختص لمراجعتها وتنظيمها.

استخدم الأزرار أدناه للمزيد من المعلومات:
"""
    
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
    
    await update.message.reply_text(
        welcome_message,
        reply_markup=reply_markup,
        parse_mode=ParseMode.MARKDOWN
    )

async def button_handler(update: Update, context: CallbackContext) -> None:
    """Handle inline keyboard button presses"""
    query = update.callback_query
    if not query or not query.from_user:
        return
    await query.answer()
    
    if query.data == "orders_list":
        user_id = query.from_user.id
        user_questions = get_user_questions(user_id)
        
        if not user_questions:
            await query.edit_message_text("📋 لم ترسل أي أسئلة بعد.")
            return
        
        orders_text = f"📋 **قائمة أسئلتك:** ({len(user_questions)} سؤال)\n\n"
        
        for i, question in enumerate(user_questions, 1):
            timestamp = datetime.fromisoformat(question['timestamp']).strftime('%Y-%m-%d %H:%M')
            content_preview = question['content'][:50] + "..." if len(question['content']) > 50 else question['content']
            orders_text += f"{i}. **{question['message_type']}** - {timestamp}\n   {content_preview}\n\n"
        
        # Add back button
        keyboard = [[InlineKeyboardButton("🔙 العودة للقائمة الرئيسية", callback_data="main_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            orders_text,
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN
        )
    
    elif query.data == "instructions":
        instructions_text = """
ℹ️ **تعليمات الاستخدام:**

📤 **لإرسال سؤال:**
• اكتب السؤال كنص عادي
• أرسل صورة للسؤال
• أرفق ملف PDF
• سجل رسالة صوتية

✅ **بعد الإرسال:**
• ستحصل على رسالة تأكيد
• سيتم توجيه سؤالك للفريق المختص

💬 **الردود:**
• إذا رد عليك الفريق، ستحصل على إشعار
• يمكنك الرد على ردهم مباشرة
• سيتم توصيل ردك للفريق تلقائياً

📋 **لعرض أسئلتك:**
• اضغط على "قائمة الطلبات" في القائمة الرئيسية

🔄 **للعودة للقائمة الرئيسية:**
• اكتب /start في أي وقت
"""
        
        keyboard = [[InlineKeyboardButton("🔙 العودة للقائمة الرئيسية", callback_data="main_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            instructions_text,
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN
        )
    
    elif query.data == "main_menu":
        # Return to main menu
        await start_command(update, context)

async def stats_command(update: Update, context: CallbackContext) -> None:
    """Show bot statistics."""
    # Only process if message is from the admin group
    if update.effective_chat.id != ADMIN_GROUP_ID:
        return
    
    if not update.message:
        return
    
    total_questions = len(questions_data)
    unique_users = len(set(q['user_id'] for q in questions_data.values()))
    
    # Count by message type
    type_counts = {}
    for question in questions_data.values():
        msg_type = question['message_type']
        type_counts[msg_type] = type_counts.get(msg_type, 0) + 1
    
    stats_text = f"""📊 **إحصائيات البوت:**

📝 العدد الكلي للأسئلة: {total_questions}
👥 عدد المستخدمين: {unique_users}

📋 **توزيع أنواع الرسائل:**
"""
    
    for msg_type, count in type_counts.items():
        stats_text += f"• {msg_type}: {count}\n"
    
    await update.message.reply_text(stats_text, parse_mode=ParseMode.MARKDOWN)

async def export_command(update: Update, context: CallbackContext) -> None:
    """Export all data as JSON files (admin only)"""
    if not update.effective_chat or update.effective_chat.id != ADMIN_GROUP_ID:
        return
    
    if not update.message:
        return
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    try:
        # Export questions data
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, 'rb') as f:
                await update.message.reply_document(
                    document=f,
                    filename=f"questions_data_{timestamp}.json",
                    caption="📁 ملف بيانات الأسئلة"
                )
        
        # Export replies data
        if os.path.exists(REPLIES_FILE):
            with open(REPLIES_FILE, 'rb') as f:
                await update.message.reply_document(
                    document=f,
                    filename=f"replies_data_{timestamp}.json",
                    caption="📁 ملف بيانات الردود"
                )
        
        # Export users data
        if os.path.exists(USERS_FILE):
            with open(USERS_FILE, 'rb') as f:
                await update.message.reply_document(
                    document=f,
                    filename=f"users_data_{timestamp}.json",
                    caption="📁 ملف بيانات المستخدمين"
                )
        
        # Export banned users data
        if os.path.exists(BANS_FILE):
            with open(BANS_FILE, 'rb') as f:
                await update.message.reply_document(
                    document=f,
                    filename=f"banned_users_{timestamp}.json",
                    caption="📁 ملف المستخدمين المحظورين"
                )
        
        # Send summary message
        await update.message.reply_text(
            f"✅ **تم تصدير جميع البيانات بنجاح**\n\n"
            f"📊 **ملخص البيانات:**\n"
            f"• الأسئلة: {len(questions_data)} سؤال\n"
            f"• الردود: {len(replies_data)} محادثة\n"
            f"• المستخدمين: {len(active_users)} مستخدم\n"
            f"• المحظورين: {len(banned_users)} مستخدم\n\n"
            f"⏰ **وقت التصدير:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            parse_mode=ParseMode.MARKDOWN
        )
        
    except Exception as e:
        await update.message.reply_text(f"❌ خطأ في التصدير: {e}")

async def broadcast_command(update: Update, context: CallbackContext) -> None:
    """Start broadcast mode (admin only)"""
    if not update.effective_chat or update.effective_chat.id != ADMIN_GROUP_ID:
        return
    
    if not update.effective_user or not update.message:
        return
    
    # Get current user count
    user_count = len(get_all_user_ids())
    
    waiting_for_broadcast[update.effective_user.id] = True
    await update.message.reply_text(
        f"📢 **وضع البث الجماعي**\n\n"
        f"📈 عدد المستقبلين: {user_count} مستخدم\n\n"
        f"📝 أرسل الرسالة الآن:\n"
        f"• نصوص\n"
        f"• صور (مع أو بدون وصف)\n"
        f"• ملفات PDF\n"
        f"• رسائل صوتية\n"
        f"• ملفات صوتية\n"
        f"• فيديوهات\n"
        f"• ملصقات",
        parse_mode=ParseMode.MARKDOWN
    )

async def help_command(update: Update, context: CallbackContext) -> None:
    """Help command handler"""
    if not update.message:
        return
    
    chat = update.effective_chat
    if chat and chat.id == ADMIN_GROUP_ID:
        help_text = (
            "👨‍💼 **مساعدة المشرفين (جروب الادمن):**\n\n"
            "• /stats — إحصائيات الأسئلة\n"
            "• /export — تصدير جميع البيانات (JSON)\n"
            "• /broadcast — بث رسالة لكل المستخدمين\n"
            "• /ban <user_id> [reason] — حظر مستخدم\n"
            "• /unban <user_id> — إلغاء حظر مستخدم\n"
            "• /banned — قائمة المستخدمين المحظورين\n\n"
            "🔁 للرد على الطلاب: قم بالرد على رسالة البوت المرتبطة بالسؤال أو على الرسائل الموجهة من الطالب وسيتم توجيه ردك مباشرة.\n"
            "♾️ النظام يدعم محادثة مستمرة ذهاباً وإياباً."
        )
    else:
        help_text = (
            "🤖 **مساعدة المستخدم:**\n\n"
            "• /start — بدء استخدام البوت\n"
            "• /help — عرض المساعدة\n\n"
            "📤 أرسل سؤالك كنص/صورة/ملف/صوت وسنقوم بتوصيله للادمن.\n"
            "🔔 ستصلك ردود الادمن ويمكنك الرد عليها وسيتم إيصالها لهم."
        )
    
    await update.message.reply_text(help_text, parse_mode=ParseMode.MARKDOWN)

async def ban_command(update: Update, context: CallbackContext) -> None:
    """Ban a user (admin only)"""
    if not update.effective_chat or update.effective_chat.id != ADMIN_GROUP_ID:
        return
    
    if not update.message:
        return
    
    # Check if user ID is provided
    if not context.args:
        await update.message.reply_text(
            "❌ يجب توفير معرف المستخدم\n"
            "الاستخدام: /ban <user_id> [reason]\n"
            "مثال: /ban 123456789 إرسال محتوى غير مناسب"
        )
        return
    
    try:
        user_id = int(context.args[0])
        reason = " ".join(context.args[1:]) if len(context.args) > 1 else "No reason provided"
        
        # Check if user is already banned
        if is_user_banned(user_id):
            await update.message.reply_text(f"❌ المستخدم {user_id} محظور بالفعل")
            return
        
        # Ban the user
        if ban_user(user_id, update.effective_user.id, reason):
            await update.message.reply_text(
                f"✅ تم حظر المستخدم {user_id}\n"
                f"السبب: {reason}\n"
                f"بواسطة: {update.effective_user.first_name}"
            )
        else:
            await update.message.reply_text(f"❌ فشل في حظر المستخدم {user_id}")
            
    except ValueError:
        await update.message.reply_text("❌ معرف المستخدم غير صحيح")

async def unban_command(update: Update, context: CallbackContext) -> None:
    """Unban a user (admin only)"""
    if not update.effective_chat or update.effective_chat.id != ADMIN_GROUP_ID:
        return
    
    if not update.message:
        return
    
    # Check if user ID is provided
    if not context.args:
        await update.message.reply_text(
            "❌ يجب توفير معرف المستخدم\n"
            "الاستخدام: /unban <user_id>\n"
            "مثال: /unban 123456789"
        )
        return
    
    try:
        user_id = int(context.args[0])
        
        # Check if user is banned
        if not is_user_banned(user_id):
            await update.message.reply_text(f"❌ المستخدم {user_id} غير محظور")
            return
        
        # Unban the user
        if unban_user(user_id):
            await update.message.reply_text(
                f"✅ تم إلغاء حظر المستخدم {user_id}\n"
                f"بواسطة: {update.effective_user.first_name}"
            )
        else:
            await update.message.reply_text(f"❌ فشل في إلغاء حظر المستخدم {user_id}")
            
    except ValueError:
        await update.message.reply_text("❌ معرف المستخدم غير صحيح")

async def banned_list_command(update: Update, context: CallbackContext) -> None:
    """Show list of banned users (admin only)"""
    if not update.effective_chat or update.effective_chat.id != ADMIN_GROUP_ID:
        return
    
    if not update.message:
        return
    
    banned_list = get_banned_users()
    
    if not banned_list:
        await update.message.reply_text("📋 لا يوجد مستخدمين محظورين")
        return
    
    message = f"🚫 **قائمة المستخدمين المحظورين** ({len(banned_list)} مستخدم):\n\n"
    
    for i, banned_user in enumerate(banned_list, 1):
        banned_at = datetime.fromisoformat(banned_user['banned_at']).strftime('%Y-%m-%d %H:%M')
        message += f"{i}. **المستخدم:** {banned_user['user_id']}\n"
        message += f"   **تاريخ الحظر:** {banned_at}\n"
        message += f"   **السبب:** {banned_user['reason']}\n\n"
    
    await update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN)

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
    """Handle messages from users"""
    user = update.effective_user
    message = update.message
    
    if not user or not message:
        return
    
    # Skip messages from the admin group
    if update.effective_chat.id == ADMIN_GROUP_ID:
        return
    
    # Check if user is banned
    if is_user_banned(user.id):
        await message.reply_text("🚫 تم حظرك من استخدام البوت. تواصل مع الإدارة للمزيد من المعلومات.")
        return
    
    # Check if this is a reply to a previous admin message
    if (message.reply_to_message and 
        message.reply_to_message.from_user and 
        message.reply_to_message.from_user.is_bot):
        await handle_user_reply(update, context)
        return
    
    # Generate unique question ID
    question_id = str(uuid.uuid4())
    
    # Determine message type and content
    message_type = "نص"
    content = ""
    file_info = None
    
    if message.text:
        message_type = "نص"
        content = message.text
    elif message.photo:
        message_type = "صورة"
        content = message.caption or "صورة بدون وصف"
        file_info = message.photo[-1].file_id
    elif message.document:
        message_type = "ملف PDF" if message.document.mime_type == "application/pdf" else "ملف"
        content = message.caption or f"ملف: {message.document.file_name}"
        file_info = message.document.file_id
    elif message.voice:
        message_type = "رسالة صوتية"
        content = "رسالة صوتية"
        file_info = message.voice.file_id
    elif message.audio:
        message_type = "ملف صوتي"
        content = message.caption or "ملف صوتي"
        file_info = message.audio.file_id
    
    # Store question data
    question_data = {
        'question_id': question_id,
        'user_id': user.id,
        'username': user.username or "",
        'fullname': f"{user.first_name or ''} {user.last_name or ''}".strip(),
        'message_type': message_type,
        'content': content,
        'file_id': file_info,
        'timestamp': datetime.now().isoformat(),
        'message_id': message.message_id
    }
    
    questions_data[question_id] = question_data
    save_data(questions_data, DATA_FILE)
    
    # Track user activity
    str_user_id = str(user.id)
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
    
    # Send confirmation to user
    await message.reply_text("✅ تم استلام رسالتك")
    
    # Forward to admin group
    await forward_to_admin_group_new(context, question_data, message)
    
    # Check for milestone notifications
    total_questions = len(questions_data)
    if total_questions % 50 == 0:
        await context.bot.send_message(
            chat_id=ADMIN_GROUP_ID,
            text=f"📊 وصل عدد الأسئلة الآن إلى {total_questions}."
        )

async def forward_to_admin_group_new(context: CallbackContext, question_data: Dict, original_message):
    """Forward question to admin group"""
    user_info = f"""📩 سؤال جديد
👤 الاسم: {question_data['fullname']}
🆔 يوزر: @{question_data['username']} 
🪪 ID: {question_data['user_id']}
⏰ الوقت: {datetime.fromisoformat(question_data['timestamp']).strftime('%Y-%m-%d %H:%M')}

"""
    
    # Store original message info for replies
    replies_data[question_data['question_id']] = {
        'user_id': question_data['user_id'],
        'user_message_id': question_data['message_id'],
        'admin_message_id': None
    }
    
    try:
        if question_data['message_type'] == "نص":
            sent_message = await context.bot.send_message(
                chat_id=ADMIN_GROUP_ID,
                text=user_info + question_data['content']
            )
        elif question_data['message_type'] == "صورة":
            sent_message = await context.bot.send_photo(
                        chat_id=ADMIN_GROUP_ID,
                photo=question_data['file_id'],
                caption=user_info + question_data['content']
            )
        elif question_data['message_type'] in ["ملف PDF", "ملف"]:
            sent_message = await context.bot.send_document(
                        chat_id=ADMIN_GROUP_ID,
                document=question_data['file_id'],
                caption=user_info + question_data['content']
            )
        elif question_data['message_type'] in ["رسالة صوتية", "ملف صوتي"]:
            if question_data['message_type'] == "رسالة صوتية":
                sent_message = await context.bot.send_voice(
                        chat_id=ADMIN_GROUP_ID,
                    voice=question_data['file_id'],
                    caption=user_info
                )
            else:
                sent_message = await context.bot.send_audio(
                        chat_id=ADMIN_GROUP_ID,
                    audio=question_data['file_id'],
                    caption=user_info + question_data['content']
                )
        
        # Store admin message ID for reply tracking
        replies_data[question_data['question_id']]['admin_message_id'] = sent_message.message_id
        save_data(replies_data, REPLIES_FILE)
        
    except Exception as e:
        logger.error(f"Error forwarding to admin group: {e}")

async def handle_user_reply(update: Update, context: CallbackContext) -> None:
    """Handle user replies to admin messages"""
    if not update.message or not update.message.reply_to_message:
        return
    
    user_reply_message_id = update.message.reply_to_message.message_id
    
    # Find which admin reply this is responding to
    question_id = None
    admin_message_id = None
    
    for qid, reply_data in replies_data.items():
        if 'admin_replies' in reply_data:
            for admin_reply in reply_data['admin_replies']:
                if admin_reply.get('user_reply_message_id') == user_reply_message_id:
                    question_id = qid
                    admin_message_id = admin_reply['admin_message_id']
                    break
        if question_id:
            break
    
    if not question_id or not admin_message_id:
        return
    
    # Forward user reply to admin group as reply to admin message
    try:
        sent_to_admin = None
        if update.message.text:
            sent_to_admin = await context.bot.send_message(
                chat_id=ADMIN_GROUP_ID,
                text=f"رد من الطالب:\n{update.message.text}",
                reply_to_message_id=admin_message_id
            )
        elif update.message.photo:
            sent_to_admin = await context.bot.send_photo(
                chat_id=ADMIN_GROUP_ID,
                photo=update.message.photo[-1].file_id,
                caption=f"رد من الطالب:\n{update.message.caption or ''}",
                reply_to_message_id=admin_message_id
            )
        elif update.message.document:
            sent_to_admin = await context.bot.send_document(
                chat_id=ADMIN_GROUP_ID,
                document=update.message.document.file_id,
                caption=f"رد من الطالب:\n{update.message.caption or ''}",
                reply_to_message_id=admin_message_id
            )
        elif update.message.voice:
            sent_to_admin = await context.bot.send_voice(
                chat_id=ADMIN_GROUP_ID,
                voice=update.message.voice.file_id,
                reply_to_message_id=admin_message_id
            )
        elif update.message.audio:
            sent_to_admin = await context.bot.send_audio(
                chat_id=ADMIN_GROUP_ID,
                audio=update.message.audio.file_id,
                caption=f"رد من الطالب:\n{update.message.caption or ''}",
                reply_to_message_id=admin_message_id
            )

        # Track the admin thread message id to enable infinite back-and-forth
        if sent_to_admin:
            if 'admin_thread_message_ids' not in replies_data[question_id]:
                replies_data[question_id]['admin_thread_message_ids'] = []
            replies_data[question_id]['admin_thread_message_ids'].append(sent_to_admin.message_id)
            save_data(replies_data, REPLIES_FILE)

        # Always confirm to the user
        await update.message.reply_text("✅ تم إرسال ردك إلى الادمن.")
            
    except Exception as e:
        logger.error(f"Error forwarding user reply to admin: {e}")

async def handle_admin_reply(update: Update, context: CallbackContext) -> None:
    """Handle replies from admin group"""
    if not update.effective_chat or update.effective_chat.id != ADMIN_GROUP_ID:
        return
    
    if not update.message or not update.message.reply_to_message:
        return
    
    # Find the question this is replying to
    replied_message_id = update.message.reply_to_message.message_id
    question_id = None
    
    for qid, reply_data in replies_data.items():
        if reply_data.get('admin_message_id') == replied_message_id:
            question_id = qid
            break
        # Also allow replies to any bot-forwarded user messages in the admin thread
        admin_thread_ids = reply_data.get('admin_thread_message_ids', [])
        if admin_thread_ids and replied_message_id in admin_thread_ids:
            question_id = qid
            break
    
    if not question_id:
            return
    
    reply_data = replies_data[question_id]
    user_id = reply_data['user_id']
    user_message_id = reply_data['user_message_id']
    
    # Send reply to user
    try:
        sent_message = None
        if update.message.text:
            sent_message = await context.bot.send_message(
                chat_id=user_id,
                text=update.message.text,
                reply_to_message_id=user_message_id
            )
        elif update.message.photo:
            sent_message = await context.bot.send_photo(
                chat_id=user_id,
                photo=update.message.photo[-1].file_id,
                caption=update.message.caption,
                reply_to_message_id=user_message_id
            )
        elif update.message.document:
            sent_message = await context.bot.send_document(
                chat_id=user_id,
                document=update.message.document.file_id,
                caption=update.message.caption,
                reply_to_message_id=user_message_id
            )
        elif update.message.voice:
            sent_message = await context.bot.send_voice(
                chat_id=user_id,
                voice=update.message.voice.file_id,
                reply_to_message_id=user_message_id
            )
        elif update.message.audio:
            sent_message = await context.bot.send_audio(
                chat_id=user_id,
                audio=update.message.audio.file_id,
                caption=update.message.caption,
                reply_to_message_id=user_message_id
            )
        else:
            sent_message = None
        
        # Store admin reply message ID for user replies
        if sent_message:
            if 'admin_replies' not in replies_data[question_id]:
                replies_data[question_id]['admin_replies'] = []
            
            replies_data[question_id]['admin_replies'].append({
                'admin_message_id': update.message.message_id,
                'user_reply_message_id': sent_message.message_id
            })
            # Send one-time instruction to user on how to reply correctly
            if not replies_data[question_id].get('instruction_sent'):
                try:
                    await context.bot.send_message(
                        chat_id=user_id,
                        text=(
                            "ℹ️ للتأكد من وصول ردك للادمن بشكل صحيح:\n"
                            "• اضغط مطولاً على رسالة الادمن ثم اختر \"رد\".\n"
                            "• اكتب ردك وأرسله.\n\n"
                            "هذا يحافظ على المحادثة متصلة ولن يتم احتسابه كسؤال جديد."
                        ),
                        reply_to_message_id=sent_message.message_id
                    )
                    replies_data[question_id]['instruction_sent'] = True
                    save_data(replies_data, REPLIES_FILE)
                except Exception as e:
                    logger.warning(f"Failed to send instruction message: {e}")
            save_data(replies_data, REPLIES_FILE)
            await update.message.reply_text("✅ تم إرسال ردك إلى الطالب.")
        
    except Exception as e:
        logger.error(f"Error sending reply to user: {e}")

async def handle_broadcast_message(update: Update, context: CallbackContext) -> None:
    """Handle broadcast message from admin"""
    if not update.effective_chat or update.effective_chat.id != ADMIN_GROUP_ID:
        return
    
    if not update.effective_user or not update.message:
        return
    
    # Check if user is in broadcast mode or replying to broadcast message
    user_in_broadcast_mode = waiting_for_broadcast.get(update.effective_user.id, False)
    is_broadcast_reply = False
    
    if update.message.reply_to_message:
        reply_text = update.message.reply_to_message.text or ""
        if "وضع البث الجماعي" in reply_text or "عدد المستقبلين:" in reply_text:
            is_broadcast_reply = True
            # Set broadcast mode for this user
            waiting_for_broadcast[update.effective_user.id] = True
    
    if not user_in_broadcast_mode and not is_broadcast_reply:
            return
    
    # Clear broadcast waiting state
    waiting_for_broadcast[update.effective_user.id] = False
    
    # Get all user IDs
    user_ids = get_all_user_ids()
    
    if not user_ids:
        await update.message.reply_text("❌ لا توجد مستخدمين لإرسال الرسالة لهم")
        return
    
    # Send confirmation first
    await update.message.reply_text(f"📢 جاري إرسال الرسالة لـ {len(user_ids)} مستخدم...")
    
    successful_sends = 0
    failed_sends = 0
    
    for user_id in user_ids:
        try:
            message_sent = False
            if update.message.text:
                await context.bot.send_message(chat_id=user_id, text=update.message.text)
                message_sent = True
            elif update.message.photo:
                await context.bot.send_photo(
                    chat_id=user_id,
                    photo=update.message.photo[-1].file_id,
                    caption=update.message.caption
                )
                message_sent = True
            elif update.message.document:
                await context.bot.send_document(
                    chat_id=user_id,
                    document=update.message.document.file_id,
                    caption=update.message.caption
                )
                message_sent = True
            elif update.message.voice:
                await context.bot.send_voice(chat_id=user_id, voice=update.message.voice.file_id)
                message_sent = True
            elif update.message.audio:
                await context.bot.send_audio(
                    chat_id=user_id,
                    audio=update.message.audio.file_id,
                    caption=update.message.caption
                )
                message_sent = True
            elif update.message.video:
                await context.bot.send_video(
                    chat_id=user_id,
                    video=update.message.video.file_id,
                    caption=update.message.caption
                )
                message_sent = True
            elif update.message.sticker:
                await context.bot.send_sticker(chat_id=user_id, sticker=update.message.sticker.file_id)
                message_sent = True
            
            if message_sent:
                successful_sends += 1
                logger.info(f"Broadcast sent successfully to user {user_id}")
            
            await asyncio.sleep(0.05)  # Reduced rate limiting for faster delivery
            
        except Exception as e:
            logger.error(f"Failed to send broadcast to user {user_id}: {e}")
            failed_sends += 1
    
    await update.message.reply_text(
        f"📢 **تم إرسال الرسالة:**\n"
        f"✅ نجح: {successful_sends}\n"
        f"❌ فشل: {failed_sends}\n"
        f"📊 الإجمالي: {len(user_ids)}",
        parse_mode=ParseMode.MARKDOWN
    )

async def setup_commands(application: Application) -> None:
    """Set bot commands that will appear in the menu."""
    # Set scoped commands: private chat (users)
    user_commands = [
        BotCommand("start", "🚀 بدء استخدام البوت"),
        BotCommand("help", "❓ المساعدة")
    ]
    await application.bot.set_my_commands(user_commands, scope=BotCommandScopeAllPrivateChats())

    # Set scoped commands: admin group only
    admin_commands = [
        BotCommand("stats", "📊 الإحصائيات"),
        BotCommand("export", "📁 تصدير البيانات"),
        BotCommand("broadcast", "📢 رسالة جماعية"),
        BotCommand("ban", "🚫 حظر مستخدم"),
        BotCommand("unban", "✅ إلغاء حظر"),
        BotCommand("banned", "📋 قائمة المحظورين")
    ]
    await application.bot.set_my_commands(admin_commands, scope=BotCommandScopeChat(chat_id=ADMIN_GROUP_ID))

    # Optionally clear default/global commands so nothing leaks across scopes
    await application.bot.set_my_commands([])

    logger.info("Commands menu set successfully!")

def main():
    """Start the bot."""
    # Create the Application
    application = Application.builder().token(BOT_TOKEN).build()

    # Add command handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("stats", stats_command))
    application.add_handler(CommandHandler("export", export_command))
    application.add_handler(CommandHandler("broadcast", broadcast_command))
    application.add_handler(CommandHandler("ban", ban_command))
    application.add_handler(CommandHandler("unban", unban_command))
    application.add_handler(CommandHandler("banned", banned_list_command))
    
    # Callback query handler for inline buttons
    application.add_handler(CallbackQueryHandler(button_handler))
    
    # Admin group message handlers
    async def admin_group_handler(update: Update, context: CallbackContext):
        if update.message and update.message.reply_to_message:
            # Check if this is a reply to a broadcast initiation message
            reply_text = update.message.reply_to_message.text or ""
            if "وضع البث الجماعي" in reply_text or "عدد المستقبلين:" in reply_text:
                await handle_broadcast_message(update, context)
            else:
                await handle_admin_reply(update, context)
        else:
            await handle_broadcast_message(update, context)
    
    application.add_handler(MessageHandler(
        filters.TEXT & filters.ChatType.GROUPS,
        admin_group_handler
    ))
    
    application.add_handler(MessageHandler(
        (filters.PHOTO | filters.Document.ALL | filters.VOICE | filters.AUDIO | filters.VIDEO | filters.Sticker.ALL) & filters.ChatType.GROUPS,
        admin_group_handler
    ))
    
    # User message handlers (private chats)
    application.add_handler(MessageHandler(
        filters.TEXT & filters.ChatType.PRIVATE,
        handle_user_message
    ))
    
    application.add_handler(MessageHandler(
        (filters.PHOTO | filters.Document.ALL | filters.VOICE | filters.AUDIO | filters.VIDEO | filters.Sticker.ALL) & filters.ChatType.PRIVATE,
        handle_user_message
    ))

    # Setup bot on startup
    application.post_init = setup_commands
    
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

