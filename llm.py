from groq import Groq
from config import GROQ_API_KEY, GROQ_MODEL, SYSTEM_PROMPT
import json
import re

client = Groq(api_key=GROQ_API_KEY)

# Емоції які VRM може відображати через blendshapes
EMOTIONS = ["neutral", "happy", "sad", "angry", "surprised", "relaxed"]

EMOTION_PROMPT = f"""
After your response, on a NEW LINE write exactly: EMOTION:<one of {EMOTIONS}>
Example:
こんにちは！嬉しいな～
EMOTION:happy
"""


class LLM:
    def __init__(self):
        self.history: list[dict] = []
        self.max_history = 20  # скільки повідомлень тримаємо в пам'яті
        print("[LLM] Groq клієнт готовий")

    def chat(self, user_text: str) -> tuple[str, str]:
        """
        Повертає (відповідь, емоція).
        """
        self.history.append({"role": "user", "content": user_text})

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT + EMOTION_PROMPT},
            *self._trim_history(),
        ]

        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=messages,
            max_tokens=300,
            temperature=0.8,
        )

        raw = response.choices[0].message.content.strip()
        text, emotion = self._parse_emotion(raw)

        self.history.append({"role": "assistant", "content": text})
        self._trim_history_inplace()

        print(f"[LLM] {text}  [{emotion}]")
        return text, emotion

    def _parse_emotion(self, raw: str) -> tuple[str, str]:
        """Витягує EMOTION:<tag> з кінця відповіді."""
        match = re.search(r"EMOTION:(\w+)", raw)
        if match:
            emotion = match.group(1).lower()
            if emotion not in EMOTIONS:
                emotion = "neutral"
            text = raw[: match.start()].strip()
        else:
            text = raw
            emotion = "neutral"
        return text, emotion

    def _trim_history(self) -> list[dict]:
        return self.history[-self.max_history:]

    def _trim_history_inplace(self):
        if len(self.history) > self.max_history:
            self.history = self.history[-self.max_history:]

    def clear_history(self):
        self.history = []
        print("[LLM] Пам'ять очищена")
