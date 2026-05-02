import numpy as np
import sounddevice as sd
import queue
import io
import soundfile as sf
from groq import Groq
from pynput import keyboard
from config import GROQ_API_KEY, MIC_SILENCE_THRESHOLD

SAMPLE_RATE = 16000
CHUNK = 1024
client = Groq(api_key=GROQ_API_KEY)


class STT:
    def __init__(self):
        self.audio_queue = queue.Queue()
        self.recording = False
        print("[STT] Groq Whisper готовий — тримай ПРОБІЛ щоб говорити")

    def listen(self) -> str:
        audio_chunks = []

        def on_press(key):
            if key == keyboard.Key.space:
                if not self.recording:
                    self.recording = True
                    print("[STT] 🔴 Запис...")

        def on_release(key):
            if key == keyboard.Key.space:
                self.recording = False
                return False  # зупиняє listener

        def mic_callback(indata, frames, time, status):
            if self.recording:
                audio_chunks.append(indata.copy())

        with sd.InputStream(
            samplerate=SAMPLE_RATE,
            channels=1,
            dtype="float32",
            blocksize=CHUNK,
            callback=mic_callback,
        ):
            with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
                listener.join()

        if not audio_chunks:
            return ""

        audio = np.concatenate(audio_chunks, axis=0).flatten()

        # фільтр — якщо занадто тихо то пропускаємо
        if np.abs(audio).mean() < 0.01:
            return ""

        return self._transcribe(audio)

    def _transcribe(self, audio: np.ndarray) -> str:
        buf = io.BytesIO()
        sf.write(buf, audio, SAMPLE_RATE, format='WAV', subtype='PCM_16')
        buf.seek(0)
        buf.name = "audio.wav"

        response = client.audio.transcriptions.create(
            file=buf,
            model="whisper-large-v3-turbo",
            response_format="text",
        )

        text = response.strip() if isinstance(response, str) else response.text.strip()
        if text:
            print(f"[STT] {text}")
        return text
