// Screenshots of the chat and the staff views, against showcase/server.py.
// Run: node showcase/shots.cjs (with the server running; needs Playwright,
// e.g. installed globally and found with NODE_PATH="$(npm root -g)").
const { chromium } = require("playwright")

const base = "http://127.0.0.1:8013"
const out = "docs/showcase"

async function api(path, body) {
  const response = await fetch(base + path, {
    method: "POST",
    headers: { "content-type": "application/json", origin: base },
    body: JSON.stringify(body ?? {}),
  })
  if (!response.ok) throw new Error(`${path}: ${response.status} ${await response.text()}`)
  return response.json()
}

async function conversation(text) {
  const { id } = await api("/api/conversations")
  const reply = await api(`/api/conversations/${id}/messages`, { text })
  if (reply.kind !== "handoff") throw new Error(`not handed off in code: ${text}`)
  return id
}

async function main() {
  const browser = await chromium.launch()
  const desktop = { viewport: { width: 1280, height: 900 }, deviceScaleFactor: 2 }
  const errors = []

  // Other customers waiting, so the agents' list has something to sort.
  const person = await conversation("Can I talk to a real person please?")
  await conversation("Why was I charged twice for my bills payment yesterday? Ref 7781-2209")
  await conversation("My card 4111 1111 1111 1111 was blocked, what is the status of my account?")
  const tagalog = await conversation("Gusto ko pong makausap ang isang tao")
  await api(`/api/agent/${tagalog}/hand-back`, { by: "Ana" })
  await api(`/api/agent/${person}/reply`, { by: "Ben", text: "Hi, Ben here from support. How can I help?" })
  await api(`/api/agent/${person}/close`, { by: "Ben" })

  // The customer in the chat: money lost, an OTP typed by mistake.
  const chat = await browser.newPage(desktop)
  chat.on("pageerror", (e) => errors.push(String(e)))
  await chat.goto(base)
  await chat.fill("#text", "Nawala ang pera ko sa padala kahapon! OTP ko 482913, paki-check po")
  await chat.press("#text", "Enter")
  await chat.waitForFunction(() => document.getElementById("status").textContent.includes("person"))
  const id = await chat.evaluate(() => sessionStorage.getItem("conversation"))

  const agent = await browser.newPage(desktop)
  agent.on("pageerror", (e) => errors.push(String(e)))
  await agent.goto(`${base}/agent`)
  await agent.screenshot({ path: `${out}/desktop-2-agents.png`, fullPage: true })

  await agent.goto(`${base}/agent/${id}`)
  await agent.fill("#by", "Ana")
  await agent.fill("#reply", "Hi po, si Ana ito ng support. Tinitingnan ko na po ang padala ninyo kahapon.")
  await agent.screenshot({ path: `${out}/desktop-3-conversation.png`, fullPage: true })
  await agent.click("button[data-action=reply]")
  await agent.waitForLoadState("load")

  await chat.waitForSelector("#messages li.agent", { timeout: 8000 })
  await chat.screenshot({ path: `${out}/desktop-1-chat.png`, fullPage: true })

  await agent.goto(`${base}/owner`)
  await agent.screenshot({ path: `${out}/desktop-4-owner.png`, fullPage: true })

  await agent.goto(`${base}/pages/send-money-fees`)
  await agent.screenshot({ path: `${out}/desktop-5-help-page.png` })

  const phone = await browser.newPage({ viewport: { width: 390, height: 844 }, deviceScaleFactor: 3, isMobile: true })
  phone.on("pageerror", (e) => errors.push(String(e)))
  // The same conversation, set before the page's own script starts one.
  await phone.addInitScript((id) => sessionStorage.setItem("conversation", id), id)
  await phone.goto(base)
  await phone.waitForSelector("#messages li.agent")
  await phone.screenshot({ path: `${out}/phone-1-chat.png`, fullPage: true })

  await browser.close()
  if (errors.length) throw new Error(errors.join("\n"))
  console.log("screenshots in", out)
}

main().catch((error) => {
  console.error(error)
  process.exit(1)
})
