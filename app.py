from quipubase.store import VectorStore
from openai import OpenAI
from openai.types.chat.chat_completion_user_message_param import (
    ChatCompletionUserMessageParam,
)

from quipubase.store.typedefs import Embedding

vs = VectorStore(namespace="ns", model="poly-sage")
ai = OpenAI()


def generate_text(i: int):
    for i in range(i):
        response = ai.chat.completions.create(
            messages=[
                {"role": "user", "content": "Escribe un haiku para esta mujer."},
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": "https://scontent.flim24-1.fna.fbcdn.net/v/t39.30808-6/496938532_1493812955448997_6569092126336394722_n.jpg?_nc_cat=1&ccb=1-7&_nc_sid=127cfc&_nc_ohc=m4RQMtXi-0MQ7kNvwGnil74&_nc_oc=AdnH5EHZUlery6Kd2FUPPw0AG-xcj5o6tHOs-IzrdOyv7UeTQCwhj_V0Crdg68a32qM&_nc_zt=23&_nc_ht=scontent.flim24-1.fna&_nc_gid=wavJJmnw_0ui-EirMf2OmA&oh=00_AfKJgPE-tn9bjJzyrCj3-BxsRkSI1aWsE8x8qb4kJFeh-A&oe=682F75F1",
                                "detail": "high",
                            },
                        }
                    ],
                },
            ],
            model="meta-llama/llama-4-maverick-17b-128e-instruct",
            temperature=2,
        )
        content = response.choices[0].message.content
        assert content is not None
        print(content)
        yield content


texts = list(generate_text(10))

r = vs.upsert([Embedding(content=c, embedding=vs.embed(c)) for c in texts])
print(r)
q = vs.query(vs.embed("I love you").tolist(), 3)
print(q)
