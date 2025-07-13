import asyncio
from dapr_agents import Agent, tool
from dapr_agents.types import UserMessage
from pydantic import BaseModel, Field
from dotenv import load_dotenv
import json
import time

load_dotenv()

# Advanced Tool Patterns Demo

# 1. Tool with Complex Data Structures
class TaskSchema(BaseModel):
    title: str = Field(description="Task title")
    priority: str = Field(description="Priority level: high, medium, low")
    due_date: str = Field(description="Due date in YYYY-MM-DD format")

@tool(args_model=TaskSchema)
def create_task(title: str, priority: str, due_date: str) -> str:
    """Create a new task with specified details."""
    task = {
        "id": f"task_{int(time.time())}",
        "title": title,
        "priority": priority,
        "due_date": due_date,
        "status": "pending",
        "created_at": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    return f"Task created: {json.dumps(task, indent=2)}"

# 2. Tool with Error Handling
class CalculationSchema(BaseModel):
    expression: str = Field(description="Mathematical expression to evaluate")

@tool(args_model=CalculationSchema)
def calculate(expression: str) -> str:
    """Safely evaluate mathematical expressions."""
    try:
        # Only allow basic math operations for security
        allowed_chars = set('0123456789+-*/().')
        if not all(c in allowed_chars or c.isspace() for c in expression):
            return f"Error: Invalid characters in expression '{expression}'"
        
        result = eval(expression)
        return f"Result: {expression} = {result}"
    except Exception as e:
        return f"Error calculating '{expression}': {str(e)}"

# 3. Tool with Conditional Logic
class WeatherActionSchema(BaseModel):
    location: str = Field(description="Location to check weather")
    action_type: str = Field(description="Type of action: check, alert, recommend")

@tool(args_model=WeatherActionSchema)
def weather_action(location: str, action_type: str) -> str:
    """Perform weather-related actions with conditional logic."""
    import random
    
    # Simulate weather data
    temp = random.randint(50, 90)
    conditions = random.choice(["sunny", "cloudy", "rainy", "snowy"])
    
    if action_type == "check":
        return f"{location}: {temp}°F, {conditions}"
    elif action_type == "alert":
        if temp > 85:
            return f"🔥 Heat Alert for {location}: {temp}°F - Stay hydrated!"
        elif temp < 60:
            return f"🧥 Cold Alert for {location}: {temp}°F - Dress warmly!"
        else:
            return f"✅ Pleasant weather in {location}: {temp}°F"
    elif action_type == "recommend":
        if conditions == "rainy":
            return f"☔ Recommendation for {location}: Bring an umbrella!"
        elif conditions == "sunny":
            return f"☀️ Recommendation for {location}: Great day for outdoor activities!"
        else:
            return f"🌤️ Recommendation for {location}: Perfect weather for any activity!"
    else:
        return f"Unknown action type: {action_type}"

# 4. Tool with Data Persistence Simulation
class NoteSchema(BaseModel):
    content: str = Field(description="Note content to save")
    category: str = Field(description="Note category: personal, work, idea")

# Simple in-memory storage for demo
notes_storage = []

@tool(args_model=NoteSchema)
def save_note(content: str, category: str) -> str:
    """Save a note with categorization."""
    note = {
        "id": len(notes_storage) + 1,
        "content": content,
        "category": category,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    notes_storage.append(note)
    return f"Note saved (ID: {note['id']}): {content} [Category: {category}]"

@tool
def list_notes() -> str:
    """List all saved notes."""
    if not notes_storage:
        return "No notes found."
    
    result = "📝 Saved Notes:\n"
    for note in notes_storage:
        result += f"  {note['id']}. [{note['category']}] {note['content']} ({note['timestamp']})\n"
    return result

# Create Advanced Agent
advanced_agent = Agent(
    name="AdvancedAssistant",
    role="Multi-Purpose AI Assistant",
    goal="Help users with complex tasks using advanced tool patterns.",
    instructions=[
        "Use appropriate tools based on user requests",
        "Handle errors gracefully and provide helpful feedback",
        "Combine multiple tools when necessary to complete complex tasks",
        "Always explain what actions you're taking"
    ],
    tools=[create_task, calculate, weather_action, save_note, list_notes]
)

async def demo_advanced_patterns():
    """Demonstrate advanced tool patterns."""
    
    print("🚀 Advanced Tool Patterns Demo")
    print("=" * 50)
    
    # Test 1: Complex data structure
    print("\n1. Testing Complex Task Creation...")
    await advanced_agent.run("Create a high priority task to 'Review Q3 budget' due on 2024-12-31")
    
    # Test 2: Error handling
    print("\n2. Testing Error Handling...")
    await advanced_agent.run("Calculate 10 + 5 * 2 and also try to calculate something invalid like 'hello + world'")
    
    # Test 3: Conditional logic
    print("\n3. Testing Conditional Logic...")
    await advanced_agent.run("Check the weather in Miami and give me an alert if needed")
    
    # Test 4: Data persistence
    print("\n4. Testing Data Persistence...")
    await advanced_agent.run("Save a work note: 'Meeting with client at 3pm tomorrow' and then list all my notes")
    
    # Test 5: Tool chaining
    print("\n5. Testing Tool Chaining...")
    await advanced_agent.run("Calculate 25 * 4, then save the result as a personal note, and finally list all notes")

if __name__ == "__main__":
    asyncio.run(demo_advanced_patterns())
