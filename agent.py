from __future__ import annotations

import json
import os
from typing import Any, Callable

from dotenv import load_dotenv
from openai import OpenAI

from tools import log_water, get_progress


# ============================================================
# LOAD ENVIRONMENT
# ============================================================

load_dotenv()


# ============================================================
# MODEL CLIENT
# ============================================================

client = OpenAI(
    base_url="https://api.groq.com/openai/v1",
    api_key=os.getenv("GROQ_API_KEY"),
)

MODEL = "openai/gpt-oss-20b"


# ============================================================
# TOOL REGISTRY
# ============================================================

REGISTRY: dict[str, Callable[..., Any]] = {
    "log_water": log_water,
    "get_progress": get_progress,
}


# ============================================================
# TOOL SCHEMAS
# ============================================================

TOOL_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "log_water",
            "description": (
                "Record the amount of water the user drank. "
                "Use this whenever the user reports drinking "
                "a specific amount of water."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "ml": {
                        "type": "integer",
                        "description": (
                            "Amount of water consumed in "
                            "milliliters."
                        ),
                    }
                },
                "required": ["ml"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_progress",
            "description": (
                "Check the user's current water intake, "
                "daily goal, and remaining amount."
            ),
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
    },
]


# ============================================================
# SYSTEM PROMPT
# ============================================================

SYSTEM = """
You are a Water Intake Coach Agent.

Your job is to help the user track their daily water intake.

You have two tools:

1. log_water(ml)
   Records the amount of water consumed.

2. get_progress()
   Returns:
   - water consumed today
   - daily water goal
   - water remaining

IMPORTANT RULES:

1. If the user says they drank a specific amount of water,
   use log_water.

2. After logging water, use get_progress to check the
   updated progress.

3. If the user asks about their progress, intake, remaining
   water, or daily goal, use get_progress.

4. The user can use natural language.

   Examples:
   - "I drank 500 ml"
   - "I had half a litre"
   - "I just drank 750 millilitres"
   - "I had another 250 ml"
   - "How much have I had?"
   - "How much more do I need?"
   - "Am I close to my goal?"

5. Convert clearly stated amounts into milliliters.

   Examples:
   - 1 litre = 1000 ml
   - half a litre = 500 ml
   - 0.75 litre = 750 ml

6. If the amount is ambiguous, do NOT invent a value.
   Ask the user for clarification.

   For example:
   "I drank a glass of water"
   should not automatically become a specific
   number of milliliters.

7. Never guess the user's current intake.

8. Always use tool results when answering questions
   about the user's progress.

9. Keep final answers concise and friendly.

10. You can call more than one tool when necessary.
"""


# ============================================================
# AGENT CLASS
# ============================================================

class WaterIntakeAgent:

    def __init__(self):

        # ----------------------------------------------------
        # Conversation memory
        # ----------------------------------------------------

        self.messages: list[dict[str, Any]] = [
            {
                "role": "system",
                "content": SYSTEM,
            }
        ]

    # ========================================================
    # RUN AGENT
    # ========================================================

    def run(
        self,
        user_input: str,
        max_steps: int = 6,
        verbose: bool = True,
    ) -> str:

        # ----------------------------------------------------
        # Add user's message to conversation memory
        # ----------------------------------------------------

        self.messages.append(
            {
                "role": "user",
                "content": user_input,
            }
        )

        # ----------------------------------------------------
        # PLAN → ACT → OBSERVE LOOP
        # ----------------------------------------------------

        for step in range(1, max_steps + 1):

            # =================================================
            # THINK / PLAN
            # =================================================

            response = client.chat.completions.create(
                model=MODEL,
                messages=self.messages,
                tools=TOOL_SCHEMA,
            )

            message = response.choices[0].message

            # Save model response to memory
            self.messages.append(
                message.model_dump(exclude_none=True)
            )

            # =================================================
            # IF NO TOOL CALL → FINAL ANSWER
            # =================================================

            if not message.tool_calls:

                if verbose:
                    print(
                        f"[step {step}] final answer"
                    )

                return message.content or ""

            # =================================================
            # ACT → EXECUTE TOOLS
            # =================================================

            for tool_call in message.tool_calls:

                tool_name = tool_call.function.name

                try:
                    arguments = json.loads(
                        tool_call.function.arguments or "{}"
                    )

                except json.JSONDecodeError:

                    result = {
                        "error": "Invalid tool arguments."
                    }

                    arguments = {}

                else:

                    # -----------------------------------------
                    # Find and execute the requested tool
                    # -----------------------------------------

                    if tool_name in REGISTRY:

                        try:

                            result = REGISTRY[
                                tool_name
                            ](**arguments)

                        except Exception as error:

                            result = {
                                "error": str(error)
                            }

                    else:

                        result = {
                            "error": (
                                f"Unknown tool: {tool_name}"
                            )
                        }

                # =================================================
                # SHOW AGENT TRACE
                # =================================================

                if verbose:

                    print(
                        f"[step {step}] "
                        f"{tool_name}({arguments}) "
                        f"-> {result}"
                    )

                # =================================================
                # OBSERVE → RETURN TOOL RESULT TO MODEL
                # =================================================

                self.messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": json.dumps(result),
                    }
                )

        # =====================================================
        # SAFETY LIMIT
        # =====================================================

        return (
            "I couldn't complete the request within "
            f"{max_steps} steps."
        )


# ============================================================
# INTERACTIVE TERMINAL
# ============================================================

def main():

    print()
    print("=" * 50)
    print("          WATER INTAKE COACH AGENT")
    print("=" * 50)
    print()
    print("You can talk naturally to the agent.")
    print()
    print("Examples:")
    print("  I drank 500 ml")
    print("  I had half a litre")
    print("  I drank another 750 ml")
    print("  How much have I consumed?")
    print("  How much more do I need?")
    print("  Am I close to my goal?")
    print()
    print("Type 'exit' to stop.")
    print()
    print("-" * 50)

    # --------------------------------------------------------
    # Create ONE agent
    # --------------------------------------------------------
    # Keeping the same object means conversation memory
    # remains available across turns.
    # --------------------------------------------------------

    agent = WaterIntakeAgent()

    while True:

        try:

            user_input = input("\nYou: ").strip()

        except (KeyboardInterrupt, EOFError):

            print("\n\nAgent: Goodbye!")
            break

        # ----------------------------------------------------
        # Empty input
        # ----------------------------------------------------

        if not user_input:
            continue

        # ----------------------------------------------------
        # Exit
        # ----------------------------------------------------

        if user_input.lower() in {
            "exit",
            "quit",
            "bye",
        }:

            print("\nAgent: Goodbye!")
            break

        # ----------------------------------------------------
        # Run agent
        # ----------------------------------------------------

        print()

        answer = agent.run(
            user_input,
            verbose=True,
        )

        print()
        print("Agent:", answer)


# ============================================================
# PROGRAM ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()