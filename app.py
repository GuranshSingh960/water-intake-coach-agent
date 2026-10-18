
from flask import Flask, render_template, request, jsonify
from agent import WaterIntakeAgent
from memory import memory

app = Flask(__name__)

# One agent instance keeps conversation history during the demo.
agent = WaterIntakeAgent()


def get_status():
    consumed = memory["water_consumed"]
    goal = memory["daily_goal"]

    return {
        "consumed": consumed,
        "goal": goal,
        "remaining": max(goal - consumed, 0),
        "percentage": min(round(consumed / goal * 100), 100)
        if goal > 0 else 0
    }


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/api/status", methods=["GET"])
def status():
    return jsonify(get_status())


@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.get_json(silent=True) or {}
    user_message = (data.get("message") or "").strip()

    if not user_message:
        return jsonify({"error": "Please enter a message."}), 400

    try:
        reply = agent.run(user_message, verbose=False)

        # Support agents that return either text or another value.
        if not isinstance(reply, str):
            reply = str(reply)

        return jsonify({
            "reply": reply,
            "status": get_status()
        })

    except Exception as error:
        app.logger.exception("Chat request failed")
        return jsonify({
            "error": (
                "Sorry, I couldn't process that message. "
                "Check your Groq API key and terminal for errors."
            )
        }), 500


@app.route("/api/quick-add", methods=["POST"])
def quick_add():
    global agent

    data = request.get_json(silent=True) or {}
    amount = data.get("amount")

    # Only allow sensible positive whole-number amounts.
    if (
        not isinstance(amount, int)
        or isinstance(amount, bool)
        or amount < 1
        or amount > 5000
    ):
        return jsonify({"error": "Invalid water amount."}), 400

    try:
        reply = agent.run(
            f"I drank {amount} ml of water.",
            verbose=False
        )

        return jsonify({
            "reply": str(reply),
            "status": get_status()
        })

    except Exception:
        app.logger.exception("Quick-add request failed")
        return jsonify({
            "error": "Couldn't log water. Check the server terminal."
        }), 500


@app.route("/api/reset", methods=["POST"])
def reset():
    global agent

    memory["water_consumed"] = 0
    agent = WaterIntakeAgent()

    return jsonify({
        "reply": "Your daily water log has been reset. Let's start fresh!",
        "status": get_status()
    })


if __name__ == "__main__":
    app.run(debug=True)
