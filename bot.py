
import asyncio
import os
from collections import defaultdict

from aiogram import Bot, Dispatcher, executor, types
from dotenv import load_dotenv
import ollama

from langchain_ollama import OllamaEmbeddings
from langchain_chroma import Chroma

load_dotenv()

TELEGRAM_BOT = os.getenv("TELEGRAM_BOT")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "gemma4:e4b")

if not TELEGRAM_BOT:
    raise RuntimeError("Missing TELEGRAM_BOT in .env")

CRISIS_KEYWORDS = [
    "suicide", "kill myself", "end my life", "want to die",
    "self harm", "self-harm", "hurt myself", "no reason to live",
]

CRISIS_RESPONSE = (
    "I'm really concerned about what you shared. "
    "Please contact a trusted person, local emergency services, "
    "or a crisis helpline immediately.\n\n"
    "India: KIRAN Mental Health Helpline: 1800-599-0019"
)

SYSTEM_TEMPLATE = """
You are Heyy Bot, an empathetic mental wellness coach.

Your role is to:
- Help users understand and manage emotions.
- Teach evidence-based techniques from CBT, ACT, mindfulness, positive psychology, and stress management.
- Ask thoughtful questions that encourage self-reflection.
- Help users identify cognitive distortions and unhelpful thought patterns.
- Provide practical exercises, journaling prompts, breathing exercises, and coping strategies.
- Encourage healthy habits such as sleep, exercise, social connection, and goal setting.

Response rules:
- Keep responses under 300 words.
- Be concise.
- Avoid excessively long explanations.
 
Communication style:
- Warm, empathetic, non-judgmental, and patient.
- Listen carefully before offering advice.
- Use simple language.
- Validate emotions without reinforcing harmful beliefs.
- Ask one or two follow-up questions when more context is needed.

Safety rules:
- Never claim to be a licensed psychologist, psychiatrist, or medical professional.
- Never diagnose mental health conditions.
- Never prescribe medication or advise stopping medication.
- If the user expresses thoughts of self-harm, suicide, harming others, severe depression, psychosis, or an emergency situation:
- Encourage immediate contact with local emergency services, a crisis hotline, or a trusted person.
- Focus on safety and support.
- Avoid providing treatment instructions.

Framework:
1. Listen and summarize the user's concern.
2. Validate emotions.
3. Explore underlying thoughts and beliefs.
4. Suggest evidence-based coping strategies.
5. Help create an actionable next step.
6. End with a reflective question.

Your goal is to improve emotional well-being, resilience, self-awareness, and healthy coping skills.
Use retrieved context when relevant.
If retrieved context is insufficient, answer using general
evidence-based mental wellness knowledge.

Retrieved Context:
{knowledge}
"""

embeddings = OllamaEmbeddings(model="nomic-embed-text")

vectorstore = Chroma(
    persist_directory="./data_db",
    collection_name="my_documents",
    embedding_function=embeddings,
)

chat_history = defaultdict(list)

bot = Bot(token=TELEGRAM_BOT)
dp = Dispatcher(bot)


def contains_crisis_language(text: str) -> bool:
    text = text.lower()
    return any(k in text for k in CRISIS_KEYWORDS)


def run_inference(user_id: int, user_text: str) -> str:
    retriever = vectorstore.as_retriever(
        search_kwargs={"k":5}
    )

    docs = retriever.invoke(user_text)

    if docs:
        knowledge = "\n\n".join(
            f"Document {i+1}:\n{d.page_content}"
            for i, d in enumerate(docs)
        )
    else:
        knowledge = "No relevant context found."

    system_prompt = SYSTEM_TEMPLATE.format(knowledge=knowledge)

    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(chat_history[user_id])
    messages.append({"role": "user", "content": user_text})

    response = ollama.chat(
        model=OLLAMA_MODEL,
        messages=messages,
    )

    assistant = response["message"]["content"]

    chat_history[user_id].append(
        {"role": "user", "content": user_text}
    )
    chat_history[user_id].append(
        {"role": "assistant", "content": assistant}
    )

    if len(chat_history[user_id]) > 20:
        chat_history[user_id] = chat_history[user_id][-20:]

    return assistant


@dp.message_handler(commands=["start"])
async def start(message: types.Message):
    await message.reply(
        "Hello! I'm Heyy Bot.\n"
        "Send me a message anytime.\n"
        "/help for commands."
    )


@dp.message_handler(commands=["help"])
async def help_cmd(message: types.Message):
    await message.reply(
        "/start - Start bot\n"
        "/help - Show help\n"
        "/clear - Clear conversation"
    )


@dp.message_handler(commands=["clear"])
async def clear(message: types.Message):
    uid = message.from_user.id
    chat_history.pop(uid, None)
    await message.reply("Conversation history cleared.")


@dp.message_handler()
async def chat(message: types.Message):

    if contains_crisis_language(message.text):
        await message.reply(CRISIS_RESPONSE)
        return

    await bot.send_chat_action(message.chat.id, "typing")

    try:
        reply = await asyncio.to_thread(
            run_inference,
            message.from_user.id,
            message.text,
        )
    except Exception as e:
        reply = f"Error: {e}"

    if len(reply) > 4000:
        for i in range(0, len(reply), 4000):
            await message.reply(reply[i:i+4000])
    else:
        await message.reply(reply)


if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
