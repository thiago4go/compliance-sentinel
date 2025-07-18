
import chainlit as cl
from dapr.clients import DaprClient
import json

@cl.on_chat_start
async def start():
    await cl.Message(content="Welcome to the Compliance Sentinel!").send()

@cl.on_message
async def main(message: cl.Message):
    with DaprClient() as d:
        # Publish an event to the "new-request" topic
        req = d.publish_event(
            pubsub_name="messagebus",
            topic_name="new-request",
            data=message.content,
        )
    await cl.Message(content="Your request has been received and is being processed.").send()

@cl.on_event("dapr_event")
async def on_dapr_event(payload):
    await cl.Message(content=f"Received event: {payload}").send()
