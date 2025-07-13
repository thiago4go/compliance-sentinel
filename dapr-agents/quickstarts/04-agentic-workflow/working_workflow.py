from dapr_agents.workflow import WorkflowApp, workflow, task
from dapr.ext.workflow import DaprWorkflowContext
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Define workflow using the pattern that worked in Challenge 1
@workflow(name="lotr_character_workflow")
def lotr_character_workflow(ctx: DaprWorkflowContext, topic: str):
    # Step 1: Get a character
    character = yield ctx.call_activity(get_character, input=topic)
    
    # Step 2: Get a famous line from that character
    famous_line = yield ctx.call_activity(get_famous_line, input=character)
    
    return f"Character: {character}\nFamous Line: {famous_line}"

@task(description="Pick a random character from The Lord of the Rings and respond with just the character's name")
def get_character(topic: str) -> str:
    pass  # LLM will implement this automatically

@task(description="What is a famous line spoken by {character} in The Lord of the Rings?")
def get_famous_line(character: str) -> str:
    pass  # LLM will implement this automatically

if __name__ == "__main__":
    print("🚀 Starting LOTR Character Workflow...")
    
    wfapp = WorkflowApp()
    
    # Run the workflow
    results = wfapp.run_and_monitor_workflow_sync(
        lotr_character_workflow, 
        input="Lord of the Rings"
    )
    
    print("✅ Workflow Results:")
    print(results)
