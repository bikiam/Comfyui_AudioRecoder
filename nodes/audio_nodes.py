import hashlib
import io
import base64
import ffmpeg
import torch
import torchaudio
import folder_paths  # type: ignore

CATEGORY = "audio"

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
    CATEGORY = CATEGORY

    def process_audio(self, base64_data, record_duration_max):
        audio_data = base64.b64decode(base64_data)
        input_buffer = io.BytesIO(audio_data)

        try:
            output, err = (
                ffmpeg
                .input('pipe:0', format='webm')
                .output('pipe:1', format='wav', acodec='pcm_s16le', ac=2, ar='44100')
                .run(input=input_buffer.read(), capture_stdout=True, capture_stderr=True)
            )
        except ffmpeg.Error as e:
            print("FFmpeg error:", e.stderr.decode())
            raise

        output_buffer = io.BytesIO(output)

        waveform, sample_rate = torchaudio.load(output_buffer)
        if waveform.shape[0] == 1:
            waveform = waveform.repeat(2, 1)

        audio = {"waveform": waveform.unsqueeze(0), "sample_rate": sample_rate}
        return (audio,)

    @classmethod
    def IS_CHANGED(cls, base64_data, record_duration_max):
        m = hashlib.sha256()
        m.update(base64_data.encode())
        return m.hexdigest()
