// The customer's chat: one conversation per browser tab, checked every few
// seconds so an agent's replies appear. Text is shown as text, never as HTML.
"use strict";
const list = document.getElementById("messages");
const statusLine = document.getElementById("status");
const form = document.getElementById("ask");
const box = document.getElementById("text");
const STATUS = {
  waiting: "We've passed your chat to a person. They'll reply here.",
  with_agent: "You're chatting with a person from our support team.",
  closed: "This chat is closed. Start a new chat if you need more help.",
};
const NAMES = { customer: "You", assistant: "Assistant", agent: "Support" };
let conversation = sessionStorage.getItem("conversation");
let shown = "";

async function call(method, url, body) {
  const response = await fetch(url, {
    method,
    headers: body ? { "content-type": "application/json" } : {},
    body: body ? JSON.stringify(body) : undefined,
  });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    const error = new Error(typeof data.detail === "string" ? data.detail : "Please try again.");
    error.status = response.status;
    throw error;
  }
  return data;
}

async function start() {
  conversation = (await call("POST", "/api/conversations")).id;
  sessionStorage.setItem("conversation", conversation);
  shown = "";
  list.replaceChildren();
}

function render(data) {
  const key = JSON.stringify(data);
  if (key === shown) return;
  shown = key;
  list.replaceChildren(
    ...data.messages.map((m) => {
      const item = document.createElement("li");
      item.className = m.sender;
      const who = document.createElement("b");
      who.textContent = NAMES[m.sender];
      const text = document.createElement("p");
      text.textContent = m.text;
      item.append(who, text);
      if (m.cited.length) {
        const from = document.createElement("p");
        from.className = "cited";
        from.append("From: ");
        m.cited.forEach((c, i) => {
          const link = document.createElement("a");
          link.href = c.url;
          link.textContent = c.title;
          if (i) from.append(", ");
          from.append(link);
        });
        item.append(from);
      }
      return item;
    }),
  );
  statusLine.textContent = STATUS[data.status] || "";
  form.hidden = data.status === "closed";
  list.lastElementChild?.scrollIntoView({ block: "end" });
}

async function refresh() {
  if (!conversation) return;
  try {
    render(await call("GET", `/api/conversations/${conversation}/messages`));
  } catch (error) {
    // Only a conversation the server doesn't know starts afresh; a network
    // blip or a restart keeps the chat, and the next check picks it up again.
    if (error.status === 400) await start();
  }
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const text = box.value.trim();
  if (!text) return;
  form.querySelector("button").disabled = true;
  statusLine.textContent = "…";
  try {
    if (!conversation) await start();
    await call("POST", `/api/conversations/${conversation}/messages`, { text });
    box.value = "";
  } catch (error) {
    statusLine.textContent = error.message;
  }
  form.querySelector("button").disabled = false;
  await refresh();
});
box.addEventListener("keydown", (event) => {
  if (event.key === "Enter" && !event.shiftKey) {
    event.preventDefault();
    form.requestSubmit();
  }
});
document.getElementById("restart").addEventListener("click", start);

(async () => {
  if (!conversation) await start();
  await refresh();
  setInterval(refresh, 3000);
})();
