import asyncio
import edge_tts
import sounddevice as sd
import soundfile as sf
import io
import numpy as np
import re
import threading

# Голоси
VOICE_JA = "ja-JP-NanamiNeural"   # японська — аніме дівчина
VOICE_UK = "uk-UA-PolinaNeural"   # українська
VOICE_EN = "en-US-AvaNeural"      # англійська

RATE = "+0%"  # швидкість, +10% = трохи швидше


class TTS:
    def __init__(self):
        print("[TTS] Edge TTS готовий (Nanami / Polina / Ava)")

    def speak(self, text: str):
        try:
            asyncio.run(self._speak_async(text))
        except Exception as e:
            print(f"[TTS] помилка: {e}")

    def speak_async(self, text: str):
        t = threading.Thread(target=self.speak, args=(text,), daemon=True)
        t.start()
        return t

    async def _speak_async(self, text: str):
        segments = self._split_by_language(text)
        for seg_text, lang in segments:
            seg_text = seg_text.strip()
            if not seg_text:
                continue
            if lang == "ja":
                voice = VOICE_JA
            elif lang == "uk":
                voice = VOICE_UK
            else:
                voice = VOICE_EN
            await self._play_segment(seg_text, voice)

    async def _play_segment(self, text: str, voice: str):
        try:
            communicate = edge_tts.Communicate(text, voice, rate=RATE)
            audio_data = b""
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    audio_data += chunk["data"]
            if audio_data:
                audio, sr = sf.read(io.BytesIO(audio_data), dtype="float32")
                sd.play(audio, samplerate=sr)
                sd.wait()
        except Exception as e:
            print(f"[TTS] помилка сегменту '{text[:30]}': {e}")

    def _split_by_language(self, text: str) -> list[tuple[str, str]]:
        # Патерни для визначення мови
        PATTERN = re.compile(
            r"(?P<ja>[\u3040-\u309f\u30a0-\u30ff\u4e00-\u9fff][^\u0000-\u007f\u0400-\u04ff]*)"
            r"|(?P<uk>[\u0400-\u04ff][^a-zA-Z\u3040-\u30ff\u4e00-\u9fff]*)"
            r"|(?P<en>[a-zA-Z][^\u0400-\u04ff\u3040-\u30ff\u4e00-\u9fff]*)"
        )

        segments = []
        last = 0

        for m in PATTERN.finditer(text):
            # пропускаємо пробіли між сегментами
            if m.start() > last:
                gap = text[last:m.start()].strip()
                if gap and segments:
                    # додаємо до попереднього сегменту
                    segments[-1] = (segments[-1][0] + " " + gap, segments[-1][1])

            if m.group("ja"):
                lang = "ja"
            elif m.group("uk"):
                lang = "uk"
            else:
                lang = "en"

            seg = m.group().strip()
            if not seg:
                last = m.end()
                continue

            # Мержимо з попереднім якщо та сама мова
            if segments and segments[-1][1] == lang:
                segments[-1] = (segments[-1][0] + " " + seg, lang)
            else:
                segments.append((seg, lang))

            last = m.end()

        return segments if segments else [(text, "en")]

    def stop(self):
        sd.stop()