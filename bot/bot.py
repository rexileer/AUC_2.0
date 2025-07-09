import asyncio
import logging
import sys
import os
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
import httpx
import json
from decimal import Decimal

from aiogram import Bot, Dispatcher, Router, F
from aiogram.types import (
    Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton,
    BotCommand, BotCommandScopeDefault, WebAppInfo
)
from aiogram.filters import Command, CommandStart, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.exceptions import TelegramAPIError
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.utils.formatting import Bold, Code, Text, as_list, as_marked_section
# from aiogram.client.default import DefaultBotProperties  # Not available in aiogram 3.1.1
from aiogram.enums import ParseMode

# Configure logging
# Create logs directory if it doesn't exist
os.makedirs('logs', exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Bot configuration
BOT_TOKEN = os.getenv('BOT_TOKEN')
BACKEND_URL = '0.0.0.0:8000'
WEBHOOK_URL = os.getenv('WEBHOOK_URL', '')
WEBHOOK_PATH = os.getenv('WEBHOOK_PATH', '/webhook')
WEBAPP_HOST = os.getenv('WEBAPP_HOST', '0.0.0.0')
WEBAPP_PORT = int(os.getenv('WEBAPP_PORT', '8080'))

if not BOT_TOKEN:
    logger.error("BOT_TOKEN environment variable is not set")
    sys.exit(1)

# States for conversations
class UserStates(StatesGroup):
    waiting_for_api_key = State()
    browsing_items = State()
    viewing_item = State()


class AuctionBot:
    def __init__(self):
        self.bot = Bot(
            token=BOT_TOKEN,
            parse_mode=ParseMode.HTML
        )
        self.dp = Dispatcher(storage=MemoryStorage())
        self.router = Router()
        self.dp.include_router(self.router)
        self.http_client = httpx.AsyncClient(timeout=30.0)

        # User sessions cache
        self.user_sessions: Dict[int, Dict[str, Any]] = {}

        # Setup handlers
        self._setup_handlers()

    def _setup_handlers(self):
        """Setup all command and message handlers"""

        # Commands
        self.router.message.register(self.cmd_start, CommandStart())
        self.router.message.register(self.cmd_help, Command('help'))
        self.router.message.register(self.cmd_input_api_key, Command('input_api_key'))
        self.router.message.register(self.cmd_balance, Command('balance'))
        self.router.message.register(self.cmd_history, Command('history'))
        self.router.message.register(self.cmd_get_items, Command('get_items'))
        self.router.message.register(self.cmd_turn_notifications, Command('turn_notifications'))
        self.router.message.register(self.cmd_my_bids, Command('my_bids'))
        self.router.message.register(self.cmd_watching, Command('watching'))
        self.router.message.register(self.cmd_profile, Command('profile'))

        # State handlers
        self.router.message.register(
            self.process_api_key,
            StateFilter(UserStates.waiting_for_api_key)
        )

        # Callback handlers
        self.router.callback_query.register(self.handle_callback)

        # Error handler
        self.dp.error.register(self.error_handler)

    async def cmd_start(self, message: Message, state: FSMContext):
        """Handle /start command"""
        user_id = message.from_user.id
        username = message.from_user.username or message.from_user.first_name

        # Register user in backend
        await self.register_bot_user(message.from_user)

        welcome_text = Text(
            "🎉 ", Bold("Welcome to Auction Platform Bot!"), "\n\n",
            "I can help you manage your auction activities:\n\n",
            "🔑 ", Code("/input_api_key"), " - Link your account\n",
            "💰 ", Code("/balance"), " - Check your balance\n",
            "📊 ", Code("/history"), " - View your auction history\n",
            "🛍️ ", Code("/get_items"), " - Browse auction items\n",
            "🔔 ", Code("/turn_notifications"), " - Manage notifications\n",
            "👤 ", Code("/profile"), " - View your profile\n",
            "❓ ", Code("/help"), " - Show this help message\n\n",
            "To get started, please link your account using ", Code("/input_api_key")
        )

        keyboard = InlineKeyboardBuilder()
        keyboard.add(InlineKeyboardButton(
            text="🔑 Link Account",
            callback_data="link_account"
        ))
        keyboard.add(InlineKeyboardButton(
            text="🌐 Open Website",
            url=f"{BACKEND_URL.replace('backend:8000', 'localhost')}"
        ))
        keyboard.adjust(1)

        await message.answer(
            welcome_text.as_html(),
            reply_markup=keyboard.as_markup()
        )

    async def cmd_help(self, message: Message):
        """Handle /help command"""
        help_text = Text(
            Bold("🤖 Auction Bot Commands"), "\n\n",
            "🔑 ", Code("/input_api_key"), " - Link your auction account\n",
            "💰 ", Code("/balance"), " - Check your current balance\n",
            "📊 ", Code("/history"), " - View bids and won auctions\n",
            "🛍️ ", Code("/get_items"), " - Browse available items\n",
            "🔔 ", Code("/turn_notifications"), " - Toggle notifications\n",
            "🎯 ", Code("/my_bids"), " - View your active bids\n",
            "👀 ", Code("/watching"), " - Items you're watching\n",
            "👤 ", Code("/profile"), " - View your profile\n",
            "❓ ", Code("/help"), " - Show this help\n\n",
            "📝 ", Bold("How to get started:"), "\n",
            "1. Get your API key from the website\n",
            "2. Use ", Code("/input_api_key"), " to link your account\n",
            "3. Start managing your auctions!\n\n",
            "🌐 Website: ", Code(BACKEND_URL.replace('backend:8000', 'localhost'))
        )

        await message.answer(help_text.as_html())

    async def cmd_input_api_key(self, message: Message, state: FSMContext):
        """Handle /input_api_key command"""
        user_id = message.from_user.id

        # Check if already linked
        if await self.is_user_linked(user_id):
            keyboard = InlineKeyboardBuilder()
            keyboard.add(InlineKeyboardButton(
                text="🔄 Re-link Account",
                callback_data="relink_account"
            ))
            keyboard.add(InlineKeyboardButton(
                text="👤 View Profile",
                callback_data="view_profile"
            ))
            keyboard.adjust(1)

            await message.answer(
                "✅ Your account is already linked!\n\n"
                "You can re-link with a new API key if needed.",
                reply_markup=keyboard.as_markup()
            )
            return

        instruction_text = Text(
            Bold("🔑 Link Your Account"), "\n\n",
            "To link your auction account:\n\n",
            "1. Go to the website: ", Code(BACKEND_URL.replace('backend:8000', 'localhost')), "\n",
            "2. Login to your account\n",
            "3. Go to Settings → API Key\n",
            "4. Copy your API key\n",
            "5. Send it to me here\n\n",
            "🔒 Your API key is secure and will be encrypted."
        )

        keyboard = InlineKeyboardBuilder()
        keyboard.add(InlineKeyboardButton(
            text="🌐 Open Website",
            url=f"{BACKEND_URL.replace('backend:8000', 'localhost')}/accounts/input_api_key/"
        ))
        keyboard.add(InlineKeyboardButton(
            text="❌ Cancel",
            callback_data="cancel"
        ))
        keyboard.adjust(1)

        await message.answer(
            instruction_text.as_html(),
            reply_markup=keyboard.as_markup()
        )

        await state.set_state(UserStates.waiting_for_api_key)

    async def process_api_key(self, message: Message, state: FSMContext):
        """Process API key input"""
        api_key = message.text.strip()
        user_id = message.from_user.id

        # Validate API key format
        if len(api_key) != 64 or not api_key.isalnum():
            await message.answer(
                "❌ Invalid API key format.\n\n"
                "API key should be 64 characters long and contain only letters and numbers."
            )
            return

        # Show loading message
        loading_msg = await message.answer("🔄 Verifying API key...")

        # Verify API key with backend
        try:
            user_data = await self.verify_api_key(api_key)
            if user_data:
                # Link Telegram account
                await self.link_telegram_account(
                    api_key,
                    user_id,
                    message.from_user.username
                )

                # Store in session
                self.user_sessions[user_id] = {
                    'api_key': api_key,
                    'user_data': user_data,
                    'linked_at': datetime.now()
                }

                success_text = Text(
                    "✅ ", Bold("Account linked successfully!"), "\n\n",
                    "👤 ", Bold("Account: "), user_data.get('username', 'Unknown'), "\n",
                    "📧 ", Bold("Email: "), user_data.get('email', 'Unknown'), "\n",
                    "💰 ", Bold("Balance: "), f"${user_data.get('balance', 0):.2f}", "\n\n",
                    "You can now use all bot features!"
                )

                keyboard = InlineKeyboardBuilder()
                keyboard.add(InlineKeyboardButton(
                    text="💰 Check Balance",
                    callback_data="check_balance"
                ))
                keyboard.add(InlineKeyboardButton(
                    text="🛍️ Browse Items",
                    callback_data="browse_items"
                ))
                keyboard.add(InlineKeyboardButton(
                    text="📊 View History",
                    callback_data="view_history"
                ))
                keyboard.adjust(2)

                await loading_msg.edit_text(
                    success_text.as_html(),
                    reply_markup=keyboard.as_markup()
                )

            else:
                await loading_msg.edit_text(
                    "❌ Invalid API key.\n\n"
                    "Please check your API key and try again."
                )
                return

        except Exception as e:
            logger.error(f"Error verifying API key: {e}")
            await loading_msg.edit_text(
                "❌ Error verifying API key.\n\n"
                "Please try again later."
            )
            return

        await state.clear()

    async def cmd_balance(self, message: Message):
        """Handle /balance command"""
        user_id = message.from_user.id

        if not await self.is_user_linked(user_id):
            await self.send_not_linked_message(message)
            return

        try:
            balance_data = await self.get_user_balance(user_id)
            if balance_data:
                balance_text = Text(
                    "💰 ", Bold("Your Balance"), "\n\n",
                    "💵 ", Bold("Available: "), f"${balance_data.get('balance', 0):.2f}", "\n",
                    "💱 ", Bold("Currency: "), balance_data.get('currency', 'USD'), "\n\n",
                    "🕐 ", Bold("Last updated: "), datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                )

                keyboard = InlineKeyboardBuilder()
                keyboard.add(InlineKeyboardButton(
                    text="🔄 Refresh",
                    callback_data="refresh_balance"
                ))
                keyboard.add(InlineKeyboardButton(
                    text="💳 Add Funds",
                    url=f"{BACKEND_URL.replace('backend:8000', 'localhost')}/accounts/balance/"
                ))
                keyboard.adjust(1)

                await message.answer(
                    balance_text.as_html(),
                    reply_markup=keyboard.as_markup()
                )
            else:
                await message.answer("❌ Could not retrieve balance information.")

        except Exception as e:
            logger.error(f"Error getting balance: {e}")
            await message.answer("❌ Error retrieving balance. Please try again.")

    async def cmd_history(self, message: Message):
        """Handle /history command"""
        user_id = message.from_user.id

        if not await self.is_user_linked(user_id):
            await self.send_not_linked_message(message)
            return

        keyboard = InlineKeyboardBuilder()
        keyboard.add(InlineKeyboardButton(
            text="🎯 My Bids",
            callback_data="history_bids"
        ))
        keyboard.add(InlineKeyboardButton(
            text="🏆 Won Auctions",
            callback_data="history_wins"
        ))
        keyboard.add(InlineKeyboardButton(
            text="📊 Statistics",
            callback_data="history_stats"
        ))
        keyboard.adjust(1)

        await message.answer(
            "📊 <b>Auction History</b>\n\n"
            "What would you like to view?",
            reply_markup=keyboard.as_markup()
        )

    async def cmd_get_items(self, message: Message):
        """Handle /get_items command"""
        user_id = message.from_user.id

        if not await self.is_user_linked(user_id):
            await self.send_not_linked_message(message)
            return

        await self.show_items_list(message, page=1)

    async def cmd_turn_notifications(self, message: Message):
        """Handle /turn_notifications command"""
        user_id = message.from_user.id

        if not await self.is_user_linked(user_id):
            await self.send_not_linked_message(message)
            return

        try:
            # Get current notification settings
            settings = await self.get_notification_settings(user_id)

            keyboard = InlineKeyboardBuilder()

            # Add toggle buttons for each notification type
            notifications = [
                ("🎯 Bid Notifications", "toggle_bid_notifications", settings.get('bid_notifications', True)),
                ("🔔 Outbid Notifications", "toggle_outbid_notifications", settings.get('outbid_notifications', True)),
                ("🏁 Auction End", "toggle_auction_end", settings.get('auction_end_notifications', True)),
                ("🏆 Win Notifications", "toggle_win_notifications", settings.get('win_notifications', True)),
                ("🆕 New Items", "toggle_new_items", settings.get('new_item_notifications', False)),
                ("💰 Price Drops", "toggle_price_drops", settings.get('price_drop_notifications', False)),
            ]

            for name, callback, enabled in notifications:
                status = "✅" if enabled else "❌"
                keyboard.add(InlineKeyboardButton(
                    text=f"{status} {name}",
                    callback_data=callback
                ))

            keyboard.adjust(1)

            settings_text = Text(
                "🔔 ", Bold("Notification Settings"), "\n\n",
                "Tap any option to toggle it on/off:\n"
            )

            await message.answer(
                settings_text.as_html(),
                reply_markup=keyboard.as_markup()
            )

        except Exception as e:
            logger.error(f"Error getting notification settings: {e}")
            await message.answer("❌ Error retrieving notification settings.")

    async def cmd_my_bids(self, message: Message):
        """Handle /my_bids command"""
        user_id = message.from_user.id

        if not await self.is_user_linked(user_id):
            await self.send_not_linked_message(message)
            return

        try:
            bids = await self.get_user_bids(user_id)
            if bids:
                await self.show_bids_list(message, bids)
            else:
                await message.answer(
                    "🎯 <b>My Bids</b>\n\n"
                    "You don't have any active bids yet.\n\n"
                    "Use /get_items to browse and bid on items!"
                )
        except Exception as e:
            logger.error(f"Error getting user bids: {e}")
            await message.answer("❌ Error retrieving your bids.")

    async def cmd_watching(self, message: Message):
        """Handle /watching command"""
        user_id = message.from_user.id

        if not await self.is_user_linked(user_id):
            await self.send_not_linked_message(message)
            return

        try:
            watching = await self.get_watching_items(user_id)
            if watching:
                await self.show_watching_list(message, watching)
            else:
                await message.answer(
                    "👀 <b>Watching List</b>\n\n"
                    "You're not watching any items yet.\n\n"
                    "Use /get_items to browse and watch items!"
                )
        except Exception as e:
            logger.error(f"Error getting watching list: {e}")
            await message.answer("❌ Error retrieving your watching list.")

    async def cmd_profile(self, message: Message):
        """Handle /profile command"""
        user_id = message.from_user.id

        if not await self.is_user_linked(user_id):
            await self.send_not_linked_message(message)
            return

        try:
            profile = await self.get_user_profile(user_id)
            if profile:
                await self.show_user_profile(message, profile)
            else:
                await message.answer("❌ Could not retrieve profile information.")
        except Exception as e:
            logger.error(f"Error getting profile: {e}")
            await message.answer("❌ Error retrieving profile.")

    async def handle_callback(self, callback: CallbackQuery, state: FSMContext):
        """Handle callback queries"""
        data = callback.data
        user_id = callback.from_user.id

        try:
            if data == "link_account":
                await callback.message.delete()
                await self.cmd_input_api_key(callback.message, state)

            elif data == "relink_account":
                await callback.message.delete()
                await self.cmd_input_api_key(callback.message, state)

            elif data == "cancel":
                await callback.message.delete()
                await state.clear()
                await callback.message.answer("❌ Operation cancelled.")

            elif data == "check_balance":
                await self.cmd_balance(callback.message)

            elif data == "browse_items":
                await self.show_items_list(callback.message, page=1)

            elif data == "view_history":
                await self.cmd_history(callback.message)

            elif data == "refresh_balance":
                await self.cmd_balance(callback.message)

            elif data.startswith("items_page_"):
                page = int(data.split("_")[-1])
                await self.show_items_list(callback.message, page=page, edit=True)

            elif data.startswith("item_"):
                item_id = data.split("_")[1]
                await self.show_item_detail(callback.message, item_id, edit=True)

            elif data.startswith("toggle_"):
                await self.toggle_notification_setting(callback, data)

            elif data.startswith("history_"):
                await self.handle_history_callback(callback, data)

            await callback.answer()

        except Exception as e:
            logger.error(f"Error handling callback {data}: {e}")
            await callback.answer("❌ Error processing request")

    async def show_items_list(self, message: Message, page: int = 1, edit: bool = False):
        """Show paginated list of auction items"""
        try:
            items = await self.get_auction_items(page=page, per_page=10)

            if not items or not items.get('items'):
                text = "🛍️ <b>Auction Items</b>\n\nNo items found."
                if edit:
                    await message.edit_text(text)
                else:
                    await message.answer(text)
                return

            text_parts = ["🛍️ <b>Auction Items</b>\n"]

            for item in items['items']:
                status_emoji = "🟢" if item.get('is_active') else "🔴"
                time_left = item.get('time_left', 'Ended')

                text_parts.append(
                    f"{status_emoji} <b>{item['title']}</b>\n"
                    f"💰 Current: ${item['current_price']:.2f}\n"
                    f"🕐 Time left: {time_left}\n"
                    f"🎯 Bids: {item.get('total_bids', 0)}\n"
                )

            text = "\n".join(text_parts)

            # Create pagination keyboard
            keyboard = InlineKeyboardBuilder()

            # Add item buttons
            for item in items['items']:
                keyboard.add(InlineKeyboardButton(
                    text=f"👀 {item['title'][:20]}...",
                    callback_data=f"item_{item['id']}"
                ))

            # Add pagination buttons
            pagination_buttons = []
            if items.get('has_previous'):
                pagination_buttons.append(InlineKeyboardButton(
                    text="⬅️ Previous",
                    callback_data=f"items_page_{page-1}"
                ))

            if items.get('has_next'):
                pagination_buttons.append(InlineKeyboardButton(
                    text="Next ➡️",
                    callback_data=f"items_page_{page+1}"
                ))

            if pagination_buttons:
                keyboard.row(*pagination_buttons)

            keyboard.adjust(1)

            if edit:
                await message.edit_text(text, reply_markup=keyboard.as_markup())
            else:
                await message.answer(text, reply_markup=keyboard.as_markup())

        except Exception as e:
            logger.error(f"Error showing items list: {e}")
            error_text = "❌ Error loading auction items."
            if edit:
                await message.edit_text(error_text)
            else:
                await message.answer(error_text)

    async def show_item_detail(self, message: Message, item_id: str, edit: bool = False):
        """Show detailed information about an auction item"""
        try:
            item = await self.get_auction_item(item_id)

            if not item:
                text = "❌ Item not found."
                if edit:
                    await message.edit_text(text)
                else:
                    await message.answer(text)
                return

            status_emoji = "🟢" if item.get('is_active') else "🔴"

            text = Text(
                f"{status_emoji} ", Bold(item['title']), "\n\n",
                "💰 ", Bold("Current Price: "), f"${item['current_price']:.2f}", "\n",
                "🎯 ", Bold("Total Bids: "), str(item.get('total_bids', 0)), "\n",
                "🕐 ", Bold("Time Left: "), item.get('time_left', 'Ended'), "\n",
                "👤 ", Bold("Seller: "), item.get('seller', 'Unknown'), "\n",
                "📝 ", Bold("Condition: "), item.get('condition', 'Unknown'), "\n\n",
                Bold("Description:"), "\n",
                item.get('description', 'No description available')[:300]
            )

            keyboard = InlineKeyboardBuilder()

            if item.get('is_active'):
                keyboard.add(InlineKeyboardButton(
                    text="🎯 Place Bid",
                    url=f"{BACKEND_URL.replace('backend:8000', 'localhost')}/auctions/{item['slug']}/"
                ))
                keyboard.add(InlineKeyboardButton(
                    text="👀 Watch Item",
                    callback_data=f"watch_{item_id}"
                ))

            keyboard.add(InlineKeyboardButton(
                text="🌐 View on Website",
                url=f"{BACKEND_URL.replace('backend:8000', 'localhost')}/auctions/{item['slug']}/"
            ))
            keyboard.add(InlineKeyboardButton(
                text="⬅️ Back to List",
                callback_data="browse_items"
            ))

            keyboard.adjust(2)

            if edit:
                await message.edit_text(text.as_html(), reply_markup=keyboard.as_markup())
            else:
                await message.answer(text.as_html(), reply_markup=keyboard.as_markup())

        except Exception as e:
            logger.error(f"Error showing item detail: {e}")
            error_text = "❌ Error loading item details."
            if edit:
                await message.edit_text(error_text)
            else:
                await message.answer(error_text)

    # Helper methods
    async def is_user_linked(self, user_id: int) -> bool:
        """Check if user has linked their account"""
        return user_id in self.user_sessions

    async def send_not_linked_message(self, message: Message):
        """Send message for users who haven't linked their account"""
        keyboard = InlineKeyboardBuilder()
        keyboard.add(InlineKeyboardButton(
            text="🔑 Link Account",
            callback_data="link_account"
        ))

        await message.answer(
            "❌ <b>Account Not Linked</b>\n\n"
            "Please link your auction account first using /input_api_key",
            reply_markup=keyboard.as_markup()
        )

    async def register_bot_user(self, user):
        """Register bot user in backend"""
        try:
            data = {
                'telegram_id': str(user.id),
                'telegram_username': user.username,
                'telegram_first_name': user.first_name,
                'telegram_last_name': user.last_name,
                'telegram_language_code': user.language_code
            }

            async with self.http_client as client:
                response = await client.post(
                    f"{BACKEND_URL}/api/bot/register/",
                    json=data
                )

                if response.status_code == 200:
                    logger.info(f"Bot user registered: {user.id}")
                    return response.json()
                else:
                    logger.error(f"Failed to register bot user: {response.status_code}")

        except Exception as e:
            logger.error(f"Error registering bot user: {e}")

        return None

    async def verify_api_key(self, api_key: str) -> Optional[Dict]:
        """Verify API key with backend"""
        try:
            async with self.http_client as client:
                response = await client.post(
                    f"{BACKEND_URL}/api/accounts/verify-api-key/",
                    json={'api_key': api_key}
                )

                if response.status_code == 200:
                    return response.json()

        except Exception as e:
            logger.error(f"Error verifying API key: {e}")

        return None

    async def link_telegram_account(self, api_key: str, telegram_user_id: int, telegram_username: str = None):
        """Link Telegram account to user"""
        try:
            data = {
                'api_key': api_key,
                'telegram_user_id': str(telegram_user_id),
                'telegram_username': telegram_username
            }

            async with self.http_client as client:
                response = await client.post(
                    f"{BACKEND_URL}/api/accounts/link-telegram/",
                    json=data
                )

                return response.status_code == 200

        except Exception as e:
            logger.error(f"Error linking Telegram account: {e}")

        return False

    async def get_user_balance(self, user_id: int) -> Optional[Dict]:
        """Get user balance from backend"""
        try:
            session = self.user_sessions.get(user_id)
            if not session:
                return None

            headers = {'Authorization': f'Bearer {session["api_key"]}'}

            async with self.http_client as client:
                response = await client.get(
                    f"{BACKEND_URL}/api/accounts/balance/",
                    headers=headers
                )

                if response.status_code == 200:
                    return response.json()

        except Exception as e:
            logger.error(f"Error getting user balance: {e}")

        return None

    async def get_auction_items(self, page: int = 1, per_page: int = 10) -> Optional[Dict]:
        """Get auction items from backend"""
        try:
            params = {
                'page': page,
                'per_page': per_page,
                'status': 'active'
            }

            async with self.http_client as client:
                response = await client.get(
                    f"{BACKEND_URL}/api/auctions/items/",
                    params=params
                )

                if response.status_code == 200:
                    return response.json()

        except Exception as e:
            logger.error(f"Error getting auction items: {e}")

        return None

    async def get_auction_item(self, item_id: str) -> Optional[Dict]:
        """Get specific auction item"""
        try:
            async with self.http_client as client:
                response = await client.get(
                    f"{BACKEND_URL}/api/auctions/items/{item_id}/"
                )

                if response.status_code == 200:
                    return response.json()

        except Exception as e:
            logger.error(f"Error getting auction item: {e}")

        return None

    async def get_user_bids(self, user_id: int) -> Optional[List[Dict]]:
        """Get user's active bids"""
        try:
            session = self.user_sessions.get(user_id)
            if not session:
                return None

            headers = {'Authorization': f'Bearer {session["api_key"]}'}

            async with self.http_client as client:
                response = await client.get(
                    f"{BACKEND_URL}/api/auctions/my-bids/",
                    headers=headers
                )

                if response.status_code == 200:
                    return response.json().get('bids', [])

        except Exception as e:
            logger.error(f"Error getting user bids: {e}")

        return None

    async def get_watching_items(self, user_id: int) -> Optional[List[Dict]]:
        """Get items user is watching"""
        try:
            session = self.user_sessions.get(user_id)
            if not session:
                return None

            headers = {'Authorization': f'Bearer {session["api_key"]}'}

            async with self.http_client as client:
                response = await client.get(
                    f"{BACKEND_URL}/api/auctions/watching/",
                    headers=headers
                )

                if response.status_code == 200:
                    return response.json().get('items', [])

        except Exception as e:
            logger.error(f"Error getting watching items: {e}")

        return None

    async def get_user_profile(self, user_id: int) -> Optional[Dict]:
        """Get user profile"""
        try:
            session = self.user_sessions.get(user_id)
            if not session:
                return None

            headers = {'Authorization': f'Bearer {session["api_key"]}'}

            async with self.http_client as client:
                response = await client.get(
                    f"{BACKEND_URL}/api/accounts/profile/",
                    headers=headers
                )

                if response.status_code == 200:
                    return response.json()

        except Exception as e:
            logger.error(f"Error getting user profile: {e}")

        return None

    async def get_notification_settings(self, user_id: int) -> Dict:
        """Get user notification settings"""
        try:
            session = self.user_sessions.get(user_id)
            if not session:
                return {}

            headers = {'Authorization': f'Bearer {session["api_key"]}'}

            async with self.http_client as client:
                response = await client.get(
                    f"{BACKEND_URL}/api/bot/notification-settings/",
                    headers=headers
                )

                if response.status_code == 200:
                    return response.json()

        except Exception as e:
            logger.error(f"Error getting notification settings: {e}")

        return {}

    async def toggle_notification_setting(self, callback: CallbackQuery, setting_type: str):
        """Toggle notification setting"""
        user_id = callback.from_user.id

        try:
            session = self.user_sessions.get(user_id)
            if not session:
                await callback.answer("❌ Account not linked")
                return

            headers = {'Authorization': f'Bearer {session["api_key"]}'}
            setting_key = setting_type.replace('toggle_', '').replace('_', '-')

            async with self.http_client as client:
                response = await client.post(
                    f"{BACKEND_URL}/api/bot/toggle-notification/",
                    headers=headers,
                    json={'setting': setting_key}
                )

                if response.status_code == 200:
                    result = response.json()
                    status = "enabled" if result.get('enabled') else "disabled"
                    await callback.answer(f"✅ Notification {status}")

                    # Refresh the settings display
                    await self.cmd_turn_notifications(callback.message)
                else:
                    await callback.answer("❌ Error updating setting")

        except Exception as e:
            logger.error(f"Error toggling notification: {e}")
            await callback.answer("❌ Error updating setting")

    async def handle_history_callback(self, callback: CallbackQuery, data: str):
        """Handle history-related callbacks"""
        user_id = callback.from_user.id

        try:
            if data == "history_bids":
                bids = await self.get_user_bids(user_id)
                if bids:
                    await self.show_bids_list(callback.message, bids, edit=True)
                else:
                    await callback.message.edit_text(
                        "🎯 <b>My Bids</b>\n\n"
                        "You don't have any active bids."
                    )

            elif data == "history_wins":
                wins = await self.get_user_wins(user_id)
                if wins:
                    await self.show_wins_list(callback.message, wins, edit=True)
                else:
                    await callback.message.edit_text(
                        "🏆 <b>Won Auctions</b>\n\n"
                        "You haven't won any auctions yet."
                    )

            elif data == "history_stats":
                stats = await self.get_user_statistics(user_id)
                if stats:
                    await self.show_user_statistics(callback.message, stats, edit=True)
                else:
                    await callback.message.edit_text(
                        "📊 <b>Statistics</b>\n\n"
                        "Could not load statistics."
                    )

        except Exception as e:
            logger.error(f"Error handling history callback: {e}")
            await callback.answer("❌ Error loading data")

    async def show_bids_list(self, message: Message, bids: List[Dict], edit: bool = False):
        """Show list of user's bids"""
        if not bids:
            text = "🎯 <b>My Bids</b>\n\nNo active bids found."
            if edit:
                await message.edit_text(text)
            else:
                await message.answer(text)
            return

        text_parts = ["🎯 <b>My Active Bids</b>\n"]

        for bid in bids[:10]:  # Show max 10 bids
            status_emoji = {
                'active': '🟢',
                'outbid': '🔴',
                'winning': '🏆'
            }.get(bid.get('status'), '⚪')

            text_parts.append(
                f"{status_emoji} <b>{bid['item_title']}</b>\n"
                f"💰 My bid: ${bid['amount']:.2f}\n"
                f"🏷️ Current: ${bid['current_price']:.2f}\n"
                f"🕐 Time left: {bid.get('time_left', 'Ended')}\n"
            )

        text = "\n".join(text_parts)

        keyboard = InlineKeyboardBuilder()
        keyboard.add(InlineKeyboardButton(
            text="🔄 Refresh",
            callback_data="history_bids"
        ))
        keyboard.add(InlineKeyboardButton(
            text="🛍️ Browse Items",
            callback_data="browse_items"
        ))
        keyboard.adjust(1)

        if edit:
            await message.edit_text(text, reply_markup=keyboard.as_markup())
        else:
            await message.answer(text, reply_markup=keyboard.as_markup())

    async def show_watching_list(self, message: Message, items: List[Dict], edit: bool = False):
        """Show list of items user is watching"""
        if not items:
            text = "👀 <b>Watching List</b>\n\nNo items being watched."
            if edit:
                await message.edit_text(text)
            else:
                await message.answer(text)
            return

        text_parts = ["👀 <b>Items I'm Watching</b>\n"]

        for item in items[:10]:  # Show max 10 items
            status_emoji = "🟢" if item.get('is_active') else "🔴"

            text_parts.append(
                f"{status_emoji} <b>{item['title']}</b>\n"
                f"💰 Current: ${item['current_price']:.2f}\n"
                f"🎯 Bids: {item.get('total_bids', 0)}\n"
                f"🕐 Time left: {item.get('time_left', 'Ended')}\n"
            )

        text = "\n".join(text_parts)

        keyboard = InlineKeyboardBuilder()
        keyboard.add(InlineKeyboardButton(
            text="🔄 Refresh",
            callback_data="cmd_watching"
        ))
        keyboard.add(InlineKeyboardButton(
            text="🛍️ Browse Items",
            callback_data="browse_items"
        ))
        keyboard.adjust(1)

        if edit:
            await message.edit_text(text, reply_markup=keyboard.as_markup())
        else:
            await message.answer(text, reply_markup=keyboard.as_markup())

    async def show_user_profile(self, message: Message, profile: Dict, edit: bool = False):
        """Show user profile information"""
        user_data = profile.get('user', {})
        profile_data = profile.get('profile', {})

        text = Text(
            "👤 ", Bold("Your Profile"), "\n\n",
            "📧 ", Bold("Email: "), user_data.get('email', 'N/A'), "\n",
            "🏷️ ", Bold("Username: "), user_data.get('username', 'N/A'), "\n",
            "💰 ", Bold("Balance: "), f"${user_data.get('balance', 0):.2f}", "\n",
            "⭐ ", Bold("Rating: "), f"{user_data.get('rating', 0):.1f}/5.0", "\n",
            "✅ ", Bold("Verified: "), "Yes" if user_data.get('is_verified') else "No", "\n\n",
            Bold("📊 Statistics:"), "\n",
            "🎯 ", Bold("Total Bids: "), str(profile_data.get('total_bids', 0)), "\n",
            "🏆 ", Bold("Won Auctions: "), str(profile_data.get('total_wins', 0)), "\n",
            "💸 ", Bold("Total Spent: "), f"${profile_data.get('total_spent', 0):.2f}", "\n",
            "📈 ", Bold("Win Rate: "), f"{profile_data.get('win_rate', 0):.1f}%"
        )

        keyboard = InlineKeyboardBuilder()
        keyboard.add(InlineKeyboardButton(
            text="⚙️ Settings",
            url=f"{BACKEND_URL.replace('backend:8000', 'localhost')}/accounts/settings/"
        ))
        keyboard.add(InlineKeyboardButton(
            text="🔄 Refresh",
            callback_data="view_profile"
        ))
        keyboard.adjust(1)

        if edit:
            await message.edit_text(text.as_html(), reply_markup=keyboard.as_markup())
        else:
            await message.answer(text.as_html(), reply_markup=keyboard.as_markup())

    async def get_user_wins(self, user_id: int) -> Optional[List[Dict]]:
        """Get user's won auctions"""
        try:
            session = self.user_sessions.get(user_id)
            if not session:
                return None

            headers = {'Authorization': f'Bearer {session["api_key"]}'}

            async with self.http_client as client:
                response = await client.get(
                    f"{BACKEND_URL}/api/auctions/my-wins/",
                    headers=headers
                )

                if response.status_code == 200:
                    return response.json().get('items', [])

        except Exception as e:
            logger.error(f"Error getting user wins: {e}")

        return None

    async def get_user_statistics(self, user_id: int) -> Optional[Dict]:
        """Get user statistics"""
        try:
            session = self.user_sessions.get(user_id)
            if not session:
                return None

            headers = {'Authorization': f'Bearer {session["api_key"]}'}

            async with self.http_client as client:
                response = await client.get(
                    f"{BACKEND_URL}/api/accounts/statistics/",
                    headers=headers
                )

                if response.status_code == 200:
                    return response.json()

        except Exception as e:
            logger.error(f"Error getting user statistics: {e}")

        return None

    async def show_wins_list(self, message: Message, wins: List[Dict], edit: bool = False):
        """Show list of user's won auctions"""
        if not wins:
            text = "🏆 <b>Won Auctions</b>\n\nNo won auctions found."
            if edit:
                await message.edit_text(text)
            else:
                await message.answer(text)
            return

        text_parts = ["🏆 <b>My Won Auctions</b>\n"]

        for item in wins[:10]:  # Show max 10 wins
            text_parts.append(
                f"🏆 <b>{item['title']}</b>\n"
                f"💰 Won for: ${item['winning_price']:.2f}\n"
                f"📅 Won on: {item.get('end_date', 'N/A')}\n"
                f"📋 Status: {item.get('status', 'N/A')}\n"
            )

        text = "\n".join(text_parts)

        keyboard = InlineKeyboardBuilder()
        keyboard.add(InlineKeyboardButton(
            text="🔄 Refresh",
            callback_data="history_wins"
        ))
        keyboard.adjust(1)

        if edit:
            await message.edit_text(text, reply_markup=keyboard.as_markup())
        else:
            await message.answer(text, reply_markup=keyboard.as_markup())

    async def show_user_statistics(self, message: Message, stats: Dict, edit: bool = False):
        """Show user statistics"""
        user_info = stats.get('user_info', {})
        bidding = stats.get('bidding', {})
        selling = stats.get('selling', {})

        text = Text(
            "📊 ", Bold("Your Statistics"), "\n\n",
            Bold("👤 Account Info:"), "\n",
            "📧 ", user_info.get('username', 'N/A'), "\n",
            "💰 Balance: $", str(user_info.get('balance', 0)), "\n",
            "⭐ Rating: ", f"{user_info.get('rating', 0):.1f}/5.0", "\n\n",
            Bold("🎯 Bidding Activity:"), "\n",
            "📝 Total Bids: ", str(bidding.get('total_bids', 0)), "\n",
            "🔥 Active Bids: ", str(bidding.get('active_bids', 0)), "\n",
            "🏆 Won Auctions: ", str(bidding.get('won_auctions', 0)), "\n",
            "💸 Total Spent: $", str(bidding.get('total_spent', 0)), "\n\n",
            Bold("🛒 Selling Activity:"), "\n",
            "📦 Items Listed: ", str(selling.get('items_listed', 0)), "\n",
            "✅ Items Sold: ", str(selling.get('items_sold', 0)), "\n",
            "💰 Total Earned: $", str(selling.get('total_earned', 0))
        )

        keyboard = InlineKeyboardBuilder()
        keyboard.add(InlineKeyboardButton(
            text="🔄 Refresh",
            callback_data="history_stats"
        ))
        keyboard.add(InlineKeyboardButton(
            text="📊 View on Website",
            url=f"{BACKEND_URL.replace('backend:8000', 'localhost')}/accounts/dashboard/"
        ))
        keyboard.adjust(1)

        if edit:
            await message.edit_text(text.as_html(), reply_markup=keyboard.as_markup())
        else:
            await message.answer(text.as_html(), reply_markup=keyboard.as_markup())

    async def error_handler(self, event, exception):
        """Global error handler"""
        logger.error(f"Bot error: {exception}", exc_info=True)

        if hasattr(event, 'message') and event.message:
            try:
                await event.message.answer(
                    "❌ An error occurred. Please try again later."
                )
            except Exception:
                pass

    async def setup_bot_commands(self):
        """Setup bot commands for Telegram UI"""
        commands = [
            BotCommand(command="start", description="🎉 Start the bot"),
            BotCommand(command="help", description="❓ Show help message"),
            BotCommand(command="input_api_key", description="🔑 Link your account"),
            BotCommand(command="balance", description="💰 Check your balance"),
            BotCommand(command="history", description="📊 View auction history"),
            BotCommand(command="get_items", description="🛍️ Browse auction items"),
            BotCommand(command="turn_notifications", description="🔔 Manage notifications"),
            BotCommand(command="my_bids", description="🎯 View your bids"),
            BotCommand(command="watching", description="👀 Items you're watching"),
            BotCommand(command="profile", description="👤 View your profile"),
        ]

        await self.bot.set_my_commands(commands, BotCommandScopeDefault())
        logger.info("Bot commands set successfully")

    async def start_polling(self):
        """Start bot with polling"""
        try:
            await self.setup_bot_commands()
            logger.info("Starting bot with polling...")

            await self.dp.start_polling(
                self.bot,
                allowed_updates=["message", "callback_query"]
            )
        except Exception as e:
            logger.error(f"Error in polling: {e}")
        finally:
            await self.bot.session.close()
            await self.http_client.aclose()

    async def cleanup(self):
        """Cleanup resources"""
        await self.bot.session.close()
        await self.http_client.aclose()


async def main():
    """Main function to run the bot"""
    logger.info("Initializing Auction Bot...")

    bot = AuctionBot()

    try:
        await bot.start_polling()
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Bot error: {e}")
    finally:
        await bot.cleanup()
        logger.info("Bot cleanup completed")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot terminated by user")
    except Exception as e:
        logger.error(f"Failed to start bot: {e}")
        sys.exit(1)
