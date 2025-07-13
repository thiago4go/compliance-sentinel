from dapr_agents.workflow import WorkflowApp, workflow, task
from dapr.ext.workflow import DaprWorkflowContext
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Simple workflow to test the pattern
@workflow(name="simple_test_workflow")
def simple_test_workflow(ctx: DaprWorkflowContext):
    print("Starting simple workflow...")
    result = yield ctx.call_activity(simple_task)
    print(f"Workflow result: {result}")
    return result

@task(description="Return a simple greeting message")
def simple_task() -> str:
    return "Hello from Dapr Agents Workflow!"

if __name__ == "__main__":
    print("Testing simple workflow pattern...")
    try:
        wfapp = WorkflowApp()
        print("WorkflowApp created successfully")
        
        results = wfapp.run_and_monitor_workflow_sync(simple_test_workflow)
        print(f"Final Results: {results}")
        
    except Exception as e:
        print(f"Error: {e}")
        print("This confirms workflows require Dapr runtime")
