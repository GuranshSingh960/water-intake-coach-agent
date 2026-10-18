# Water Intake Coach Agent

This project implements a Water Intake Coach Agent for CSE476 Agentic AI and Intelligent Automation. The agent helps a user track daily water consumption and progress toward a daily goal of 2500 ml. It uses two tools: `log_water(ml)`, which records the amount of water consumed, and `get_progress()`, which checks the current intake, daily goal, and remaining amount.

The agent uses a plan-act-observe loop. The model receives the user's request, decides which tool to call, the Python program executes the selected tool, and the result is returned to the model so it can decide whether another tool call is needed or whether to give the final answer. Memory is maintained using the application state in `memory.py` and the conversation history stored by `WaterIntakeAgent`, allowing the agent to use information from earlier turns.

One failure encountered during development was the `externally-managed-environment` error when installing Python packages with `pip` on Arch Linux. The system Python environment prevented global package installation. This was handled by creating a `.venv` virtual environment and installing the required packages inside it. The agent and notebook were then tested successfully.
