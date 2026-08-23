"""
TikTok Video Downloader Telegram Bot (MTProto / Pyrogram Edition)
Downloads TikTok videos in HD quality without watermarks and uploads up to 2 GB.
"""

import os
import asyncio
import logging
import tempfile
import gc
import re
import time
from typing import Optional, Dict
from datetime import datetime
import validators
from dotenv import load_dotenv

from pyrogram import Client, filters
from pyrogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)
from pyrogram.enums import ChatAction, ParseMode
from pyrogram.errors import RPCError, FloodWait

from tiktok_downloader import download_tiktok_video

# Load environment variables
load_dotenv()

# Global variable for web server integration
bot_instance = None

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO if not os.getenv('DEBUG') else logging.DEBUG
)
logger = logging.getLogger(__name__)


class TikTokBot:
    """
    TikTok Video Downloader Telegram Bot using MTProto (Pyrogram/Pyrofork).
    Supports video uploads up to 2 GB.
    """

    def __init__(self):
        self.token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.api_id = os.getenv('TELEGRAM_API_ID')
        self.api_hash = os.getenv('TELEGRAM_API_HASH')
        self.admin_chat_id = os.getenv('ADMIN_CHAT_ID')
        self.max_file_size = 2000 * 1024 * 1024  # 2 GB MTProto upload limit

        if not self.token:
            raise ValueError("TELEGRAM_BOT_TOKEN is required in environment variables")

        if not self.api_id or not self.api_hash:
            raise ValueError(
                "TELEGRAM_API_ID and TELEGRAM_API_HASH are required for MTProto (up to 2GB upload).\n"
                "Get them from https://my.telegram.org and add them to your .env file."
            )

        try:
            self.api_id = int(self.api_id)
        except ValueError:
            raise ValueError("TELEGRAM_API_ID must be a valid integer")

        # Initialize Pyrogram client with in-memory session to prevent disk lock issues
        self.app = Client(
            name="tiktok_downloader_bot",
            api_id=self.api_id,
            api_hash=self.api_hash,
            bot_token=self.token,
            in_memory=True
        )

        # Statistics
        self.stats = {
            'total_downloads': 0,
            'successful_downloads': 0,
            'failed_downloads': 0,
            'start_time': datetime.now()
        }

        # User quality preferences (user_id: quality) -> 'hd' (default) or 'standard'
        self.user_quality_preferences: Dict[int, str] = {}

        # Register Pyrogram handlers
        self._register_handlers()

    def _register_handlers(self):
        """Register command, message, and callback handlers."""

        @self.app.on_message(filters.command("start") & filters.private)
        async def _start(client: Client, message: Message):
            await self.start_command(client, message)

        @self.app.on_message(filters.command("help") & filters.private)
        async def _help(client: Client, message: Message):
            await self.help_command(client, message)

        @self.app.on_message(filters.command("stats") & filters.private)
        async def _stats(client: Client, message: Message):
            await self.stats_command(client, message)

        @self.app.on_message(filters.command("quality") & filters.private)
        async def _quality(client: Client, message: Message):
            await self.quality_command(client, message)

        @self.app.on_callback_query()
        async def _callback(client: Client, callback_query: CallbackQuery):
            await self.handle_callback_query(client, callback_query)

        # Handle TikTok URLs
        @self.app.on_message(
            filters.text & filters.private & ~filters.command(
                ["start", "help", "stats", "quality"]
            )
        )
        async def _messages(client: Client, message: Message):
            if self.extract_tiktok_url(message.text or ""):
                await self.handle_tiktok_url(client, message)
            else:
                await self.handle_other_messages(client, message)

    async def start_command(self, client: Client, message: Message) -> None:
        """Handle /start command"""
        user = message.from_user
        first_name = user.first_name if user else "there"

        welcome_message = (
            f"🎬 **TikTok HD Downloader Bot**\n\n"
            f"👋 Hello {first_name}! I can help you download TikTok videos in HD quality without watermarks.\n\n"
            f"**How to use:**\n"
            f"1️⃣ Send me any TikTok video link\n"
            f"2️⃣ Wait while I process it\n"
            f"3️⃣ Get your HD video without watermark! (Supports up to **2 GB**)\n\n"
            f"**Supported formats:**\n"
            f"• tiktok.com/@user/video/123456\n"
            f"• vm.tiktok.com/ABC123\n"
            f"• vt.tiktok.com/ABC123\n"
            f"• tiktok.com/t/ABC123\n\n"
            f"**Features:**\n"
            f"✅ Ultra HD Quality (1080p/4K)\n"
            f"✅ No watermarks\n"
            f"✅ Up to 2 GB file size support (MTProto native)\n"
            f"✅ Fast processing & Live progress\n"
            f"✅ Original audio quality\n\n"
            f"**Commands:**\n"
            f"/start - Show this message\n"
            f"/help - Get help and examples\n"
            f"/stats - View bot statistics\n"
            f"/quality - Choose default quality preference\n\n"
            f"Ready to download? Just send me a TikTok link! 🚀"
        )

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("📱 How to get TikTok link", callback_data="help_link")],
            [InlineKeyboardButton("⚙️ Quality Settings", callback_data="quality_settings")],
            [InlineKeyboardButton("📊 Bot Stats", callback_data="show_stats")]
        ])

        await message.reply_text(
            text=welcome_message,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=keyboard
        )

        if user:
            logger.info(f"User started bot: {user.id} - {user.username or user.first_name}")

    async def help_command(self, client: Client, message: Message) -> None:
        """Handle /help command"""
        help_message = (
            "📚 **Help & Instructions**\n\n"
            "**Step-by-step guide:**\n"
            "1. Open TikTok app on your phone\n"
            "2. Find the video you want to download\n"
            "3. Tap the \"Share\" button (arrow icon)\n"
            "4. Select \"Copy Link\"\n"
            "5. Come back to this bot and paste the link\n"
            "6. Wait for the magic! ✨\n\n"
            "**Supported URL formats:**\n"
            "• `https://www.tiktok.com/@username/video/1234567890`\n"
            "• `https://vm.tiktok.com/ABC123DEF/`\n"
            "• `https://vt.tiktok.com/ABC123/`\n"
            "• `https://tiktok.com/t/ABC123/`\n\n"
            "**Quality Options:**\n"
            "🔥 **Auto HD** - Highest available quality (up to 2GB)\n"
            "📺 **Standard** - Good quality, smaller file size\n\n"
            "**Troubleshooting:**\n"
            "❌ **\"Invalid URL\"** - Check your link format\n"
            "❌ **\"Video not found\"** - Video might be deleted/private\n"
            "❌ **\"Download failed\"** - Try again or check if video exists"
        )

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Back to Main", callback_data="back_main")]
        ])

        await message.reply_text(
            text=help_message,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=keyboard
        )

    async def stats_command(self, client: Client, message: Message) -> None:
        """Handle /stats command"""
        uptime = datetime.now() - self.stats['start_time']
        total = self.stats['total_downloads']
        successful = self.stats['successful_downloads']
        failed = self.stats['failed_downloads']
        success_rate = (successful / max(total, 1)) * 100

        stats_message = (
            f"📊 **Bot Statistics**\n\n"
            f"**Downloads:**\n"
            f"✅ Successful: {successful}\n"
            f"❌ Failed: {failed}\n"
            f"📈 Total: {total}\n\n"
            f"**Success Rate:** {success_rate:.1f}%\n"
            f"**Uptime:** {str(uptime).split('.')[0]}\n\n"
            f"**Bot Info:**\n"
            f"🤖 Engine: MTProto (Pyrogram) - 2GB Limit\n"
            f"🚀 Status: 🟢 Online\n"
            f"⚡ Speed: HD downloads in seconds"
        )

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔄 Refresh", callback_data="show_stats")]
        ])

        await message.reply_text(
            text=stats_message,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=keyboard
        )

    async def quality_command(self, client: Client, message: Message) -> None:
        """Handle /quality command"""
        user_id = message.from_user.id if message.from_user else 0
        current_quality = self.user_quality_preferences.get(user_id, 'hd')

        hd_marker = " ✅" if current_quality == 'hd' else ""
        std_marker = " ✅" if current_quality == 'standard' else ""
        current_text = "Auto HD ✅" if current_quality == 'hd' else "Standard ✅"

        quality_message = (
            f"⚙️ **Quality Settings**\n\n"
            f"**Available Options:**\n"
            f"🔥 **Auto HD** - Best quality available{hd_marker}\n"
            f"📺 **Standard** - Good quality, faster download{std_marker}\n\n"
            f"**Current Setting:** {current_text}\n\n"
            f"Choose your preferred quality setting below:"
        )

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔥 Auto HD", callback_data="quality_hd")],
            [InlineKeyboardButton("📺 Standard", callback_data="quality_standard")],
            [InlineKeyboardButton("🔙 Back to Main Menu", callback_data="back_main")]
        ])

        await message.reply_text(
            text=quality_message,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=keyboard
        )

    async def handle_callback_query(self, client: Client, query: CallbackQuery) -> None:
        """Handle inline keyboard callbacks"""
        try:
            await query.answer()
        except Exception as e:
            logger.warning(f"Failed to answer callback query: {e}")

        user_id = query.from_user.id if query.from_user else 0

        if query.data == "help_link":
            help_message = (
                "📱 **How to get TikTok video link:**\n\n"
                "1. Open TikTok app\n"
                "2. Find the video you want\n"
                "3. Tap the **Share** button (➡️)\n"
                "4. Select **Copy Link**\n"
                "5. Come back here and paste it!\n\n"
                "**Alternative method:**\n"
                "1. Tap and hold on the video\n"
                "2. Select \"Copy Link\" from menu\n"
                "3. Paste here!\n\n"
                "That's it! 🎉"
            )
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Back", callback_data="back_main")]
            ])
            await query.edit_message_text(
                text=help_message,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=keyboard
            )

        elif query.data == "quality_settings":
            current_quality = self.user_quality_preferences.get(user_id, 'hd')
            hd_marker = " ✅" if current_quality == 'hd' else ""
            std_marker = " ✅" if current_quality == 'standard' else ""
            current_text = "Auto HD ✅" if current_quality == 'hd' else "Standard ✅"

            quality_message = (
                f"⚙️ **Quality Settings**\n\n"
                f"**Available Options:**\n"
                f"🔥 **Auto HD** - Best quality available{hd_marker}\n"
                f"📺 **Standard** - Good quality, faster download{std_marker}\n\n"
                f"**Current Setting:** {current_text}\n\n"
                f"Choose your preferred quality setting below:"
            )
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("🔥 Auto HD", callback_data="quality_hd")],
                [InlineKeyboardButton("📺 Standard", callback_data="quality_standard")],
                [InlineKeyboardButton("🔙 Back to Main Menu", callback_data="back_main")]
            ])
            await query.edit_message_text(
                text=quality_message,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=keyboard
            )

        elif query.data == "quality_hd":
            self.user_quality_preferences[user_id] = 'hd'
            try:
                await query.answer("✅ Auto HD quality selected!")
            except Exception:
                pass

            quality_message = (
                "⚙️ **Quality Settings**\n\n"
                "**Available Options:**\n"
                "🔥 **Auto HD** - Best quality available ✅\n"
                "📺 **Standard** - Good quality, faster download\n\n"
                "**Current Setting:** Auto HD ✅\n\n"
                "Your videos will now be downloaded in the highest quality available (up to 2GB)."
            )
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("🔥 Auto HD", callback_data="quality_hd")],
                [InlineKeyboardButton("📺 Standard", callback_data="quality_standard")],
                [InlineKeyboardButton("🔙 Back to Main Menu", callback_data="back_main")]
            ])
            await query.edit_message_text(
                text=quality_message,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=keyboard
            )

        elif query.data == "quality_standard":
            self.user_quality_preferences[user_id] = 'standard'
            try:
                await query.answer("✅ Standard quality selected!")
            except Exception:
                pass

            quality_message = (
                "⚙️ **Quality Settings**\n\n"
                "**Available Options:**\n"
                "🔥 **Auto HD** - Best quality available\n"
                "📺 **Standard** - Good quality, faster download ✅\n\n"
                "**Current Setting:** Standard ✅\n\n"
                "Your videos will now be downloaded in standard quality for faster delivery."
            )
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("🔥 Auto HD", callback_data="quality_hd")],
                [InlineKeyboardButton("📺 Standard", callback_data="quality_standard")],
                [InlineKeyboardButton("🔙 Back to Main Menu", callback_data="back_main")]
            ])
            await query.edit_message_text(
                text=quality_message,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=keyboard
            )

        elif query.data == "show_stats":
            uptime = datetime.now() - self.stats['start_time']
            total = self.stats['total_downloads']
            successful = self.stats['successful_downloads']
            failed = self.stats['failed_downloads']
            success_rate = (successful / max(total, 1)) * 100

            stats_message = (
                f"📊 **Bot Statistics**\n\n"
                f"**Downloads:**\n"
                f"✅ Successful: {successful}\n"
                f"❌ Failed: {failed}\n"
                f"📈 Total: {total}\n\n"
                f"**Success Rate:** {success_rate:.1f}%\n"
                f"**Uptime:** {str(uptime).split('.')[0]}\n\n"
                f"**Status:** 🟢 Online (MTProto 2GB Active)"
            )
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄 Refresh", callback_data="show_stats")],
                [InlineKeyboardButton("🔙 Back", callback_data="back_main")]
            ])
            await query.edit_message_text(
                text=stats_message,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=keyboard
            )

        elif query.data == "back_main":
            user = query.from_user
            first_name = user.first_name if user else "there"
            welcome_message = (
                f"🎬 **TikTok HD Downloader Bot**\n\n"
                f"👋 Hello {first_name}! I can help you download TikTok videos in HD quality without watermarks.\n\n"
                f"**How to use:**\n"
                f"1️⃣ Send me any TikTok video link\n"
                f"2️⃣ Wait while I process it\n"
                f"3️⃣ Get your HD video without watermark! (Up to **2 GB**)\n\n"
                f"Ready to download? Just send me a TikTok link! 🚀"
            )
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("📱 How to get TikTok link", callback_data="help_link")],
                [InlineKeyboardButton("⚙️ Quality Settings", callback_data="quality_settings")],
                [InlineKeyboardButton("📊 Bot Stats", callback_data="show_stats")]
            ])
            await query.edit_message_text(
                text=welcome_message,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=keyboard
            )

    async def handle_tiktok_url(self, client: Client, message: Message) -> None:
        """Handle incoming TikTok URL messages and upload video up to 2GB"""
        user = message.from_user
        user_id = user.id if user else 0
        text = (message.text or "").strip()

        tiktok_url = self.extract_tiktok_url(text)
        if not tiktok_url:
            await message.reply_text(
                "❌ **Invalid TikTok URL**\n\n"
                "Please send a valid TikTok link. Need help? Use /help to see examples.",
                parse_mode=ParseMode.MARKDOWN
            )
            return

        processing_message = await message.reply_text(
            "🔄 **Processing your request...**\n\n"
            "⏳ Fetching video information...",
            parse_mode=ParseMode.MARKDOWN
        )

        temp_file_path = None
        try:
            await client.send_chat_action(chat_id=message.chat.id, action=ChatAction.TYPING)
            self.stats['total_downloads'] += 1
            logger.info(f"Processing TikTok URL: {tiktok_url} for user {user_id}")

            user_quality = self.user_quality_preferences.get(user_id, 'hd')
            quality_text = "HD" if user_quality == 'hd' else "Standard"

            await processing_message.edit_text(
                f"🔄 **Processing your request...**\n\n"
                f"📥 Downloading {quality_text} video...",
                parse_mode=ParseMode.MARKDOWN
            )

            result = await download_tiktok_video(tiktok_url, quality=user_quality)

            if not result.get('success'):
                error_message = result.get('error', 'Unknown error occurred')
                await processing_message.edit_text(
                    f"❌ **Download Failed**\n\n"
                    f"Error: {error_message}\n\n"
                    f"Please try again or check if the video is available.",
                    parse_mode=ParseMode.MARKDOWN
                )
                self.stats['failed_downloads'] += 1
                logger.error(f"Download failed for {tiktok_url}: {error_message}")
                return

            file_size = result.get('file_size', 0)
            video_data = result.get('video_data')

            # Check if file size exceeds MTProto 2GB limit
            if file_size > self.max_file_size:
                video_url = result.get('video_url')
                await processing_message.edit_text(
                    f"📥 **Download Link Ready**\n\n"
                    f"📊 Video size: **{file_size / (1024*1024):.1f}MB**\n"
                    f"⚠️ File exceeds Telegram's 2GB maximum limit\n\n"
                    f"**Download directly:**\n"
                    f"🔗 [Click here to download]({video_url})\n\n"
                    f"🎯 **Or try Standard Quality** for a smaller file.",
                    parse_mode=ParseMode.MARKDOWN,
                    disable_web_page_preview=False
                )
                self.stats['successful_downloads'] += 1
                return

            if not video_data:
                await processing_message.edit_text(
                    "❌ **Download Failed**\n\n"
                    "Could not retrieve video data. Please try again.",
                    parse_mode=ParseMode.MARKDOWN
                )
                self.stats['failed_downloads'] += 1
                return

            file_size = len(video_data)

            # Write to disk to allow Pyrogram streaming upload without holding all RAM
            with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as temp_file:
                temp_file.write(video_data)
                temp_file_path = temp_file.name

            # Immediately free RAM memory
            del video_data
            gc.collect()
            logger.info(f"Saved {file_size / (1024*1024):.1f}MB to {temp_file_path} and freed RAM")

            await processing_message.edit_text(
                f"🔄 **Processing your request...**\n\n"
                f"📤 Uploading video ({file_size / (1024*1024):.1f}MB)...",
                parse_mode=ParseMode.MARKDOWN
            )

            await client.send_chat_action(chat_id=message.chat.id, action=ChatAction.UPLOAD_VIDEO)

            # Prepare caption
            caption = (
                f"🎬 TikTok Video Downloaded\n\n"
                f"📝 Title: {result.get('title', 'TikTok Video')[:100]}\n"
                f"👤 Author: @{result.get('author', 'Unknown')}\n"
                f"🎯 Quality: {result.get('quality', 'HD')}\n"
                f"📱 Size: {file_size / (1024*1024):.1f}MB\n\n"
                f"✨ Downloaded without watermark in HD quality!"
            )

            # Real-time progress callback for large video uploads
            last_progress_time = [0.0]

            async def upload_progress(current, total):
                now = time.time()
                if now - last_progress_time[0] >= 3.0:
                    last_progress_time[0] = now
                    percent = (current / max(total, 1)) * 100
                    mb_current = current / (1024 * 1024)
                    mb_total = total / (1024 * 1024)
                    try:
                        await processing_message.edit_text(
                            f"📤 **Uploading your video...**\n\n"
                            f"📊 Progress: `{mb_current:.1f}MB` / `{mb_total:.1f}MB` ({percent:.1f}%)\n"
                            f"⏳ Please wait...",
                            parse_mode=ParseMode.MARKDOWN
                        )
                    except Exception:
                        pass

            # Upload video directly via MTProto (supports up to 2GB!)
            await self.app.send_video(
                chat_id=message.chat.id,
                video=temp_file_path,
                caption=caption,
                supports_streaming=True,
                reply_to_message_id=message.id,
                progress=upload_progress
            )

            # Delete the status message
            try:
                await processing_message.delete()
            except Exception:
                pass

            self.stats['successful_downloads'] += 1
            logger.info(f"Successfully sent {file_size / (1024*1024):.1f}MB video to user {user_id}")

        except FloodWait as fw:
            logger.warning(f"Telegram FloodWait: {fw.value}s")
            await asyncio.sleep(fw.value)
        except Exception as e:
            self.stats['failed_downloads'] += 1
            logger.error(f"Error handling TikTok URL: {e}", exc_info=True)
            try:
                await processing_message.edit_text(
                    f"❌ **Upload Failed**\n\n"
                    f"Error: {str(e)[:150]}\n\n"
                    f"Please try again or choose standard quality.",
                    parse_mode=ParseMode.MARKDOWN
                )
            except Exception:
                pass

            if self.admin_chat_id:
                try:
                    await self.app.send_message(
                        chat_id=int(self.admin_chat_id),
                        text=f"❌ Error in bot:\nUser: {user_id}\nURL: {tiktok_url}\nError: {str(e)[:200]}"
                    )
                except Exception:
                    pass
        finally:
            # Always clean up temporary file from disk
            if temp_file_path and os.path.exists(temp_file_path):
                try:
                    os.unlink(temp_file_path)
                    logger.info("Cleaned up temporary video file")
                except Exception as e:
                    logger.warning(f"Failed to delete temp file {temp_file_path}: {e}")
            gc.collect()

    async def handle_other_messages(self, client: Client, message: Message) -> None:
        """Handle non-TikTok messages"""
        text = (message.text or "").strip().lower()

        if any(word in text for word in ['hello', 'hi', 'hey', 'start']):
            await message.reply_text(
                "👋 Hello! Send me a TikTok video link and I'll download it for you in HD quality!\n\n"
                "Use /help if you need assistance. 🎬",
                parse_mode=ParseMode.MARKDOWN
            )
        else:
            await message.reply_text(
                "🤔 I didn't find a TikTok link in your message.\n\n"
                "Please send me a valid TikTok video URL, or use /help for instructions.",
                parse_mode=ParseMode.MARKDOWN
            )

    def extract_tiktok_url(self, text: str) -> Optional[str]:
        """Extract TikTok URL from text"""
        url_patterns = [
            r'https?://(?:www\.)?tiktok\.com/@[^/]+/video/\d+[^\s]*',
            r'https?://(?:vm|vt)\.tiktok\.com/[A-Za-z0-9]+[^\s]*',
            r'https?://(?:www\.)?tiktok\.com/t/[A-Za-z0-9]+[^\s]*',
            r'https?://[^\s]*tiktok[^\s]*'
        ]

        for pattern in url_patterns:
            match = re.search(pattern, text)
            if match:
                url = match.group(0)
                url = re.sub(r'[.,;!?]*$', '', url)
                if self.is_valid_tiktok_url(url):
                    return url
        return None

    def is_valid_tiktok_url(self, url: str) -> bool:
        """Check if URL is a valid TikTok URL"""
        if not validators.url(url):
            return False
        tiktok_domains = ['tiktok.com', 'vm.tiktok.com', 'vt.tiktok.com']
        return any(domain in url.lower() for domain in tiktok_domains)

    def run(self):
        """Run the Pyrogram MTProto bot client"""
        logger.info("🚀 Starting TikTok Downloader Bot (MTProto 2GB Mode)...")
        self.app.run()


def main():
    """Main entry point"""
    try:
        bot = TikTokBot()
        bot.run()
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.critical(f"Bot crashed: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    main()