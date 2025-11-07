import os
import asyncio
import logging
import tempfile
from typing import Optional
from datetime import datetime
import validators

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes
)
from telegram.constants import ChatAction, ParseMode
from telegram.error import TelegramError, BadRequest, TimedOut

from dotenv import load_dotenv
from tiktok_downloader import download_tiktok_video

# Load environment variables
load_dotenv()

# Global variable for Flask webhook integration
telegram_app = None

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO if not os.getenv('DEBUG') else logging.DEBUG
)
logger = logging.getLogger(__name__)

class TikTokBot:
    """
    TikTok Video Downloader Telegram Bot
    Downloads TikTok videos in HD quality without watermarks
    """

    def __init__(self):
        self.token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.admin_chat_id = os.getenv('ADMIN_CHAT_ID')
        self.storage_channel_id = os.getenv('STORAGE_CHANNEL_ID')
        self.max_file_size = 50 * 1024 * 1024  # 50MB Telegram limit for direct upload
        self.max_channel_file_size = 400 * 1024 * 1024  # 400MB limit for channel storage

        if not self.token:
            raise ValueError("TELEGRAM_BOT_TOKEN is required in environment variables")

        if not self.storage_channel_id:
            logger.warning("STORAGE_CHANNEL_ID not set - large file storage will not work")

        # Statistics
        self.stats = {
            'total_downloads': 0,
            'successful_downloads': 0,
            'failed_downloads': 0,
            'start_time': datetime.now()
        }

        # User quality preferences (user_id: quality)
        # Quality options: 'hd' (default), 'standard'
        self.user_quality_preferences = {}

        # Temporary storage for large file requests
        # Format: {user_id: {'url': original_url, 'video_url': direct_link, 'result': video_info}}
        self.pending_large_files = {}

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /start command"""
        user = update.effective_user

        welcome_message = f"""
🎬 **TikTok HD Downloader Bot**

👋 Hello {user.first_name}! I can help you download TikTok videos in HD quality without watermarks.

**How to use:**
1️⃣ Send me any TikTok video link
2️⃣ Wait while I process it
3️⃣ Get your HD video without watermark!

**Supported formats:**
• tiktok.com/@user/video/123456
• vm.tiktok.com/ABC123
• vt.tiktok.com/ABC123

**Features:**
✅ HD Quality (up to 1080p/4K if available)
✅ No watermarks
✅ Fast processing
✅ Multiple quality options
✅ Original audio quality

**Commands:**
/start - Show this message
/help - Get help and examples
/stats - View bot statistics
/quality - Choose default quality preference

