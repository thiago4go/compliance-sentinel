from fastapi import FastAPI
from dapr.clients import DaprClient

app = FastAPI()

@app.get("/invoke-backend")
async def invoke_backend():
    with DaprClient() as d:
        response = d.invoke_method(
            app_id='backend',
            method_name='hello',
            data=b'',
            http_verb='GET'
        )
        backend_message = response.json().get("message", "No message from backend")
    return {"message": f"Frontend invoked backend: {backend_message}"}

@app.get("/")
async def root():
    return {"message": "Hello from the FastAPI Frontend! Access /invoke-backend to call the backend."}