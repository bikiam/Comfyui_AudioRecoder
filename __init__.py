from .nodes.audio_nodes import BikiAudioRecorderNode

NODE_CLASS_MAPPINGS = {
  "BikiAudioRecorderNode": BikiAudioRecorderNode
}
NODE_DISPLAY_NAME_MAPPINGS = {
  "BikiAudioRecorderNode": "AUDIO Recorder"
}
WEB_DIRECTORY = "./web"

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS", "WEB_DIRECTORY"]