Ready to download? Just send me a TikTok link! 🚀
        """

        keyboard = [
            [InlineKeyboardButton("📱 How to get TikTok link", callback_data="help_link")],
            [InlineKeyboardButton("⚙️ Quality Settings", callback_data="quality_settings")],
            [InlineKeyboardButton("📊 Bot Stats", callback_data="show_stats")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            welcome_message,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=reply_markup
        )

        # Log new user
        logger.info(f"New user started bot: {user.id} - {user.username or user.first_name}")

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /help command"""
        help_message = """
📚 **Help & Instructions**

**Step-by-step guide:**
1. Open TikTok app on your phone
2. Find the video you want to download
3. Tap the "Share" button (arrow icon)
4. Select "Copy Link"
5. Come back to this bot and paste the link
6. Wait for the magic! ✨

**Supported URL formats:**
• `https://www.tiktok.com/@username/video/1234567890`
• `https://vm.tiktok.com/ABC123DEF/`
• `https://vt.tiktok.com/ABC123/`
• `https://tiktok.com/t/ABC123/`

**Quality Options:**
🔥 **HD/4K** - Highest available quality
📺 **Standard** - Good quality, smaller file
🎵 **Audio Only** - Extract MP3 audio

**Tips:**
• Videos are processed in HD when available
• Some videos might be region-locked
• Private accounts may not work
• Very large files might take longer

**Troubleshooting:**
❌ **"Invalid URL"** - Check your link format
❌ **"Video not found"** - Video might be deleted/private
❌ **"Download failed"** - Try again or check if video exists

Need more help? Contact @SupportBot
        """

        keyboard = [
            [InlineKeyboardButton("🔙 Back to Main", callback_data="back_main")],
            [InlineKeyboardButton("💬 Contact Support", url="https://t.me/YourSupportUsername")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            help_message,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=reply_markup
        )

    async def stats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /stats command"""
        uptime = datetime.now() - self.stats['start_time']

        stats_message = f"""
📊 **Bot Statistics**

**Downloads:**
✅ Successful: {self.stats['successful_downloads']}
❌ Failed: {self.stats['failed_downloads']}
📈 Total: {self.stats['total_downloads']}

**Success Rate:** {(self.stats['successful_downloads']/max(self.stats['total_downloads'], 1)*100):.1f}%

**Uptime:** {str(uptime).split('.')[0]}

**Bot Info:**
🤖 Version: 2.0
🚀 Status: Running smoothly
⚡ Speed: HD downloads in seconds
        """

        keyboard = [
            [InlineKeyboardButton("🔄 Refresh", callback_data="show_stats")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            stats_message,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=reply_markup
        )

    async def quality_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /quality command"""
        user_id = update.effective_user.id
        current_quality = self.user_quality_preferences.get(user_id, 'hd')

        if current_quality == 'hd':
            current_setting = "Auto HD ✅"
            hd_marker = " ✅"
            std_marker = ""
        else:
            current_setting = "Standard ✅"
            hd_marker = ""
            std_marker = " ✅"

        quality_message = f"""
⚙️ **Quality Settings**

**Available Options:**
🔥 **Auto HD** - Best quality available{hd_marker}
📺 **Standard** - Good quality, faster download{std_marker}
🎵 **Audio Only** - Extract MP3 (Coming soon)

**Current Setting:** {current_setting}

Choose your preferred quality setting below:
        """

        keyboard = [
            [InlineKeyboardButton("🔥 Auto HD", callback_data="quality_hd")],
            [InlineKeyboardButton("📺 Standard", callback_data="quality_standard")],
            [InlineKeyboardButton("🔙 Back to Main Menu", callback_data="back_main")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            quality_message,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=reply_markup
        )

    async def handle_tiktok_url(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle TikTok URL messages"""
        user = update.effective_user
        message = update.message
        text = message.text.strip()

        # Extract URL from message
        tiktok_url = self.extract_tiktok_url(text)

        if not tiktok_url:
            await message.reply_text(
                "❌ **Invalid TikTok URL**\n\n"
                "Please send a valid TikTok link. Need help? Use /help to see examples.",
                parse_mode=ParseMode.MARKDOWN
            )
            return

        # Show processing message
        processing_message = await message.reply_text(
            "🔄 **Processing your request...**\n\n"
            "⏳ Fetching video information...",
            parse_mode=ParseMode.MARKDOWN
        )

        try:
            # Send typing action
            await context.bot.send_chat_action(
                chat_id=update.effective_chat.id,
                action=ChatAction.TYPING
            )

            # Update statistics
            self.stats['total_downloads'] += 1

            # Download video
            logger.info(f"Processing TikTok URL: {tiktok_url} for user {user.id}")

            # Get user's quality preference
            user_quality = self.user_quality_preferences.get(user.id, 'hd')
            quality_text = "HD" if user_quality == 'hd' else "Standard"

            # Update processing message
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
                    "Please try again or check if the video is available.",
                    parse_mode=ParseMode.MARKDOWN
                )
                self.stats['failed_downloads'] += 1
                logger.error(f"Download failed for {tiktok_url}: {error_message}")
                return

            # Check file size
            video_data = result.get('video_data')
            if not video_data:
                await processing_message.edit_text(
                    "❌ **Download Failed**\n\n"
                    "Could not retrieve video data. Please try again.",
                    parse_mode=ParseMode.MARKDOWN
                )
                self.stats['failed_downloads'] += 1
                return

            file_size = len(video_data)

            if file_size > self.max_file_size:
                # Store the request for later if user wants the link
                user_id = update.effective_user.id
                self.pending_large_files[user_id] = {
                    'url': tiktok_url,
                    'video_url': result.get('video_url'),
                    'result': result,
                    'quality': user_quality
                }

                # Create inline keyboard with options
                keyboard = [
                    [InlineKeyboardButton("☁️ Get via Cloud Storage", callback_data="large_file_link")],
                    [InlineKeyboardButton("📺 Try Standard Quality", callback_data="large_file_standard")],
                    [InlineKeyboardButton("❌ Cancel", callback_data="large_file_cancel")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)

                await processing_message.edit_text(
                    f"⚠️ **File Size Limit Exceeded**\n\n"
                    f"📊 Video size: **{file_size / (1024*1024):.1f}MB**\n"
                    f"📱 Telegram limit: **{self.max_file_size / (1024*1024):.0f}MB**\n\n"
                    f"**What would you like to do?**\n\n"
                    f"☁️ **Get via Cloud Storage** - Upload to cloud, receive video in chat\n"
                    f"📺 **Try Standard Quality** - Download in lower quality (smaller file)\n"
                    f"❌ **Cancel** - Abort this download",
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=reply_markup
                )
                # Don't increment failed downloads yet - user might choose an option
                return

            # Update message for upload
            await processing_message.edit_text(
                "🔄 **Processing your request...**\n\n"
                "📤 Uploading your video...",
                parse_mode=ParseMode.MARKDOWN
            )

            # Send upload action
            await context.bot.send_chat_action(
                chat_id=update.effective_chat.id,
                action=ChatAction.UPLOAD_VIDEO
            )

            # Create a temporary file
            with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as temp_file:
                temp_file.write(video_data)
                temp_file_path = temp_file.name

            try:
                # Escape special characters for Markdown
                def escape_markdown(text):
                    """Escape special characters for Markdown V2"""
                    if not text:
                        return "Unknown"
                    # For MarkdownV1, we need to escape: _ * [ ] ( ) ~ ` > # + - = | { } . !
                    special_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
                    for char in special_chars:
                        text = text.replace(char, '\\' + char)
                    return text

                title = escape_markdown(result.get('title', 'TikTok Video')[:100])
                author = escape_markdown(result.get('author', 'Unknown'))
                quality = escape_markdown(result.get('quality', 'HD'))

                # Prepare caption without Markdown to avoid parsing errors
                caption = (
                    f"🎬 TikTok Video Downloaded\n\n"
                    f"📝 Title: {result.get('title', 'TikTok Video')[:100]}\n"
                    f"👤 Author: @{result.get('author', 'Unknown')}\n"
                    f"🎯 Quality: {result.get('quality', 'HD')}\n"
                    f"📱 Size: {file_size / (1024*1024):.1f}MB\n\n"
                    f"✨ Downloaded without watermark in HD quality!\n\n"
                    f"🤖 @tikdownload98_bot"
                )

                # Send video without Markdown parsing
                with open(temp_file_path, 'rb') as video_file:
                    await context.bot.send_video(
                        chat_id=update.effective_chat.id,
                        video=video_file,
                        caption=caption,
                        supports_streaming=True,
                        reply_to_message_id=message.message_id
                    )

                # Delete processing message
                await processing_message.delete()

                # Update statistics
                self.stats['successful_downloads'] += 1

                logger.info(f"Successfully processed video for user {user.id}: {result.get('title', 'Unknown')}")

            except Exception as e:
                await processing_message.edit_text(
                    f"❌ **Upload Failed**\n\n"
                    f"Error uploading video: {str(e)[:100]}\n\n"
                    "Please try again later.",
                    parse_mode=ParseMode.MARKDOWN
                )
                self.stats['failed_downloads'] += 1
                logger.error(f"Upload error: {e}")
            finally:
                # Clean up temporary file
                try:
                    os.unlink(temp_file_path)
                except:
                    pass

        except Exception as e:
            await processing_message.edit_text(
                f"❌ **Error Occurred**\n\n"
                f"Unexpected error: {str(e)[:100]}\n\n"
                "Please try again later or contact support.",
                parse_mode=ParseMode.MARKDOWN
            )
            self.stats['failed_downloads'] += 1
            logger.error(f"Unexpected error: {e}")

            # Notify admin if configured
            if self.admin_chat_id:
                try:
                    await context.bot.send_message(
                        chat_id=self.admin_chat_id,
                        text=f"❌ Error in bot:\nUser: {user.id}\nURL: {tiktok_url}\nError: {str(e)[:200]}"
                    )
                except:
                    pass

    def extract_tiktok_url(self, text: str) -> Optional[str]:
        """Extract TikTok URL from text"""
        import re

        # Look for TikTok URLs in the text
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
                # Clean up URL (remove trailing punctuation)
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

    async def handle_callback_query(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle inline keyboard callbacks"""
        query = update.callback_query

        # Answer callback query with error handling for event loop issues
        try:
            await query.answer()
        except Exception as e:
            logger.warning(f"Failed to answer callback query: {e}")
            # Continue processing even if answer fails

        if query.data == "help_link":
            help_message = """
📱 **How to get TikTok video link:**

1. Open TikTok app
2. Find the video you want
3. Tap the **Share** button (➡️)
4. Select **Copy Link**
5. Come back here and paste it!

**Alternative method:**
1. Tap and hold on the video
2. Select "Copy Link" from menu
3. Paste here!

That's it! 🎉
            """

            keyboard = [[InlineKeyboardButton("🔙 Back", callback_data="back_main")]]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await query.edit_message_text(
                help_message,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=reply_markup
            )

        elif query.data == "quality_settings":
            quality_message = """
⚙️ **Quality Settings**

**Available Options:**
🔥 **Auto HD** - Best quality available (Default)
📺 **Standard** - Good quality, faster download
🎵 **Audio Only** - Extract MP3 (Coming soon)

**Current Setting:** Auto HD ✅

Quality is automatically selected based on the original video quality.
            """

            keyboard = [
                [InlineKeyboardButton("🔥 Auto HD", callback_data="quality_hd")],
                [InlineKeyboardButton("📺 Standard", callback_data="quality_standard")],
                [InlineKeyboardButton("🔙 Back", callback_data="back_main")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await query.edit_message_text(
                quality_message,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=reply_markup
            )

        elif query.data == "show_stats":
            uptime = datetime.now() - self.stats['start_time']

            stats_message = f"""
📊 **Bot Statistics**

**Downloads:**
✅ Successful: {self.stats['successful_downloads']}
❌ Failed: {self.stats['failed_downloads']}
📈 Total: {self.stats['total_downloads']}

**Success Rate:** {(self.stats['successful_downloads']/max(self.stats['total_downloads'], 1)*100):.1f}%

**Uptime:** {str(uptime).split('.')[0]}

**Status:** 🟢 Online
            """

            keyboard = [
                [InlineKeyboardButton("🔄 Refresh", callback_data="show_stats")],
                [InlineKeyboardButton("🔙 Back", callback_data="back_main")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await query.edit_message_text(
                stats_message,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=reply_markup
            )

        elif query.data == "quality_hd":
            # Store user preference
            user_id = query.from_user.id
            self.user_quality_preferences[user_id] = 'hd'

            try:
                await query.answer("✅ Auto HD quality selected!")
            except Exception as e:
                logger.warning(f"Failed to answer callback query: {e}")

            quality_message = """
⚙️ **Quality Settings**

**Available Options:**
🔥 **Auto HD** - Best quality available ✅
📺 **Standard** - Good quality, faster download
🎵 **Audio Only** - Extract MP3 (Coming soon)

**Current Setting:** Auto HD ✅

Your videos will now be downloaded in the highest quality available.
            """

            keyboard = [
                [InlineKeyboardButton("🔥 Auto HD", callback_data="quality_hd")],
                [InlineKeyboardButton("📺 Standard", callback_data="quality_standard")],
                [InlineKeyboardButton("🔙 Back to Main Menu", callback_data="back_main")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await query.edit_message_text(
                quality_message,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=reply_markup
            )

        elif query.data == "quality_standard":
            # Store user preference
            user_id = query.from_user.id
            self.user_quality_preferences[user_id] = 'standard'

            try:
                await query.answer("✅ Standard quality selected!")
            except Exception as e:
                logger.warning(f"Failed to answer callback query: {e}")

            quality_message = """
⚙️ **Quality Settings**

**Available Options:**
🔥 **Auto HD** - Best quality available
📺 **Standard** - Good quality, faster download ✅
🎵 **Audio Only** - Extract MP3 (Coming soon)

**Current Setting:** Standard ✅

Your videos will now be downloaded in standard quality for faster downloads and smaller file sizes.
            """

            keyboard = [
                [InlineKeyboardButton("🔥 Auto HD", callback_data="quality_hd")],
                [InlineKeyboardButton("📺 Standard", callback_data="quality_standard")],
                [InlineKeyboardButton("🔙 Back to Main Menu", callback_data="back_main")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await query.edit_message_text(
                quality_message,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=reply_markup
            )

        elif query.data == "large_file_link":
            # User wants the video via channel storage
            user_id = query.from_user.id

            try:
                await query.answer("📤 Uploading to storage...")
            except Exception as e:
                logger.warning(f"Failed to answer callback query: {e}")

            if user_id not in self.pending_large_files:
                await query.edit_message_text(
                    "❌ **Session Expired**\n\n"
                    "This request has expired. Please send the TikTok link again.",
                    parse_mode=ParseMode.MARKDOWN
                )
                return

            pending = self.pending_large_files[user_id]
            result = pending.get('result')

            # Check if storage channel is configured
            if not self.storage_channel_id:
                await query.edit_message_text(
                    "❌ **Storage Not Configured**\n\n"
                    "Channel storage is not set up. Please contact the bot administrator.",
                    parse_mode=ParseMode.MARKDOWN
                )
                self.stats['failed_downloads'] += 1
                del self.pending_large_files[user_id]
                return

            # Check if we already have the video data (we should!)
            video_data = result.get('video_data')

            if not video_data:
                # Fallback: Download again if video_data is missing
                await query.edit_message_text(
                    "📥 **Downloading Video...**\n\n"
                    "Please wait, this may take a moment for large files...",
                    parse_mode=ParseMode.MARKDOWN
                )

                original_url = pending.get('url')
                quality = pending.get('quality', 'hd')
                download_result = await download_tiktok_video(original_url, quality=quality)

                if not download_result.get('success'):
                    await query.edit_message_text(
                        "❌ **Download Failed**\n\n"
                        "Could not download the video. Please try again.",
                        parse_mode=ParseMode.MARKDOWN
                    )
                    self.stats['failed_downloads'] += 1
                    del self.pending_large_files[user_id]
                    return

                video_data = download_result.get('video_data')
                if not video_data:
                    await query.edit_message_text(
                        "❌ **Error**\n\n"
                        "Could not retrieve video data. Please try again.",
                        parse_mode=ParseMode.MARKDOWN
                    )
                    self.stats['failed_downloads'] += 1
                    del self.pending_large_files[user_id]
                    return

            file_size = len(video_data)

            # IMPORTANT: Telegram Bot API has a 50MB upload limit (not just sendVideo, but ALL uploads)
            # For files >50MB, we need to provide a direct download link instead
            # https://core.telegram.org/bots/api#sending-files
            if file_size > 50 * 1024 * 1024:  # 50MB
                # Provide direct download link instead of trying to upload
                video_url = result.get('video_url') or pending.get('video_url')

                if video_url:
                    await query.edit_message_text(
                        f"📥 **Download Link Ready**\n\n"
                        f"📊 Video size: **{file_size / (1024*1024):.1f}MB**\n"
                        f"⚠️ File is too large for Telegram Bot API (50MB limit)\n\n"
                        f"**Download directly:**\n"
                        f"🔗 [Click here to download]({video_url})\n\n"
                        f"💡 **Tip:** After downloading, you can send it to Telegram from your device.\n\n"
                        f"🎯 **Or try Standard Quality** for a smaller file that can be sent directly.",
                        parse_mode=ParseMode.MARKDOWN,
                        disable_web_page_preview=False
                    )
                    self.stats['successful_downloads'] += 1
                    del self.pending_large_files[user_id]
                    logger.info(f"Provided direct download link for {file_size / (1024*1024):.1f}MB file to user {user_id}")
                    return
                else:
                    await query.edit_message_text(
                        f"❌ **File Too Large**\n\n"
                        f"📊 Video size: **{file_size / (1024*1024):.1f}MB**\n"
                        f"🚫 Telegram Bot API limit: **50MB**\n\n"
                        f"Unfortunately, the download link is not available.\n"
                        f"Please try **Standard Quality** for a smaller file.",
                        parse_mode=ParseMode.MARKDOWN
                    )
                    self.stats['failed_downloads'] += 1
                    del self.pending_large_files[user_id]
                    return

            # Check if file is too large even for channel storage
            if file_size > self.max_channel_file_size:
                await query.edit_message_text(
                    f"❌ **File Too Large**\n\n"
                    f"📊 Video size: **{file_size / (1024*1024):.1f}MB**\n"
                    f"� Maximum allowed: **{self.max_channel_file_size / (1024*1024):.0f}MB**\n\n"
                    f"This video exceeds even our extended storage limit.\n"
                    f"Please try a shorter video or standard quality.",
                    parse_mode=ParseMode.MARKDOWN
                )
                self.stats['failed_downloads'] += 1
                del self.pending_large_files[user_id]
                return

            # Update status
            await query.edit_message_text(
                "☁️ **Uploading to Storage...**\n\n"
                f"� Size: {file_size / (1024*1024):.1f}MB\n"
                "⏳ This may take a few moments...",
                parse_mode=ParseMode.MARKDOWN
            )

            # Create temporary file for upload
            with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as temp_file:
                temp_file.write(video_data)
                temp_file_path = temp_file.name

            # CRITICAL: Delete video data from memory to free up RAM
            # Large files (100MB+) can exceed memory limits on free hosting
            del video_data
            import gc
            gc.collect()  # Force garbage collection
            logger.info(f"Freed {file_size / (1024*1024):.1f}MB from memory after writing to disk")

            try:
                # Upload to storage channel with retry logic
                max_retries = 3
                retry_delay = 5
                channel_message = None

                for attempt in range(max_retries):
                    try:
                        with open(temp_file_path, 'rb') as video_file:
                            if attempt > 0:
                                await query.edit_message_text(
                                    f"☁️ **Uploading to Storage...**\n\n"
                                    f"📊 Size: {file_size / (1024*1024):.1f}MB\n"
                                    f"🔄 Retry attempt {attempt + 1}/{max_retries}\n"
                                    "⏳ Please wait...",
                                    parse_mode=ParseMode.MARKDOWN
                                )

                            # Use send_document for files >50MB (Telegram API limitation)
                            # send_video has 50MB limit, send_document supports up to 2GB
                            channel_message = await context.bot.send_document(
                                chat_id=self.storage_channel_id,
                                document=video_file,
                                caption=f"🎬 {result.get('title', 'TikTok Video')[:100]}\n"
                                        f"👤 @{result.get('author', 'Unknown')}\n"
                                        f"📊 {file_size / (1024*1024):.1f}MB\n"
                                        f"🔑 User: {user_id}",
                                filename=f"tiktok_video_{user_id}.mp4",
                                connect_timeout=60,
                                pool_timeout=60,
                                read_timeout=600,  # 10 minutes for large files
                                write_timeout=600
                            )
                        break  # Success, exit retry loop

                    except Exception as retry_error:
                        logger.warning(f"Upload attempt {attempt + 1} failed: {retry_error}")
                        if attempt < max_retries - 1:
                            await asyncio.sleep(retry_delay)
                        else:
                            raise  # Re-raise on final attempt

                if not channel_message:
                    raise Exception("Failed to upload after all retries")

                # Get the file_id from the uploaded document
                file_id = channel_message.document.file_id

                logger.info(f"Uploaded large file to channel for user {user_id}, file_id: {file_id}")

                # Now send the video to the user using the file_id
                await query.edit_message_text(
                    "📤 **Sending Video...**\n\n"
                    "Almost done!",
                    parse_mode=ParseMode.MARKDOWN
                )

                caption = (
                    f"🎬 TikTok Video Downloaded\n\n"
                    f"📝 Title: {result.get('title', 'TikTok Video')[:100]}\n"
                    f"� Author: @{result.get('author', 'Unknown')}\n"
                    f"🎯 Quality: {result.get('quality', 'HD')}\n"
                    f"📱 Size: {file_size / (1024*1024):.1f}MB\n\n"
                    f"✨ Downloaded without watermark via cloud storage!\n\n"
                    f"🤖 @tikdownload98_bot"
                )

                # Send video to user using file_id (no re-upload needed!)
                # Note: We use send_document because the file is >50MB
                await context.bot.send_document(
                    chat_id=query.message.chat_id,
                    document=file_id,
                    caption=caption,
                    filename=f"{result.get('title', 'tiktok_video')[:50]}.mp4"
                )

                # Delete the status message
                await query.message.delete()

                # Clean up and update stats
                del self.pending_large_files[user_id]
                self.stats['successful_downloads'] += 1
                logger.info(f"Successfully sent large file via channel storage to user {user_id}")

            except Exception as e:
                await query.edit_message_text(
                    f"❌ **Upload Failed**\n\n"
                    f"Error: {str(e)[:100]}\n\n"
                    "Please try again later or contact support.",
                    parse_mode=ParseMode.MARKDOWN
                )
                self.stats['failed_downloads'] += 1
                logger.error(f"Channel upload error: {e}")
                if user_id in self.pending_large_files:
                    del self.pending_large_files[user_id]
            finally:
                # Clean up temporary file
                try:
                    os.unlink(temp_file_path)
                except:
                    pass

        elif query.data == "large_file_standard":
            # User wants to try standard quality
            user_id = query.from_user.id

            try:
                await query.answer("📺 Switching to standard quality...")
            except Exception as e:
                logger.warning(f"Failed to answer callback query: {e}")

            if user_id not in self.pending_large_files:
                await query.edit_message_text(
                    "❌ **Session Expired**\n\n"
                    "This request has expired. Please send the TikTok link again.",
                    parse_mode=ParseMode.MARKDOWN
                )
                return

            pending = self.pending_large_files[user_id]
            original_url = pending.get('url')
            current_quality = pending.get('quality')

            # Check if already tried standard
            if current_quality == 'standard':
                await query.edit_message_text(
                    "❌ **Already Standard Quality**\n\n"
                    "This video is already in standard quality and still exceeds 50MB.\n\n"
                    "Please use the **Get Storage Link** option instead, or try a different video.",
                    parse_mode=ParseMode.MARKDOWN
                )
                del self.pending_large_files[user_id]
                self.stats['failed_downloads'] += 1
                return

            # Clean up pending request
            del self.pending_large_files[user_id]

            # Show processing message
            await query.edit_message_text(
                "🔄 **Processing your request...**\n\n"
                "📥 Downloading standard quality video...",
                parse_mode=ParseMode.MARKDOWN
            )

            # Try downloading in standard quality
            result = await download_tiktok_video(original_url, quality='standard')

            if not result.get('success'):
                error_message = result.get('error', 'Unknown error occurred')
                await query.edit_message_text(
                    f"❌ **Download Failed**\n\n"
                    f"Error: {error_message}\n\n"
                    "Please try again or use the storage link option.",
                    parse_mode=ParseMode.MARKDOWN
                )
                self.stats['failed_downloads'] += 1
                return

            video_data = result.get('video_data')
            if not video_data:
                await query.edit_message_text(
                    "❌ **Download Failed**\n\n"
                    "Could not retrieve video data. Please try again.",
                    parse_mode=ParseMode.MARKDOWN
                )
                self.stats['failed_downloads'] += 1
                return

            file_size = len(video_data)

            # Check if still too large
            if file_size > self.max_file_size:
                # Store again for link option
                self.pending_large_files[user_id] = {
                    'url': original_url,
                    'video_url': result.get('video_url'),
                    'result': result,
                    'quality': 'standard'
                }

                keyboard = [
                    [InlineKeyboardButton("☁️ Get via Cloud Storage", callback_data="large_file_link")],
                    [InlineKeyboardButton("❌ Cancel", callback_data="large_file_cancel")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)

                await query.edit_message_text(
                    f"⚠️ **Still Too Large**\n\n"
                    f"📊 Standard quality size: **{file_size / (1024*1024):.1f}MB**\n"
                    f"📱 Telegram limit: **{self.max_file_size / (1024*1024):.0f}MB**\n\n"
                    f"Even the standard quality version exceeds Telegram's limit.\n\n"
                    f"**Would you like to get it via cloud storage instead?**",
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=reply_markup
                )
                return

            # File is small enough, upload it
            await query.edit_message_text(
                "🔄 **Processing your request...**\n\n"
                "📤 Uploading your video...",
                parse_mode=ParseMode.MARKDOWN
            )

            # Create temporary file and upload
            with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as temp_file:
                temp_file.write(video_data)
                temp_file_path = temp_file.name

            try:
                caption = (
                    f"🎬 TikTok Video Downloaded\n\n"
                    f"📝 Title: {result.get('title', 'TikTok Video')[:100]}\n"
                    f"👤 Author: @{result.get('author', 'Unknown')}\n"
                    f"🎯 Quality: Standard\n"
                    f"📱 Size: {file_size / (1024*1024):.1f}MB\n\n"
                    f"✨ Downloaded without watermark!\n\n"
                    f"🤖 @tikdownload98_bot"
                )

                with open(temp_file_path, 'rb') as video_file:
                    await context.bot.send_video(
                        chat_id=query.message.chat_id,
                        video=video_file,
                        caption=caption,
                        supports_streaming=True
                    )

                await query.message.delete()
                self.stats['successful_downloads'] += 1
                logger.info(f"Successfully uploaded standard quality for user {user_id}")

            except Exception as e:
                await query.edit_message_text(
                    f"❌ **Upload Failed**\n\n"
                    f"Error: {str(e)[:100]}\n\n"
                    "Please try again later.",
                    parse_mode=ParseMode.MARKDOWN
                )
                self.stats['failed_downloads'] += 1
                logger.error(f"Upload error: {e}")
            finally:
                try:
                    os.unlink(temp_file_path)
                except:
                    pass

        elif query.data == "large_file_cancel":
            # User cancelled the request
            user_id = query.from_user.id

            try:
                await query.answer("❌ Download cancelled")
            except Exception as e:
                logger.warning(f"Failed to answer callback query: {e}")

            if user_id in self.pending_large_files:
                del self.pending_large_files[user_id]

            await query.edit_message_text(
                "❌ **Download Cancelled**\n\n"
                "Feel free to send another TikTok link whenever you're ready! 🎬",
                parse_mode=ParseMode.MARKDOWN
            )
            self.stats['failed_downloads'] += 1

        elif query.data == "back_main":
            # Recreate start message
            user = query.from_user
            welcome_message = f"""
🎬 **TikTok HD Downloader Bot**

👋 Hello {user.first_name}! I can help you download TikTok videos in HD quality without watermarks.

**How to use:**
1️⃣ Send me any TikTok video link
2️⃣ Wait while I process it
3️⃣ Get your HD video without watermark!

Ready to download? Just send me a TikTok link! 🚀
            """

            keyboard = [
                [InlineKeyboardButton("📱 How to get TikTok link", callback_data="help_link")],
                [InlineKeyboardButton("⚙️ Quality Settings", callback_data="quality_settings")],
                [InlineKeyboardButton("📊 Bot Stats", callback_data="show_stats")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await query.edit_message_text(
                welcome_message,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=reply_markup
            )

    async def handle_other_messages(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle non-TikTok messages"""
        message = update.message.text

        if any(word in message.lower() for word in ['hello', 'hi', 'hey', 'start']):
            await update.message.reply_text(
                "👋 Hello! Send me a TikTok video link and I'll download it for you in HD quality!\n\n"
                "Use /help if you need assistance. 🎬",
                parse_mode=ParseMode.MARKDOWN
            )
        else:
            await update.message.reply_text(
                "🤔 I didn't find a TikTok link in your message.\n\n"
                "Please send me a valid TikTok video URL, or use /help for instructions.",
                parse_mode=ParseMode.MARKDOWN
            )

    def run(self):
        """Run the bot with automatic webhook/polling detection"""
        # Create application
        app = Application.builder().token(self.token).build()

        # Add all handlers
        self._add_handlers(app)

        # Detect production environment
        is_production = any([
            os.getenv('RENDER'),
            os.getenv('RAILWAY_ENVIRONMENT'),
            os.getenv('DYNO'),
            os.getenv('WEBHOOK_URL')
        ])

        # Clear any existing webhook first (this fixes the conflict issue)
        self._clear_webhook(app)

        if is_production:
            self._run_webhook(app)
        else:
            self._run_polling(app)

    def _add_handlers(self, app):
        """Add all handlers to the application"""
        app.add_handler(CommandHandler("start", self.start_command))
        app.add_handler(CommandHandler("help", self.help_command))
        app.add_handler(CommandHandler("stats", self.stats_command))
        app.add_handler(CommandHandler("quality", self.quality_command))
        app.add_handler(CallbackQueryHandler(self.handle_callback_query))

        # Handle TikTok URLs
        app.add_handler(MessageHandler(
            filters.TEXT & ~filters.COMMAND & filters.Regex(r'tiktok\.com|vm\.tiktok\.com|vt\.tiktok\.com'),
            self.handle_tiktok_url
        ))

        # Handle other messages
        app.add_handler(MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            self.handle_other_messages
        ))

    def _clear_webhook(self, app):
        """Clear any existing webhook to prevent conflicts"""
        try:
            import asyncio

            async def clear_webhook():
                await app.bot.delete_webhook(drop_pending_updates=True)
                logger.info("🧹 Cleared existing webhook")

            # Check if there's already an event loop
            try:
                loop = asyncio.get_event_loop()
                if loop.is_closed():
                    raise RuntimeError("Loop is closed")
            except RuntimeError:
                # No loop or closed loop, create new one
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

            # Run webhook clearing without closing the loop
            loop.run_until_complete(clear_webhook())

        except Exception as e:
            logger.warning(f"Could not clear webhook: {e}")
            # Continue anyway - this is not critical

    def _run_webhook(self, app):
        """Configure webhook for Flask integration (no separate server)"""
        webhook_url = os.getenv('WEBHOOK_URL') or os.getenv('RENDER_EXTERNAL_URL')

        # For Render, construct URL from service name if not provided
        if not webhook_url and os.getenv('RENDER'):
            service_name = "tikdownloader"  # Should match render.yaml service name
            webhook_url = f"https://{service_name}.onrender.com"

        if not webhook_url:
            logger.error("❌ No webhook URL provided for production mode!")
            logger.info("🔄 Falling back to polling mode...")
            self._run_polling(app)
            return

        # Use webhook path without exposing token
        webhook_path = f"webhook/{self.token}"
        full_webhook_url = f"{webhook_url}/{webhook_path}"

        logger.info("🌐 Configuring webhook mode...")
        logger.info(f"🔗 Webhook URL: {full_webhook_url}")

        try:
            # Set webhook using proper async context
            async def configure_webhook():
                await app.bot.set_webhook(
                    url=full_webhook_url,
                    drop_pending_updates=True,
                    allowed_updates=Update.ALL_TYPES
                )
                logger.info("✅ Webhook configured successfully")

            # Use existing event loop if available
            import asyncio
            try:
                # Try to get existing loop
                loop = asyncio.get_event_loop()
                if loop.is_closed():
                    raise RuntimeError("Loop is closed")
            except RuntimeError:
                # Create new loop if none exists or closed
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

            # Run webhook configuration
            loop.run_until_complete(configure_webhook())

            # Store app globally for Flask webhook handling
            import sys
            sys.modules[__name__].telegram_app = app

            # Keep the main thread alive - Flask handles all HTTP requests
            logger.info("🔄 Webhook mode active - Flask handles all requests")
            import signal
            import time

            def signal_handler(sig, frame):
                logger.info("Received shutdown signal")
                raise KeyboardInterrupt

            signal.signal(signal.SIGTERM, signal_handler)
            signal.signal(signal.SIGINT, signal_handler)

            try:
                while True:
                    time.sleep(60)
            except KeyboardInterrupt:
                logger.info("Webhook mode shutting down...")

        except Exception as e:
            logger.error(f"❌ Webhook configuration failed: {e}")
            logger.info("🔄 Falling back to polling...")
            self._run_polling(app)

    def _run_polling(self, app):
        """Run bot in polling mode for development"""
        logger.info("🔄 Starting polling mode...")
        try:
            # Don't manipulate event loops - let the telegram bot handle it
            app.run_polling(
                drop_pending_updates=True,
                allowed_updates=Update.ALL_TYPES
            )
        except Exception as e:
            logger.error(f"❌ Polling failed: {e}")
            raise

def main():
    """Main entry point"""
    try:
        bot = TikTokBot()
        bot.run()
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Bot crashed: {e}")
        raise

if __name__ == "__main__":
    main()