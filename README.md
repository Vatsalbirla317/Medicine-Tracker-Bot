# 🩺 Medicine Tracker Bot

A Telegram bot that automates daily medicine reminders and status tracking for family/group care. Sends scheduled notifications, tracks dose confirmations, and allows easy status checks — all in a private/group chat.

---

## 📌 Features

- ⏰ Sends automated medicine reminders at 10:00 AM and 7:30 PM (IST)
- ✅ Tracks whether morning and evening doses are confirmed
- 🤖 Supports natural confirmations like "done", "dawa le li", "medicine taken"
- 🧠 Maintains daily memory of doses and resets at midnight
- 🔁 Sends follow-up alerts if medicine isn't marked as taken
- 📊 Responds to queries like "dawa ka status" or "meds update"

---

## 🛠 Tech Stack

- Python 3.11+
- [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot)
- Render (for deployment)
- `zoneinfo` for timezone handling
- `HTTPServer` to keep Render service alive

---

## 🚀 Usage & Setup

### 🧩 Prerequisites

- Python installed
- Telegram Bot token from [BotFather](https://t.me/BotFather)
- A group/chat ID where the bot is a member
- Optionally: a Render account to deploy

### 🛠️ Local Setup

1. **Clone the repo**:
   ```bash
   git clone https://github.com/Vatsalbirla317/Medicine-Tracker-Bot.git
   cd Medicine-Tracker-Bot
