#!/bin/bash
# Activate the Python virtual environment and set up paths
source venv/bin/activate
export PATH="$HOME/.local/bin:$PATH"
echo "✅ Virtual environment activated!"
echo "✅ Python packages available: dapr, dapr-agents, flask-dapr, etc."
echo "✅ Tools available: q, qchat, dapr, diagrid, gemini"
echo ""
echo "To use this environment in future sessions, run: source activate_env.sh"
