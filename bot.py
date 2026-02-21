import time
import asyncio
import logging
import threading
import pyrogram.utils
import urllib.request
from aiohttp import web
from pyrogram import Client
from pyrogram.types import BotCommand
from SilentXForward.forward import start_processor, set_user_client
from SilentXForward import web_server
from config import API_ID, API_HASH, BOT_TOKEN, TG_WORKERS, WEB_SERVER, PORT, APP_URL, PING_INTERVAL, USER_SESSION_STRING

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def ping_loop():
    while True:
        try:
            with urllib.request.urlopen(APP_URL, timeout=10) as response:
                if response.status == 200:
                    logger.info("✅ Ping Successful")
                else:
                    logger.error(f"⚠️ Ping Failed: {response.status}")
        except Exception as e:
            logger.debug(f"❌ Exception During Ping: {e}")
        time.sleep(PING_INTERVAL)

if APP_URL:
    threading.Thread(target=ping_loop, daemon=True).start()
    
async def create_server():
    try:
        app = web.AppRunner(await web_server())
        await app.setup()
        await web.TCPSite(app, "0.0.0.0", PORT).start()
        logger.info(f"Web server started on port {PORT}")
    except Exception as e:
        logger.error(f"Failed to start web server: {e}")

class Bot(Client):
    def __init__(self):
        super().__init__(
            "SilentXForwardBot",
            api_id=API_ID,
            api_hash=API_HASH,
            bot_token=BOT_TOKEN,
            workers=TG_WORKERS,
            sleep_threshold=10,
            plugins={"root": "SilentXForward"}
        )

    async def start(self, *args, **kwargs):
        await super().start(*args, **kwargs)
        me = await self.get_me()
        logger.info(f"Bot Started! Name: {me.first_name} (@{me.username})")

        self.user_client = None
        if USER_SESSION_STRING:
            try:
                self.user_client = Client(
                    "SilentXForwardUserClient",
                    api_id=API_ID,
                    api_hash=API_HASH,
                    session_string=USER_SESSION_STRING,
                    no_updates=True,
                )
                await self.user_client.start()
                set_user_client(self.user_client)
                ume = await self.user_client.get_me()
                logger.info(
                    "✅ Userbot session connected: %s (%s)",
                    getattr(ume, "first_name", ""),
                    getattr(ume, "id", ""),
                )
            except Exception as e:
                logger.error(f"Failed to start userbot session: {e}")
                self.user_client = None

        await self.set_bot_commands(
            [
                BotCommand("start", "Start the bot"),
                BotCommand("help", "Show help menu"),
                BotCommand("commands", "Show all commands"),
                BotCommand("about", "Show bot information"),
                BotCommand("forward", "Start forward setup"),
                BotCommand("oldforward", "Forward old messages by range"),
                BotCommand("set", "Add source-target mapping"),
                BotCommand("remove_target", "Remove one target from source"),
                BotCommand("remove_source", "Remove source mapping"),
                BotCommand("list", "Show all mappings"),
                BotCommand("clear", "Clear all mappings"),
                BotCommand("unequify", "Remove duplicate targets"),
                BotCommand("settings", "Show your settings"),
                BotCommand("status", "Show advanced status"),
                BotCommand("cancel", "Cancel ongoing setup"),
                BotCommand("reset", "Reset your settings"),
                BotCommand("donate", "Support developers"),
                BotCommand("resetall", "Reset all users (owner only)"),
                BotCommand("broadcast", "Broadcast message (owner only)"),
                BotCommand("pauseforward", "Pause forwarding (owner only)"),
                BotCommand("resumeforward", "Resume forwarding (owner only)"),
                BotCommand("stats", "Show runtime stats (owner only)"),
                BotCommand("addusersession", "Add userbot session (owner only)"),
                BotCommand("addbottoken", "Add managed bot token (owner only)"),
                BotCommand("accounts", "Show managed account info (owner only)"),
                BotCommand("restart", "Restart bot (owner only)"),
            ]
        )
        
        if WEB_SERVER:
            await create_server()
            
        self.processor_tasks = await start_processor(self)
        logger.info(f"✅ Auto Forwarding Started For {len(self.processor_tasks)} Sources")

    async def stop(self, *args, **kwargs):
        logger.info("🛑 Stopping Auto Forwarding...")
        for task in getattr(self, "processor_tasks", {}).values():
            task.cancel()

        if getattr(self, "user_client", None):
            try:
                await self.user_client.stop()
            except Exception:
                pass

        await super().stop(*args, **kwargs)
        logger.info("Bot Stopped")

if __name__ == '__main__':
    Bot().run()
