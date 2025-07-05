import re
import io
import base64
import ffmpeg
import torchaudio
from pathlib import Path
# assume INPUT_DIR has been defined above
INPUT_DIR = Path("/content/ComfyUI/input")
class BikiAudioRecorderNode:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "base64_data": ("STRING", {"multiline": False}),
                "record_duration_max": ("INT", {
                    "default": 10,
                    "min": 1,
                    "max": 600,
                    "step": 1
                }),
            }
        }

    RETURN_TYPES = ("AUDIO",)
    RETURN_NAMES = ("AUDIO",)
    FUNCTION = "process_audio"
    CATEGORY = "audio"

    def process_audio(self, base64_data, record_duration_max):
        # 1) Decode & convert via FFmpeg
        raw = base64.b64decode(base64_data)
        try:
            wav_bytes, _ = (
                ffmpeg
                .input('pipe:0', format='webm')
                .output('pipe:1', format='wav', acodec='pcm_s16le', ac=2, ar='44100')
                .run(input=raw, capture_stdout=True, capture_stderr=True)
            )
        except ffmpeg.Error as e:
            print("FFmpeg error:", e.stderr.decode())
            raise

        # 2) Determine next recordN.wav filename
        existing = list(INPUT_DIR.glob("record*.wav"))
        nums = [int(p.stem.replace("record", "")) for p in existing if p.stem.startswith("record") and p.stem.replace("record","").isdigit()]
        next_n = max(nums) + 1 if nums else 1
        out_path = INPUT_DIR / f"record{next_n}.wav"

        # 3) Save to disk
        out_path.write_bytes(wav_bytes)
        print(f"[BikiAudioRecorderNode] saved WAV to {out_path}")

        # 4) Load into torch
        buffer = io.BytesIO(wav_bytes)
        waveform, sr = torchaudio.load(buffer)
        if waveform.shape[0] == 1:
            waveform = waveform.repeat(2, 1)

        audio = {"waveform": waveform.unsqueeze(0), "sample_rate": sr}
        return (audio,)

    @classmethod
    def IS_CHANGED(cls, base64_data, record_duration_max):
        import hashlib
        m = hashlib.sha256()
        m.update(base64_data.encode())
        return m.hexdigest()
