import re
import io
import base64
import ffmpeg
import torchaudio
from pathlib import Path
import hashlib

# point this at your ComfyUI input folder
INPUT_DIR = Path("/content/ComfyUI/input")

class BikiAudioRecorderNode:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "base64_data":      ("STRING",  {"multiline": False}),
                "record_duration_max": ("INT", {
                    "default": 10, "min": 1, "max": 600, "step": 1
                }),
                "save_audio":       ("BOOLEAN", {"default": False}),
                "file_prefix":      ("STRING",  {"default": "record", "multiline": False}),
            }
        }

    RETURN_TYPES = ("AUDIO",)
    RETURN_NAMES = ("AUDIO",)
    FUNCTION = "process_audio"
    CATEGORY = "audio"

    def process_audio(self, base64_data, record_duration_max, save_audio, file_prefix):
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

        # 2) Optionally save to disk
        if save_audio:
            # find existing files with this prefix
            existing = list(INPUT_DIR.glob(f"{file_prefix}*.wav"))
            nums = []
            for p in existing:
                m = re.match(rf'^{re.escape(file_prefix)}(\d+)\.wav$', p.name)
                if m:
                    nums.append(int(m.group(1)))
            next_n = max(nums) + 1 if nums else 1

            out_path = INPUT_DIR / f"{file_prefix}{next_n}.wav"
            out_path.write_bytes(wav_bytes)
            print(f"[BikiAudioRecorderNode] saved WAV to {out_path}")

        # 3) Load into torch
        buffer = io.BytesIO(wav_bytes)
        waveform, sr = torchaudio.load(buffer)
        if waveform.shape[0] == 1:
            waveform = waveform.repeat(2, 1)

        audio = {"waveform": waveform.unsqueeze(0), "sample_rate": sr}
        return (audio,)

    @classmethod
    def IS_CHANGED(cls, base64_data, record_duration_max, save_audio, file_prefix):
        m = hashlib.sha256()
        m.update(base64_data.encode())
        # also include save_audio & prefix so changing them re-triggers the node
        m.update(str(save_audio).encode())
        m.update(file_prefix.encode())
        return m.hexdigest()
