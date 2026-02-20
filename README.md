# SilentXForward Bot

A Powerful And Efficient Telegram Bot Designed To Forward Videos And Documents From Multiple Source Channels To Multiple Target Channels Without The "Forwarded From" Tag.

**Join Telegram - [SilentXBotz](https://t.me/SilentXBotz)**

## What's New ? 
- Now User Can Set There Source And Target Chat From Bot PM.

## Features

- **Multi-Source & Multi-Target**: Supports Forwarding From Multiple Source Channels To Multiple Destination Channels.
- **Advanced Content Filtering**: Forward videos/documents by default and optionally enable photos/audio via env vars.
- **Tag Removal**: Forwards Messages Without The "Forwarded From" Tag.
- **Smart Delivery**: Single posts are forwarded immediately while albums are grouped to preserve order.
- **Retry & FloodWait Handling**: Automatic retry with bounded queue retries to avoid infinite loops.
- **Keep-Alive**: Built-In Web Server To Keep The Bot Running On Platform Like Heroku/Koyeb.

## Configuration

The Bot Is Configured Using .

| Variable | Description | Required | Default |
| :--- | :--- | :--- | :--- |
| `API_ID` | Your Telegram API ID From [my.telegram.org](https://my.telegram.org) | Yes | - |
| `API_HASH` | Your Telegram API Hash From [my.telegram.org](https://my.telegram.org) | Yes | - |
| `BOT_TOKEN` | Your Bot Token From [@BotFather](https://t.me/BotFather) | Yes | - |
| `WEB_SERVER` | Set To `True` To Enable The Keep-Alive Web Server. | Optional | `True` |
| `PORT` | Port For The Web Server. | Optional | `8080` |
| `TG_WORKERS` | Number Of Pyrogram workers. | Optional | `4` |
| `BUFFER_DELAY` | Delay (seconds) for collecting album items before forwarding. | Optional | `4` |
| `FORWARD_DELAY_SECONDS` | Delay between forwarded files for flood safety. | Optional | `0.3` |
| `MAX_QUEUE_RETRIES` | Maximum retries for failed target forwarding. | Optional | `3` |
| `FORWARD_VIDEO` | Forward video messages. | Optional | `True` |
| `FORWARD_DOCUMENT` | Forward document messages. | Optional | `True` |
| `FORWARD_PHOTO` | Forward photo messages. | Optional | `False` |
| `FORWARD_AUDIO` | Forward audio messages. | Optional | `False` |
| `APP_URL` | URL Of Your Deployed App (Used For Self-Pinning To Keep Awake). | Optional | `None` |


## Deployment

### Deploy on Heroku

[![Deploy](https://www.herokucdn.com/deploy/button.svg)](https://heroku.com/deploy)

1. Click The Button Above.
2. Fill In The Required Environment Variables.
3. Click **Deploy app**.
4. Turn On The **worker** Dyno (And **web** Dyno If Using `WEB_SERVER`).

### Deploy on Koyeb/Render (Using Docker)

1. Fork This Repository.
2. Create A New Service On Koyeb/Render.
3. Select "Docker" As The Deployment Method.
4. Set The Environment Variables.
5. Deploy.

### Local Deployment

1. **Clone the repository:**
   ```bash
   git clone https://github.com/NBBotz/Auto-Forward-Bot.git
   cd Auto-Forward-Bot
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set environment variables:**
   You can create a `.env` file or export them in your terminal.
   ```bash
   export API_ID=your_api_id
   export API_HASH=your_api_hash
   export BOT_TOKEN=your_bot_token
   export SOURCE_CHANNELS="-10012345678, -10087654321"
   export TARGET_CHANNELS="-10011223344, -10055667788"
   ```

4. **Run the bot:**
   ```bash
   python bot.py
   ```

## Credits

- Built With [Pyrogram](https://github.com/pyrogram/pyrogram)
- Maintained By [SilentXBotz](https://t.me/SilentXBotz)
