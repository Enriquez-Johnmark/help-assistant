"""The web app: the customer's chat page, the support agents' view and the
content owner's view, over a small JSON API. It answers only on this computer
(G1) and every page says it is a demo for a made-up company (G2)."""

import logging
import threading
from collections.abc import Awaitable, Callable
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

import anthropic
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, ConfigDict, Field

from help_assistant.service import ChatService, Message

DEMO_NOTE = "A demo for Halimbawa Money, a made-up company. Not affiliated with any real company."

# Names this computer answers to; anything else may be a page elsewhere
# pointing its own name at 127.0.0.1 (DNS rebinding), so it is refused (G1).
LOCAL_NAMES = frozenset({"127.0.0.1", "localhost", "::1"})

REASONS = {
    "asked_for_person": "Asked for a person",
    "own_account": "Their own account or a transaction",
    "lost_money": "Money lost or stolen",
    "not_sure": "The assistant wasn't sure",
}

MODEL_DOWN = "The assistant can't answer right now. Please try again in a moment, or ask for a person."

log = logging.getLogger("help_assistant.web")
HERE = Path(__file__).parent


class CustomerText(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    text: str = Field(min_length=1, max_length=2000)


class AgentAction(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    by: str = Field(min_length=1, max_length=60)


class AgentText(AgentAction):
    text: str = Field(min_length=1, max_length=2000)


def _local(host: str | None) -> bool:
    """Whether a Host header or an origin's host names this computer."""
    if not host:
        return False
    return urlsplit(f"//{host}").hostname in LOCAL_NAMES


def create_app(service: ChatService) -> FastAPI:
    app = FastAPI(title="Help Assistant (demo)", docs_url=None, redoc_url=None, openapi_url=None)
    templates = Jinja2Templates(directory=HERE / "templates")
    templates.env.globals["demo_note"] = DEMO_NOTE  # pyright: ignore[reportUnknownMemberType, reportArgumentType]
    app.mount("/static", StaticFiles(directory=HERE / "static"), name="static")
    # One request at a time touches the conversation store: a demo on one computer.
    lock = threading.Lock()
    titles: dict[str, str] = {row["slug"]: row["title"] for row in service.db.execute("select * from pages")}

    @app.middleware("http")
    async def only_this_computer(  # pyright: ignore[reportUnusedFunction]
        request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        if not _local(request.headers.get("host")):
            return Response("This demo answers only on this computer.", status_code=403)
        changes = request.method not in ("GET", "HEAD")
        origin = request.headers.get("origin")
        if changes and (
            (origin is not None and not _local(urlsplit(origin).netloc))
            or request.headers.get("sec-fetch-site") == "cross-site"
        ):
            return Response("Changes are accepted only from this demo's own pages.", status_code=403)
        response = await call_next(request)
        response.headers["Content-Security-Policy"] = "default-src 'self'; frame-ancestors 'none'"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "no-referrer"
        return response

    @app.exception_handler(anthropic.APIError)
    async def model_down(_: Request, error: anthropic.APIError) -> JSONResponse:  # pyright: ignore[reportUnusedFunction]
        # By kind and status only: an error's message may quote the request,
        # and a key must never reach a page or a log (G1).
        log.warning("the model failed: %s %s", type(error).__name__, getattr(error, "status_code", ""))
        return JSONResponse({"detail": MODEL_DOWN}, status_code=502)

    def act[T](do: Callable[[], T]) -> T:
        with lock:
            try:
                return do()
            except ValueError as error:  # the service's own refusals, in plain words
                raise HTTPException(400, str(error)) from None

    def cited(ids: list[str]) -> list[dict[str, str]]:
        links: list[dict[str, str]] = []
        for passage in ids:
            page = passage.split("#")[0]
            links.append({"id": passage, "title": titles.get(page, page), "url": f"/pages/{passage}"})
        return links

    def message(m: Message) -> dict[str, Any]:
        return {"sender": m.sender, "text": m.text, "at": m.at, "cited": cited(m.cited)}

    @app.get("/", response_class=HTMLResponse)
    def chat_page(request: Request) -> HTMLResponse:  # pyright: ignore[reportUnusedFunction]
        return templates.TemplateResponse(request, "chat.html")

    @app.get("/pages/{slug}", response_class=HTMLResponse)
    def help_page(request: Request, slug: str) -> HTMLResponse:  # pyright: ignore[reportUnusedFunction]
        if slug not in titles:
            raise HTTPException(404, "no such help page")
        sections = act(
            lambda: service.db.execute(
                "select id, heading, text from passages where page = ? order by position", (slug,)
            ).fetchall()
        )
        return templates.TemplateResponse(
            request,
            "page.html",
            {
                "title": titles[slug],
                "sections": [
                    {
                        "anchor": s["id"].split("#")[1],
                        "heading": s["heading"],
                        "text": s["text"].partition("\n")[2],
                    }
                    for s in sections
                ],
            },
        )

    @app.post("/api/conversations")
    def start() -> dict[str, str]:  # pyright: ignore[reportUnusedFunction]
        return {"id": act(service.start)}

    @app.get("/api/conversations/{conversation}/messages")
    def messages(conversation: str) -> dict[str, Any]:  # pyright: ignore[reportUnusedFunction]
        status = act(lambda: service.status(conversation))
        return {
            "status": status,
            "messages": [message(m) for m in act(lambda: service.messages(conversation))],
        }

    @app.post("/api/conversations/{conversation}/messages")
    def customer_message(conversation: str, body: CustomerText) -> dict[str, Any]:  # pyright: ignore[reportUnusedFunction]
        reply = act(lambda: service.customer_message(conversation, body.text))
        return {"kind": reply.kind, "text": reply.text, "cited": cited(reply.cited), "warned": reply.warned}

    @app.get("/agent", response_class=HTMLResponse)
    def agent_list(request: Request) -> HTMLResponse:  # pyright: ignore[reportUnusedFunction]
        return templates.TemplateResponse(
            request, "agent.html", {"waiting": act(service.waiting), "reasons": REASONS}
        )

    @app.get("/agent/{conversation}", response_class=HTMLResponse)
    def agent_conversation(request: Request, conversation: str) -> HTMLResponse:  # pyright: ignore[reportUnusedFunction]
        status = act(lambda: service.status(conversation))
        return templates.TemplateResponse(
            request,
            "agent_conversation.html",
            {"id": conversation, "status": status, "messages": act(lambda: service.messages(conversation))},
        )

    @app.post("/api/agent/{conversation}/reply")
    def agent_reply(conversation: str, body: AgentText) -> dict[str, bool]:  # pyright: ignore[reportUnusedFunction]
        act(lambda: service.agent_reply(conversation, body.by, body.text))
        return {"ok": True}

    @app.post("/api/agent/{conversation}/hand-back")
    def hand_back(conversation: str, body: AgentAction) -> dict[str, bool]:  # pyright: ignore[reportUnusedFunction]
        act(lambda: service.hand_back(conversation, body.by))
        return {"ok": True}

    @app.post("/api/agent/{conversation}/close")
    def close(conversation: str, body: AgentAction) -> dict[str, bool]:  # pyright: ignore[reportUnusedFunction]
        act(lambda: service.close(conversation, body.by))
        return {"ok": True}

    @app.get("/owner", response_class=HTMLResponse)
    def owner(request: Request) -> HTMLResponse:  # pyright: ignore[reportUnusedFunction]
        view = act(service.owner_view)
        return templates.TemplateResponse(
            request, "owner.html", {"view": view, "reasons": REASONS, "log": act(service.audit_log)}
        )

    return app
