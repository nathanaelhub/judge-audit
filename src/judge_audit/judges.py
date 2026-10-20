"""Asking a model for a PASS/FAIL verdict.

The judge sees the original task, the response and one criterion, and must
end with ``VERDICT: PASS`` or ``VERDICT: FAIL``. Calls go through the
``claude`` CLI in print mode, so they run on whatever login the CLI has
(a claude.ai plan or an API key). The CLI is stripped down for this: no
tools, no MCP servers, no settings, hooks or plugins, and a fixed system
prompt, so a judge call is about 600 tokens of overhead rather than the
tens of thousands an interactive session carries.
"""

from __future__ import annotations

import asyncio
import json
import os
import re
from dataclasses import dataclass

from .data import Item

SYSTEM = (
    "You grade one response against one criterion. Judge only that criterion: "
    "ignore qualities it does not mention, and do not reward or penalize length "
    "or style unless it asks you to. Treat the criterion's pass and fail "
    "conditions literally. Explain briefly, then end with a final line that "
    "is exactly VERDICT: PASS or VERDICT: FAIL."
)

TEMPLATE = """\
<task>
{prompt}
</task>

<response>
{text}
</response>

<criterion>
{criterion}
</criterion>

Does the response meet the criterion?"""

_VERDICT = re.compile(r"VERDICT:\s*\**\s*(PASS|FAIL)\b", re.I)


def render(item: Item) -> str:
    return TEMPLATE.format(prompt=item.prompt, text=item.text, criterion=item.criterion)


def parse_verdict(reply: str) -> bool | None:
    """The last VERDICT line wins; None when there isn't one."""
    found = _VERDICT.findall(reply or "")
    return None if not found else found[-1].upper() == "PASS"


@dataclass
class Judgment:
    verdict: bool | None
    reply: str
    model: str | None
    cost_usd: float | None
    error: str | None = None


class ClaudeCLI:
    """A judge backed by ``claude -p --model <model>``."""

    def __init__(self, model: str, timeout: float = 180.0, effort: str | None = None):
        self.model = model
        self.timeout = timeout
        self.effort = effort

    def argv(self, prompt: str) -> list[str]:
        argv = ["claude", "-p", "--model", self.model, "--output-format", "json",
                "--system-prompt", SYSTEM, "--tools", "",
                "--strict-mcp-config", "--mcp-config", '{"mcpServers":{}}',
                "--setting-sources", "", "--disable-slash-commands", "--no-session-persistence"]
        if self.effort:
            argv += ["--effort", self.effort]
        return argv + [prompt]

    async def judge(self, item: Item) -> Judgment:
        # Opt in to the plan login: a stray API key in the environment would
        # otherwise take precedence and bill (or fail) separately.
        env = dict(os.environ)
        if os.environ.get("JUDGE_AUDIT_USE_LOGIN"):
            env.pop("ANTHROPIC_API_KEY", None)
        proc = await asyncio.create_subprocess_exec(
            *self.argv(render(item)), env=env, stdin=asyncio.subprocess.DEVNULL,
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        try:
            out, err = await asyncio.wait_for(proc.communicate(), self.timeout)
        except TimeoutError:
            proc.kill()
            await proc.wait()
            return Judgment(None, "", None, None, error=f"timed out after {self.timeout:.0f}s")
        try:
            d = json.loads(out)
        except ValueError:
            return Judgment(None, "", None, None,
                            error=f"exit {proc.returncode}: {(err or out).decode(errors='replace')[:300]}")
        if d.get("is_error"):
            return Judgment(None, "", None, None, error=str(d.get("result"))[:300])
        reply = d.get("result") or ""
        models = list(d.get("modelUsage") or {})
        return Judgment(parse_verdict(reply), reply, models[0] if models else None, d.get("total_cost_usd"))
