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
        self.max_file_size = 200 * 1024 * 1024  # 50MB Telegram limit

        if not self.token:
            raise ValueError("TELEGRAM_BOT_TOKEN is required in environment variables")

        # Statistics
        self.stats = {
            'total_downloads': 0,
            'successful_downloads': 0,
            'failed_downloads': 0,
            'start_time': datetime.now()
        }

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

Need more help? Contact @YourSupportUsername
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

            # Update processing message
            await processing_message.edit_text(
                "🔄 **Processing your request...**\n\n"
                "📥 Downloading HD video...",
                parse_mode=ParseMode.MARKDOWN
            )

            result = await download_tiktok_video(tiktok_url)

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
                await processing_message.edit_text(
                    f"❌ **File Too Large**\n\n"
                    f"Video size: {file_size / (1024*1024):.1f}MB\n"
                    f"Telegram limit: {self.max_file_size / (1024*1024)}MB\n\n"
                    "Try downloading a shorter video.",
                    parse_mode=ParseMode.MARKDOWN
                )
                self.stats['failed_downloads'] += 1
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
                # Prepare caption
                caption = f"""
🎬 **TikTok Video Downloaded**

📝 **Title:** {result.get('title', 'TikTok Video')[:100]}
👤 **Author:** @{result.get('author', 'Unknown')}
🎯 **Quality:** {result.get('quality', 'HD')}
📱 **Size:** {file_size / (1024*1024):.1f}MB

✨ Downloaded without watermark in HD quality!

🤖 @YourBotUsername
                """.strip()

                # Send video
                with open(temp_file_path, 'rb') as video_file:
                    await context.bot.send_video(
                        chat_id=update.effective_chat.id,
                        video=video_file,
                        caption=caption,
                        parse_mode=ParseMode.MARKDOWN,
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
        await query.answer()

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

        try:
            if is_production:
                self._run_webhook(app)
            else:
                self._run_polling(app)
        finally:
            # Ensure proper cleanup
            try:
                if hasattr(app, 'stop'):
                    app.stop()
            except:
                pass

    def _add_handlers(self, app):
        """Add all handlers to the application"""
        app.add_handler(CommandHandler("start", self.start_command))
        app.add_handler(CommandHandler("help", self.help_command))
        app.add_handler(CommandHandler("stats", self.stats_command))
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

    def _run_webhook(self, app):
        """Run bot in webhook mode for production"""
        webhook_url = os.getenv('WEBHOOK_URL') or os.getenv('RENDER_EXTERNAL_URL')

        if not webhook_url:
            logger.error("❌ No webhook URL provided for production mode!")
            logger.info("🔄 Falling back to polling mode...")
            raise Exception("No webhook URL configured")

        # Use webhook path without token for better security
        webhook_path = f"webhook/{self.token}"

        logger.info("🌐 Starting webhook mode...")
        logger.info(f"🔗 Webhook URL: {webhook_url}/{webhook_path}")

        try:
            app.run_webhook(
                listen="0.0.0.0",
                port=int(os.getenv('PORT', 10000)),  # Render uses 10000
                url_path=webhook_path,
                webhook_url=f"{webhook_url}/{webhook_path}",
                drop_pending_updates=True,
                allowed_updates=Update.ALL_TYPES
            )
        except Exception as e:
            logger.error(f"❌ Webhook failed: {e}")
            raise  # Don't fall back here, let the retry mechanism handle it

    def _run_polling(self, app):
        """Run bot in polling mode for development"""
        logger.info("🔄 Starting polling mode...")
        try:
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