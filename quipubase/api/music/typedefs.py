from google.genai import types
from pydantic import BaseModel
	
class MusicGenerationParams(BaseModel):
	model_config = {"extra":"ignore"}
	prompts:list[types.WeightedPrompt]
	config:types.LiveMusicGenerationConfig
	
	