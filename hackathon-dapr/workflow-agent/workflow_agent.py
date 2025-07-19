from dapr.ext.workflow import WorkflowRuntime
from dapr.clients import DaprClient
import json
import time

wfr = WorkflowRuntime()

@wfr.workflow(name="compliance_workflow")
def compliance_workflow(ctx, input: dict):
    # 1. Start the harvesting process
    harvest_task = ctx.call_activity(harvest_insights, input=input)
    yield harvest_task

    # 2. Wait for the results
    results = yield harvest_task

    # 3. Store the results
    store_task = ctx.call_activity(store_results, input=results)
    yield store_task

    # 4. Publish the final event
    with DaprClient() as d:
        d.publish_event(
            pubsub_name="messagebus",
            topic_name="request-complete",
            data=json.dumps(results)
        )

    return "Compliance check complete."

@wfr.activity(name="harvest_insights")
def harvest_insights(ctx, input: dict) -> dict:
    with DaprClient() as d:
        # Invoke the harvester-insights-agent service
        response = d.invoke_method(
            "harvester-insights-agent",
            "harvest-insights",
            data=json.dumps(input)
        )
    return json.loads(response.data)

def harvester_complete_subscriber(event_data):
    with DaprClient() as d:
        # In a real-world scenario, you would use the assessment_id to correlate the
        # results with the correct workflow instance.
        print(f"Received harvester complete event: {event_data}")

@wfr.activity(name="store_results")
def store_results(ctx, input: dict):
    # Logic to store results in PostgreSQL
    print(f"Storing results: {input}")
    pass

def new_request_subscriber(event_data):
    with DaprClient() as d:
        instance_id = d.start_workflow(
            workflow_component="dapr",
            workflow_name="compliance_workflow",
            input=event_data
        )
    print(f"Started workflow: {instance_id}")

if __name__ == "__main__":
    print("Starting Dapr Workflow runtime...")
    wfr.start()
    print("Dapr Workflow runtime started.")
    while True:
        time.sleep(1)

