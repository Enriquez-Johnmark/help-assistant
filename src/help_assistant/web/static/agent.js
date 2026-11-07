// The agent's actions on one conversation. The name is remembered on this computer.
"use strict";
const form = document.getElementById("act");
const by = document.getElementById("by");
const reply = document.getElementById("reply");
const error = document.getElementById("error");
const conversation = form.dataset.conversation;
by.value = localStorage.getItem("agent-name") || "";

async function act(action) {
  error.textContent = "";
  if (!by.value.trim()) {
    error.textContent = "Type your name first.";
    return;
  }
  localStorage.setItem("agent-name", by.value.trim());
  const body = { by: by.value };
  if (action === "reply") {
    if (!reply.value.trim()) {
      error.textContent = "Type a reply first.";
      return;
    }
    body.text = reply.value;
  }
  const response = await fetch(`/api/agent/${conversation}/${action}`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!response.ok) {
    const data = await response.json().catch(() => ({}));
    error.textContent = typeof data.detail === "string" ? data.detail : "That didn't work. Please try again.";
    return;
  }
  location.href = action === "reply" ? location.pathname : "/agent";
}

form.addEventListener("submit", (event) => {
  event.preventDefault();
  act("reply");
});
form.querySelectorAll("button[type=button]").forEach((button) =>
  button.addEventListener("click", () => act(button.dataset.action)),
);

// New messages from the customer: reload to show them, unless a reply is being typed.
const notice = document.getElementById("new");
let count = Number(form.dataset.count);
setInterval(async () => {
  const response = await fetch(`/api/conversations/${conversation}/messages`).catch(() => null);
  if (!response?.ok) return;
  const data = await response.json();
  if (data.messages.length === count && data.status === form.dataset.status) return;
  if (!reply.value.trim()) location.reload();
  else notice.hidden = false;
}, 4000);
