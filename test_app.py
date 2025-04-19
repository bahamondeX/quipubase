from fastapi import FastAPI, Depends
from pydantic import BaseModel
import uvicorn

app = FastAPI(title="Test App", description="Test application")

class Item(BaseModel):
    name: str
    description: str = None

@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.get("/items/")
def read_items():
    return [{"item_id": 1}, {"item_id": 2}]

@app.post("/items/")
def create_item(item: Item):
    return item

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)