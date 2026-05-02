import asyncio
import json
import threading
import websockets
from stt import STT
from llm import LLM
from tts import TTS
from config import WS_HOST, WS_PORT

# ── Стан ─────────────────────────────────────────────────────────────
stt = STT()
llm = LLM()
tts = TTS()

connected_clients: set = set()


# ── WebSocket — шле події у Electron VRM ─────────────────────────────
async def ws_handler(websocket):
    connected_clients.add(websocket)
    print(f"[WS] Electron підключився")
    try:
        async for message in websocket:
            # Electron може слати команди назад (наприклад текстовий ввід)
            data = json.loads(message)
            if data.get("type") == "text_input":
                asyncio.create_task(process_text(data["text"]))
            elif data.get("type") == "clear_history":
                llm.clear_history()
    except websockets.exceptions.ConnectionClosed:
        pass
    finally:
        connected_clients.discard(websocket)
        print(f"[WS] Electron відключився")


async def broadcast(event: dict):
    """Шле JSON подію всім підключеним Electron вікнам."""
    if not connected_clients:
        return
    msg = json.dumps(event, ensure_ascii=False)
    await asyncio.gather(
        *[ws.send(msg) for ws in connected_clients],
        return_exceptions=True,
    )


# ── Обробка одного повороту розмови ──────────────────────────────────
async def process_text(user_text: str):
    if not user_text.strip():
        return

    print(f"\n👤 {user_text}")

    # Показуємо що думаємо
    await broadcast({"type": "state", "value": "thinking"})

    # LLM відповідь
    response_text, emotion = llm.chat(user_text)
    print(f"🤖 {response_text}  [{emotion}]")

    # Надсилаємо текст і емоцію у VRM
    await broadcast({
        "type": "response",
        "text": response_text,
        "emotion": emotion,
    })

    # TTS (в окремому треді щоб не блокувати event loop)
    await broadcast({"type": "state", "value": "speaking"})
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, tts.speak, response_text)

    await broadcast({"type": "state", "value": "idle"})


# ── Мікрофон loop (в окремому треді) ─────────────────────────────────
def mic_loop(loop: asyncio.AbstractEventLoop):
    print("[MIC] Мікрофон активний. Говори!")
    while True:
        text = stt.listen()
        if text:
            asyncio.run_coroutine_threadsafe(process_text(text), loop)


# ── Текстовий ввід з консолі ──────────────────────────────────────────
async def console_input_loop():
    loop = asyncio.get_event_loop()
    print("[CONSOLE] Друкуй повідомлення і натискай Enter (або говори в мік):")
    while True:
        line = await loop.run_in_executor(None, input, "> ")
        if line.strip().lower() in ("/quit", "/exit"):
            print("Вихід...")
            break
        elif line.strip().lower() == "/clear":
            llm.clear_history()
        elif line.strip():
            await process_text(line.strip())


# ── Головна точка входу ───────────────────────────────────────────────
async def main():
    # Запускаємо WebSocket сервер
    ws_server = await websockets.serve(ws_handler, WS_HOST, WS_PORT)
    print(f"[WS] Сервер запущено на ws://{WS_HOST}:{WS_PORT}")

    # Запускаємо мікрофон в окремому треді
    loop = asyncio.get_event_loop()
    mic_thread = threading.Thread(target=mic_loop, args=(loop,), daemon=True)
    mic_thread.start()

    # Консольний ввід (головний таск)
    await console_input_loop()
    ws_server.close()


if __name__ == "__main__":
    asyncio.run(main())
