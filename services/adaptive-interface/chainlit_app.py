import chainlit as cl
from dapr.clients import DaprClient

@cl.on_chat_start
async def start():
    await cl.Message(content="Hello! I am your Chainlit Dapr Agent. Ask me anything!").send()

@cl.on_message
async def main(message: cl.Message):
    # Invoke the backend service via Dapr
    with DaprClient() as d:
        response = d.invoke_method(
            app_id='backend',
            method_name='hello',
            data=b'',
            http_verb='GET'
        )
        backend_message = response.json().get("message", "No message from backend")

    await cl.Message(
        content=f"You said: {message.content}\nBackend says: {backend_message}",
    ).send()
