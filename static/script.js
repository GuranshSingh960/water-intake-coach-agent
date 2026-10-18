
const chatMessages = document.getElementById("chatMessages");
const chatForm = document.getElementById("chatForm");
const messageInput = document.getElementById("messageInput");
const sendBtn = document.getElementById("sendBtn");
const resetBtn = document.getElementById("resetBtn");
const toast = document.getElementById("toast");

let busy = false;
let toastTimer;

function formatTime() {
    return new Intl.DateTimeFormat([], {
        hour: "numeric",
        minute: "2-digit"
    }).format(new Date());
}

function formatMl(value) {
    return `${Number(value).toLocaleString()} ml`;
}

function showToast(message) {
    toast.textContent = message;
    toast.classList.add("show");

    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => {
        toast.classList.remove("show");
    }, 2800);
}

function addMessage(text, sender) {
    const row = document.createElement("div");
    row.className = `message ${sender}-message`;

    const avatar = document.createElement("div");
    avatar.className = "message-avatar";
    avatar.textContent = sender === "user" ? "👤" : "💧";

    const bubble = document.createElement("div");
    bubble.className = "bubble";

    const author = document.createElement("div");
    author.className = "message-author";
    author.textContent = sender === "user" ? "You" : "Water Coach";

    // textContent prevents model responses from being interpreted as HTML.
    const content = document.createElement("div");
    content.textContent = text;
    content.style.whiteSpace = "pre-wrap";

    const time = document.createElement("div");
    time.className = "message-time";
    time.textContent = formatTime();

    bubble.append(author, content, time);
    row.append(avatar, bubble);
    chatMessages.appendChild(row);

    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function setBusy(value) {
    busy = value;
    sendBtn.disabled = value;
    messageInput.disabled = value;

    document.querySelectorAll(".quick-btn, .suggestion").forEach(button => {
        button.disabled = value;
    });

    resetBtn.disabled = value;
    sendBtn.textContent = value ? "…" : "➤";
}

function updateStatus(status) {
    if (!status) return;

    const consumed = Number(status.consumed) || 0;
    const goal = Number(status.goal) || 0;
    const remaining = Math.max(Number(status.remaining) || 0, 0);
    const percentage = Math.max(
        0,
        Math.min(Number(status.percentage) || 0, 100)
    );

    document.getElementById("consumedRing").textContent = formatMl(consumed);
    document.getElementById("goalRing").textContent = goal.toLocaleString();

    document.getElementById("consumedStat").textContent = formatMl(consumed);
    document.getElementById("goalStat").textContent = formatMl(goal);
    document.getElementById("remainingStat").textContent = formatMl(remaining);

    document.getElementById("progressPercent").textContent =
        `${percentage}% completed`;

    document.getElementById("goalMessage").textContent =
        percentage >= 100 ? "Goal reached! 🎉" : "Keep it going!";

    document.getElementById("progressBar").style.width = `${percentage}%`;
    document.getElementById("progressRing").style.setProperty(
        "--progress",
        `${percentage}%`
    );
}

async function apiRequest(url, payload = {}) {
    const response = await fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
    });

    const data = await response.json().catch(() => ({}));

    if (!response.ok) {
        throw new Error(data.error || "Something went wrong.");
    }

    return data;
}

async function sendMessage(message) {
    const text = message.trim();

    if (!text || busy) return;

    addMessage(text, "user");
    messageInput.value = "";
    messageInput.style.height = "auto";
    setBusy(true);

    const typing = document.createElement("div");
    typing.className = "typing";
    typing.textContent = "Water Coach is thinking…";
    chatMessages.appendChild(typing);
    chatMessages.scrollTop = chatMessages.scrollHeight;

    try {
        const data = await apiRequest("/api/chat", { message: text });

        addMessage(data.reply || "I couldn't generate a response.", "bot");
        updateStatus(data.status);
    } catch (error) {
        addMessage(
            `Sorry, I couldn't process that request. ${error.message}`,
            "bot"
        );
        showToast("Message failed. Check your connection and server.");
    } finally {
        typing.remove();
        setBusy(false);
        messageInput.focus();
    }
}

chatForm.addEventListener("submit", event => {
    event.preventDefault();
    sendMessage(messageInput.value);
});

messageInput.addEventListener("keydown", event => {
    if (event.key === "Enter" && !event.shiftKey) {
        event.preventDefault();
        chatForm.requestSubmit();
    }
});

messageInput.addEventListener("input", () => {
    messageInput.style.height = "auto";
    messageInput.style.height =
        `${Math.min(messageInput.scrollHeight, 120)}px`;
});

document.querySelectorAll(".suggestion").forEach(button => {
    button.addEventListener("click", () => {
        sendMessage(button.dataset.message);
    });
});

document.querySelectorAll(".quick-btn[data-amount]").forEach(button => {
    button.addEventListener("click", async () => {
        if (busy) return;

        const amount = Number(button.dataset.amount);

        addMessage(`I drank ${formatMl(amount)} of water.`, "user");
        setBusy(true);

        const typing = document.createElement("div");
        typing.className = "typing";
        typing.textContent = "Logging your water…";
        chatMessages.appendChild(typing);
        chatMessages.scrollTop = chatMessages.scrollHeight;

        try {
            const data = await apiRequest("/api/quick-add", { amount });
            addMessage(data.reply, "bot");
            updateStatus(data.status);
        } catch (error) {
            addMessage(`Couldn't log your water. ${error.message}`, "bot");
            showToast("Water could not be logged.");
        } finally {
            typing.remove();
            setBusy(false);
        }
    });
});

document.getElementById("checkProgressBtn").addEventListener("click", () => {
    sendMessage("How much water have I consumed today, and how much remains?");
});

resetBtn.addEventListener("click", async () => {
    if (busy) return;

    const confirmed = window.confirm(
        "Reset today's water intake to zero? This cannot be undone."
    );

    if (!confirmed) return;

    setBusy(true);

    try {
        const data = await apiRequest("/api/reset");

        chatMessages.replaceChildren();
        addMessage(data.reply, "bot");
        updateStatus(data.status);
        showToast("Daily water log reset.");
    } catch (error) {
        showToast(error.message);
    } finally {
        setBusy(false);
    }
});

async function loadInitialStatus() {
    try {
        const response = await fetch("/api/status");
        if (!response.ok) throw new Error("Unable to load progress.");

        const status = await response.json();
        updateStatus(status);
    } catch (error) {
        showToast("Could not load your water progress.");
    }
}

loadInitialStatus();
