# MindGuide 🧘‍♂️

MindGuide is a Telegram chatbot that acts as an empathetic mental wellness coach. It combines a local LLM (via Ollama) with a Retrieval-Augmented Generation (RAG) pipeline to ground its responses in curated wellness content, while applying built-in safety rules and crisis detection.

> ⚠️ **Disclaimer:** MindGuide is not a licensed therapist or medical professional. It does not diagnose conditions or prescribe treatment. It is a supportive tool for self-reflection and general wellness guidance only. If you or someone you know is in crisis, please contact local emergency services or a crisis helpline immediately.

---

## Features

- 💬 **Telegram bot** built with `aiogram`, supporting `/start`, `/help`, and `/clear` commands
- 🧠 **RAG pipeline** — retrieves relevant context from a Chroma vector store before generating a response
- 🦙 **Local inference** via [Ollama](https://ollama.com/), using a configurable chat model and `nomic-embed-text` embeddings
- 🗂️ **Per-user chat history** with automatic trimming to the last 20 messages
- 🚨 **Crisis keyword detection** that intercepts messages with self-harm/suicide language and responds with helpline information instead of generating an LLM reply
- 📏 **Guardrailed system prompt** enforcing response length, tone, and safety boundaries (no diagnoses, no medication advice, always encouraging professional help when needed)

## How it works

1. A user sends a message to the bot.
2. The message is checked against a crisis-keyword list. If a match is found, the bot immediately replies with helpline information and skips the LLM call.
3. Otherwise, the message is embedded and used to query a Chroma vector store for the top relevant chunks of context.
4. The retrieved context is injected into a system prompt (`MindGuide` persona) along with the user's recent chat history.
5. The combined prompt is sent to a local Ollama model, and the reply is sent back to the user.
6. The conversation turn is stored in memory, capped at the last 20 messages per user.

## Tech stack

| Component | Tool |
|---|---|
| Bot framework | [aiogram](https://docs.aiogram.dev/) |
| LLM inference | [Ollama](https://ollama.com/) |
| Vector store | [Chroma](https://www.trychroma.com/) via `langchain_chroma` |
| Embeddings | `nomic-embed-text` via `langchain_ollama` |
| Document loading & splitting | `langchain_community`, `langchain_text_splitters` |
| Config | `python-dotenv` |

## Project structure

```
.
├── bot.py              # Main Telegram bot logic (handlers, RAG, crisis detection)
├── create_db.ipynb     # Notebook to build the Chroma vector store from data.txt
├── data.txt             # Source wellness content to embed (not included)
├── data_db/             # Persisted Chroma vector store (generated)
└── .env                  # Environment variables (not committed)
```

## Setup

### Prerequisites

- Python 3.10+
- [Ollama](https://ollama.com/) installed and running locally
- A Telegram bot token (from [@BotFather](https://t.me/BotFather))

### 1. Clone and install dependencies

```bash
git clone https://github.com/Nikhilvijai/<repo-name>.git
cd <repo-name>
pip install -r requirements.txt
```

### 2. Pull the required Ollama models

```bash
ollama pull nomic-embed-text
ollama pull <your-chat-model>   # e.g. gemma2, llama3, etc.
```

### 3. Configure environment variables

Create a `.env` file in the project root:

```env
TELEGRAM_BOT=your_telegram_bot_token
OLLAMA_MODEL=your_chat_model_name
```

### 4. Build the vector database

Add your wellness content to `data.txt`, then run `create_db.ipynb` to chunk, embed, and persist it to a local Chroma store (`./data_db`).

### 5. Run the bot

```bash
python bot.py
```

## Usage

| Command | Description |
|---|---|
| `/start` | Greet the user and introduce the bot |
| `/help` | List available commands |
| `/clear` | Clear the user's conversation history |

Simply message the bot to start a conversation.

## Safety design

- The system prompt explicitly forbids diagnosing, prescribing, or claiming clinical authority.
- Crisis-related messages bypass the LLM entirely and trigger a fixed, India-specific helpline response (KIRAN Mental Health Helpline: 1800-599-0019).
- Responses are capped at ~300 words to keep guidance concise and actionable.

## Future improvements

- [ ] Expand crisis keyword detection with multilingual support
- [ ] Add logging/analytics for usage patterns (anonymized)
- [ ] Support additional helpline numbers based on user locale
- [ ] Deploy with persistent storage and containerization (Docker)

## License

MIT

