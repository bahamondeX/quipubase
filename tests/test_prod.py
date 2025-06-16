from openai import OpenAI

ai = OpenAI(base_url="https://quipubase-1004773754699.southamerica-west1.run.app/v1", api_key="")

def test_chat_completion():
	response = ai.chat.completions.create(
		model="gpt-4",
		messages=[
			{"role": "system", "content": "You are a helpful assistant."},
			{"role": "user", "content": "Hello! How can you assist me today?"}
		]
	)
	content = response.choices[0].message.content
	assert content is not None
	assert isinstance(content, str)
	assert len(content) > 0
	
def test_embedding():
	response = ai.embeddings.create(
		model="poly-sage",
		input=["Hello world", "This is a test"]
	)
	assert response.data is not None
	assert isinstance(response.data, list)
	assert len(response.data) == 2
	assert isinstance(response.data[0].embedding, list)
	assert len(response.data[0].embedding) > 0
	