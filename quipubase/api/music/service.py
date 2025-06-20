import os
from google.genai import Client
from .typedefs import MusicGenerationParams

client = Client(api_key=os.environ["OPENAI_API_KEY"],http_options={'api_version': 'v1alpha'})

class MusicGenerationService:
    async def run(self, *, data: MusicGenerationParams):
        print("MusicGenerationService.run called.") # Added debug print
        try:
            async with client.aio.live.music.connect(model='models/lyria-realtime-exp') as session:
                print("WebSocket connection established.") # Added debug print
                if len(data.prompts):
                    await session.set_weighted_prompts(prompts=data.prompts)
                    print(f"Weighted prompts set: {len(data.prompts)} prompts.") # Added debug print
                
                await session.set_music_generation_config(config=data.config)
                print("Music generation config set.") # Added debug print
                
                await session.play()
                print("Play command sent. Awaiting audio stream...") # Added debug print

                audio_chunk_count = 0
                async for message in session.receive():
                    print(f"Received message type: {type(message)}, content: {message.server_content}") # Added debug print
                    
                    if message.server_content and message.server_content.audio_chunks:
                        audio_data = message.server_content.audio_chunks[0].data
                        if audio_data:
                            yield audio_data
                            audio_chunk_count += 1
                            print(f"Yielded audio chunk {audio_chunk_count}, length: {len(audio_data)} bytes.") # Added debug print
                        else:
                            print("Received audio chunk with empty data.") # Added debug print
                    else:
                        print("Received message with no audio chunks or server_content.") # Added debug print

                print(f"Streaming finished. Total audio chunks yielded: {audio_chunk_count}.") # Added debug print

        except Exception as e:
            print(f"An error occurred in MusicGenerationService.run: {e}") # Added error logging
            # Re-raise the exception if you want FastAPI to handle it and return a 500
            raise