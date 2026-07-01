# Waifu & Husbando Catcher (Collect Em All)

A Telegram bot character collection game where the bot spawns anime characters in Telegram groups based on message frequency. Users compete to guess and collect characters to build their harem.

## How to Run

The bot starts automatically via the "Start application" workflow:
```
python3 -m shivu
```

## Project Structure

- `shivu/` — Main bot package
  - `__main__.py` — Entry point, message counter, guess logic
  - `__init__.py` — Bot/DB client initialization
  - `config.py` — Configuration (token, MongoDB URL, etc.)
  - `modules/` — Bot feature modules (harem, trade, leaderboard, etc.)
- `requirements.txt` — Python dependencies

## Configuration

All config is in `shivu/config.py`:
- `TOKEN` — Telegram Bot Token
- `mongo_url` — MongoDB Atlas connection string
- `api_id` / `api_hash` — Telegram API credentials (from my.telegram.org)
- `OWNER_ID` — Bot owner's Telegram user ID
- `GROUP_ID` — Main group chat ID
- `CHARA_CHANNEL_ID` — Channel for character uploads

## Dependencies

- `python-telegram-bot==20.6` — Main bot framework
- `pyrogram` + `tgcrypto` — Additional Telegram client
- `motor` + `pymongo` — Async MongoDB driver
- `apscheduler` — Job scheduling
- `aiohttp`, `requests` — HTTP clients

## User Preferences

(none set)
