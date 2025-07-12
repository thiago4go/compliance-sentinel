from fastapi import FastAPI
from dapr.ext.fastapi import DaprApp

app = FastAPI()
dapr_app = DaprApp(app)

@dapr_app.subscribe(pubsub="pubsub", topic="greetings")
def handle_greeting(data: dict):
    print(f"Received greeting: {data}")

@app.get("/hello")
def hello():
    return {"message": "Hello from the backend!"}