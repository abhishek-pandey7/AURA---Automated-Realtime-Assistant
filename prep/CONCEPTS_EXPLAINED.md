# Concepts Explained

> Companion to [INTERVIEW_PREP.md](INTERVIEW_PREP.md). That file tells you *what
> to say*. This one makes sure you actually understand it.
>
> Every concept here is taught from scratch — what problem it solves, how it
> works, when it's the wrong choice — and then tied back to the exact place it
> shows up in your repo. If a term in the main doc feels like a word you're
> reciting rather than a thing you know, find it here first.
>
> Part A covers concepts **that are in your code**. Part B covers concepts
> **that aren't** but that interviewers will raise anyway — mostly the
> distributed-systems vocabulary. You need to know those well enough to say
> "that doesn't apply here, and here's why" without sounding evasive.

---

## Table of contents

**Part A — in your code**

- [A0. The groundwork: tokens, context windows, temperature](#a0-the-groundwork)
- [A1. Tool calling (function calling)](#a1-tool-calling-function-calling)
- [A2. The agent loop / ReAct](#a2-the-agent-loop--react)
- [A3. Plugin registry & convention over configuration](#a3-plugin-registry--convention-over-configuration)
- [A4. Two-stage pipelines (planner + executor)](#a4-two-stage-pipelines-planner--executor)
- [A5. Human-in-the-loop, allow-lists vs deny-lists, defence in depth](#a5-human-in-the-loop-allow-lists-vs-deny-lists-defence-in-depth)
- [A6. Retries, backoff, fail-fast, graceful degradation](#a6-retries-backoff-fail-fast-graceful-degradation)
- [A7. Persistence: write-through, atomicity, write amplification](#a7-persistence-write-through-atomicity-write-amplification)
- [A8. Tiered perception: OCR, centroids, vision fallback](#a8-tiered-perception-ocr-centroids-vision-fallback)
- [A9. Runtime code generation & imitation learning](#a9-runtime-code-generation--imitation-learning)
- [A10. Lazy initialisation & singletons](#a10-lazy-initialisation--singletons)
- [A11. Prompt-as-configuration](#a11-prompt-as-configuration)
- [A12. OAuth 2.0, the way you actually used it](#a12-oauth-20-the-way-you-actually-used-it)

**Part B — not in your code, but they'll ask**

- [B1. Caching](#b1-caching)
- [B2. Queues and async work](#b2-queues-and-async-work)
- [B3. Load balancing, replication, sharding](#b3-load-balancing-replication-sharding)
- [B4. Rate limiting](#b4-rate-limiting)
- [B5. CDNs](#b5-cdns)
- [B6. RAG and vector search](#b6-rag-and-vector-search)
- [B7. Context compaction](#b7-context-compaction)
- [B8. Sandboxing and isolation](#b8-sandboxing-and-isolation)
- [B9. Observability](#b9-observability)
- [B10. Idempotency](#b10-idempotency)

---

# Part A — Concepts that are in your code

## A0. The groundwork

Three things everything else rests on. If you're shaky here, the rest won't
land.

### Tokens

A language model doesn't read characters or words — it reads **tokens**, which
are roughly word-fragments. "Automated" might be one token; "AURA" might be two
or three. Rough rule of thumb for English: **1 token ≈ 4 characters ≈ ¾ of a
word.**

Why you care: you pay per token, and you're *limited* per token. When
`aura/agent.py:120` sends the system prompt plus the whole conversation plus
every tool schema, all of that is tokens. Your system prompt is ~70 lines,
call it 900 tokens, and it's resent on **every single iteration**. A 20-step
task pays for it 20 times.

### Context window

The model's working memory: the maximum number of tokens it can consider in one
request — prompt *and* response together. A mid-sized open model like the one
you're running might have 8k to 128k depending on configuration.

This is a **hard wall**, not a soft limit. Go over and the API returns an error;
the model doesn't gracefully forget the oldest part. It's the single most
important constraint in agent design, and it's why §2.6 and Axis 1 of §4 in the
main doc both circle back to it.

Here's the thing that makes agents specifically hard: **the context grows on
every iteration.** Look at `agent.py:121-124` — every loop pass sends
`{system}` + `memory.get_messages()`, and memory only ever grows. Tool results
get appended (`:235`), assistant messages get appended (`:188`). Nothing is ever
removed. So a long task isn't just slower, it's on a collision course with a
wall.

```
iteration 1:  [system][goal]                                    ~1,200 tok
iteration 2:  [system][goal][assistant+tools][tool result]      ~2,000 tok
iteration 3:  [system][goal][...][...][...][...]                ~3,400 tok
...
iteration 20: [system][goal][ ... 60 more messages ... ]        ~40,000 tok  ← wall
```

That shape — cost and risk growing with every step — is why §4 says context is
what breaks first.

### Temperature

A number, usually 0 to 1 (sometimes to 2), controlling randomness in the
model's output. **Low temperature = more deterministic**, picks the most likely
next token. **High temperature = more varied**, more willing to pick less likely
tokens.

You used this deliberately, and it's worth pointing out in an interview because
it shows intent rather than accepting defaults:

| Where | Temperature | Why |
| --- | --- | --- |
| `planner.py:55` | **0.2** | Planning should be stable and repeatable. Same goal → same plan. |
| `agent.py:127` | **0.3** | Execution needs a little flexibility to recover from surprises. |
| `learning.py:125` | **0.1** | Code generation. You want correct syntax, not creativity. |

That's three different values chosen for three different jobs. Say it that way.

### JSON Schema

A standard format for describing the *shape* of data: what fields exist, their
types, which are required. Every `TOOL_DEFS` entry in your repo is JSON Schema.
It's how you tell the model "here is a function, here are its parameters" in a
way the model can program against. More on this in A1.

---

## A1. Tool calling (function calling)

### The problem it solves

A language model can only produce text. It cannot run a command, read a file, or
click a mouse. If you ask a plain chat model "what's in my home directory?" the
best it can do is *describe* how you'd find out.

Tool calling is the bridge. You describe your functions to the model in a
structured format; instead of prose, the model can emit a **structured request
to call one**. Your code executes it and hands back the result. The model never
executes anything — it asks, you decide, you run it.

### How it actually works

Three steps.

**1. You declare what's available.** Every tool module in `aura/tools/` exports
a `TOOL_DEFS` list. Here's the shape, from `aura/tools/shell.py:6`:

```python
TOOL_DEF = {
    "type": "function",
    "function": {
        "name": "bash",
        "description": "Run a shell command in the current working directory. ...",
        "parameters": {
            "type": "object",
            "properties": {
                "command": {"type": "string", "description": "The shell command to execute."},
                "timeout": {"type": "integer", "description": "Max seconds to wait. Default 60."},
            },
            "required": ["command"],
        },
    },
}
```

The **description fields are the real API documentation** — they are the only
thing the model reads to decide whether this tool fits the situation. That's why
yours are verbose and contain warnings like "On Windows this is PowerShell — use
PowerShell syntax only." A vague description produces wrong tool choices. Tool
descriptions are prompt engineering, not comments.

**2. The model responds with a call, not an answer.** You pass
`tools=ALL_TOOL_DEFS, tool_choice="auto"` (`agent.py:125-126`) — "here's
everything you can do, decide for yourself whether to use any." The response
comes back with a `tool_calls` array instead of text: a name, an id, and
arguments as a **JSON string**.

**3. You execute and report back.** `agent.py:199` parses the arguments,
`:213` dispatches, and `:235` appends the result as a message with
`role: "tool"` and the matching `tool_call_id`. The id is what lets the model
pair a result with the request that produced it — necessary because a single
response can contain several parallel tool calls, which your loop handles at
`:194`.

### The detail worth pointing at in an interview

`agent.py:197-210`:

```python
try:
    tool_inputs = json.loads(tc.function.arguments)
except json.JSONDecodeError:
    # Some models wrap JSON in markdown fences
    raw = tc.function.arguments.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        ...
```

The `arguments` field is *specified* to be a JSON string. Your code handles the
case where it comes back wrapped in markdown code fences anyway. That's not
defensive paranoia — that's a real behaviour of smaller open-weight models, and
the same workaround appears independently in `planner.py:73-78`.

This is a genuinely good thing to volunteer, because it shows you know the
difference between the spec and reality: *"I'm running an open-weight model,
and its tool-call formatting isn't always spec-compliant, so the harness
tolerates fenced JSON. That's the tax you pay for model independence."*

### When tool calling is the wrong approach

- **When the task is pure text** (summarise this, translate that). No tools
  needed; you're adding a round trip for nothing.
- **When the sequence is fixed and known.** If you always do A then B then C,
  write `a(); b(); c()`. Letting a model decide adds latency, cost and
  non-determinism to something that had none.
- **When you can't tolerate a wrong choice.** The model *might* pick the wrong
  tool. If a wrong pick is catastrophic and unrecoverable, don't delegate the
  decision.

---

## A2. The agent loop / ReAct

### The problem it solves

One model call gets you one shot. The model has to guess everything about your
environment up front, and if any guess is wrong, the output is quietly broken
and nothing tells you.

Real work isn't like that. Real work is: try something, look at what happened,
adjust. You run the tests, you see the failure, you fix it, you run them again.

**ReAct** — **Rea**soning + **Act**ing — is the pattern that gives a model that
same cycle. Reasoning and acting interleave instead of happening once.

### The loop, concretely

```
   ┌─────────────────────────────────────────────┐
   │                                             │
   ▼                                             │
[ Call the model with: system + full history ]   │
   │                                             │
   ▼                                             │
[ Did it return tool_calls? ]                    │
   │                    │                        │
   │ no                 │ yes                    │
   ▼                    ▼                        │
[ DONE ]          [ Execute each tool ]          │
                        │                        │
                        ▼                        │
                  [ Append results to history ] ─┘
```

That's `aura/agent.py:110-251`, almost line for line. The termination check is
`:156`:

```python
if not message.tool_calls:
    final = message.content or "[ AURA ] Task complete."
```

**No tool calls means finished.** The model signals completion by simply talking
instead of acting.

### Why this specific loop gives you self-correction

Because the tool result goes back into the history, the model *sees what
happened*. Concretely, from your README's own demo trace:

```
iteration 3:  model calls  bash("pytest -v")
              result:      "1 failed, 0 passed ... AssertionError on line 12"
              ↑ this text is now in the conversation

iteration 4:  model has read that failure, calls  patch_file(...)

iteration 5:  model calls  bash("pytest -v")
              result:      "1 passed"

iteration 6:  no tool calls → done
```

There's no error-handling code in AURA that does this. The recovery is emergent
from the loop plus the prompt instruction at `agent.py:38` ("If a command fails,
read stderr, identify the cause, fix it, and retry automatically"). That's the
whole trick, and it's worth saying plainly: *the loop is what turns a text
generator into something that can recover.*

### The two limits you must be able to name

**1. Stopping ≠ succeeding.** "No tool calls" is a *stop* condition. A model
that gave up, got confused, or hallucinated success produces the exact same
signal as one that genuinely finished. You have no verification. This is Q2 in
the main doc and it's the most common follow-up on this topic.

**2. The iteration cap is blunt.** `max_iterations: int = 30` (`agent.py:96`).
It stops runaway loops, which is essential — without it, a model stuck in a
retry cycle burns tokens until your budget is gone. But it also truncates
legitimate long work with a vague message (`:253-254`). A cost/token budget
would be smarter than a step count, because 30 cheap steps and 30 expensive ones
are very different things.

### Alternatives, and when each is better

| Approach | Better when | Worse when |
| --- | --- | --- |
| **Single-shot** | Task is self-contained, no environment interaction | Anything needing feedback |
| **Fixed pipeline / DAG** | Steps are known and stable; you want testability | Task space is open-ended |
| **ReAct loop** (yours) | Environment is unpredictable, recovery matters | You need determinism or cost predictability |
| **Tree search / multi-path** | Some paths dead-end and backtracking pays | Cost matters — it multiplies calls |

The honest framing: if AURA only did Gmail and Calendar, a fixed pipeline would
be the better engineering choice — testable, predictable, cheap. ReAct earns its
complexity specifically because "operate an arbitrary GUI" has no enumerable set
of states.

---

## A3. Plugin registry & convention over configuration

### The problem it solves

You have 13 tool modules and want to add a 14th. The naive approach is a central
list:

```python
from aura.tools import shell, web, filesystem, gmail, ...   # edit this
ALL_TOOLS = [shell.TOOL_DEF, *web.TOOL_DEFS, ...]           # and this
DISPATCH = {"bash": shell.run, "web_fetch": web.web_fetch, ...}  # and this
```

Three places to edit for every new tool, and every one is a place to forget.

A **plugin registry** inverts it: the system *discovers* its own components at
startup instead of being told about them.

### Convention over configuration

The idea that a component declares itself by **following a naming rule** rather
than by being registered somewhere. Your convention, from
`aura/tools/__init__.py:21-33`:

> A module in `aura/tools/` is a tool provider if it exposes `TOOL_DEFS` (a list
> of JSON schemas) or `TOOL_DEF` (a single one). For each schema, the
> implementation is the module-level function whose name equals
> `schema["function"]["name"]`.

Follow that and you exist. No registration call, no import line, no dict entry.

### How the discovery works

```python
pkg_dir = Path(__file__).resolve().parent
for _, module_name, ispkg in pkgutil.iter_modules([str(pkg_dir)]):
    if ispkg: continue
    module = importlib.import_module(f"aura.tools.{module_name}")
```

Two standard-library pieces:

- **`pkgutil.iter_modules([dir])`** — lists every importable module in a
  directory. This is *filesystem* inspection, not code inspection: it finds
  files that exist right now, which is the whole point.
- **`importlib.import_module(name)`** — imports a module by *string name*
  computed at runtime, rather than by a static `import x` statement. That's what
  makes it possible to import a file that didn't exist when the program started.

Then the schemas go in `ALL_TOOL_DEFS` (which is what `agent.py:125` sends to
the model) and the functions go in `_dispatch_map` (which is what `dispatch()`
at `:41` looks up).

### Why this is load-bearing, not decorative

This is the point to hammer if someone asks "why not just use a dict?"

`aura/learning.py:162-166`:

```python
file_path = tools_dir / f"{tool_name}.py"
file_path.write_text(code, encoding="utf-8")
aura.tools._init_tools()          # ← re-scan
```

AURA **writes a new Python file into its own tools directory while running**,
then re-runs discovery. The new tool is available on the very next iteration, in
the same process, with no restart.

A static dict cannot do that. You'd have to edit source and relaunch. So the
registry isn't a style preference — the self-extension feature is impossible
without it. That's a much stronger answer than "it's cleaner."

### The cost, which is real

`aura/tools/__init__.py:36-37`:

```python
except Exception:
    pass # Ignore broken generated tools on startup
```

Every import error — a typo, a missing dependency, a Windows-only import on
Linux — is silently swallowed. The tool simply doesn't exist, with no message
anywhere. The *intent* is right (one bad generated tool shouldn't stop AURA
booting) but silence is the wrong implementation. Catch, **log the module name
and the exception**, continue. Same resilience, actual observability.

This is genuinely the best five-line fix in the codebase and saying so shows
judgement about where effort pays off.

### The other trade-off: implicit contracts break quietly

The "function name must match schema name" rule lives nowhere but in code — and
you already needed an exception to it at `:34`:

```python
elif module_name == "shell" and tool_name == "bash":
    _dispatch_map[tool_name] = getattr(module, "run")
```

`shell.py` exposes `run`, but the tool is called `bash`. One special case,
hardcoded. That's evidence the convention was slightly too tight — a cleaner
design would let a module declare the mapping explicitly (e.g. an optional
`TOOL_IMPL = {"bash": run}`) rather than special-casing one module by name.

### When a plugin registry is the wrong call

- **When the set is fixed and small.** A dict is clearer and statically
  analysable. Your IDE can follow it; it can't follow `importlib`.
- **When you need startup guarantees.** Auto-discovery means you learn about a
  broken component at *use* time, not boot time.
- **When plugins are untrusted.** Auto-importing whatever is in a directory
  means auto-executing whatever is in a directory — module-level code runs on
  import. Combined with A9, that's the security story of this project.

---

## A4. Two-stage pipelines (planner + executor)

### The idea

Rather than one model call doing everything, split the work across calls with
different jobs, different prompts, and different settings. AURA does this in two
stages:

```
  goal string
      │
      ▼
┌──────────────┐   planner.py — temp 0.2, 512 tokens, NO tools
│   PLANNER    │   job: decompose into ≤10 concrete subtasks, return JSON
└──────────────┘
      │
      ▼  ["create dir and files", "write the Flask app", "run tests and fix"]
      │
      ├────────► agent.run_agent(task_1, memory)  ─┐
      ├────────► agent.run_agent(task_2, memory)   │ agent.py — temp 0.3,
      └────────► agent.run_agent(task_3, memory)  ─┘ 4096 tokens, ALL tools
                                        │
                                   one shared Memory
```

### Why split at all

Three distinct benefits, and you should be able to name which one mattered most
(this is one of the `[confirm with me]` spots — the code supports more than one
reading):

**1. The plan is visible before anything runs.** `ui.py:230` renders it in a
panel. For an agent that is about to execute shell commands and move your
physical mouse, showing the intended steps first is a trust mechanism, and it
costs almost nothing. This is a UX argument, and it's a good one.

**2. Each executor context stays focused.** Instead of one sprawling
conversation about a five-part goal, you get five conversations each about one
thing. Less drift, less context.

**3. Different jobs want different settings.** Decomposition wants stability
(temp 0.2, tight token cap). Execution wants a little adaptability (temp 0.3,
4096 tokens for tool arguments). One call can't have two temperatures.

### Soft dependency — the part that's actually well-designed

`planner.py:84-88`:

```python
    except Exception:
        pass

    # Fallback — treat whole goal as one task
    return [goal]
```

If planning fails *entirely* — endpoint down, malformed JSON, anything — the
function returns the original goal as a single-element list and **execution
proceeds normally**. The agent loop is perfectly capable of handling an
undecomposed goal; it just doesn't get the nice plan display.

That's a **soft dependency**: a component whose failure degrades the experience
rather than stopping the system. Contrast with the LLM endpoint itself, which is
a **hard dependency** — if that's down, nothing works. Knowing which of your
dependencies are which is a real architectural skill, and you can point at this
as a case where you got it right.

### The flaw: the plan is frozen

This is the sharpest legitimate criticism of AURA's design and you should raise
it yourself.

The planner runs **before any execution**, so it has zero information about the
environment. It's guessing from the goal string alone. If subtask 2 discovers
that the plan was wrong — the file doesn't exist, the app has a different
layout, the API returned something unexpected — subtasks 3, 4 and 5 still run
exactly as written. There's no mechanism to revise or discard them.

Two things partially mitigate it, and they're worth mentioning so the criticism
doesn't sound worse than it is:

- The ReAct loop *within* each subtask is fully adaptive. Local recovery works
  well; it's only the cross-subtask structure that's rigid.
- All subtasks share one `Memory` instance (`ui.py:248` passes the same object
  each time), so later subtasks can see what earlier ones actually did.

**The real fix is replanning**: after each subtask, feed the results back to the
planner and let it revise the remainder. The cost is latency and money at every
boundary, plus a new failure mode — a replanning loop that oscillates between two
plans forever. So you'd need a replan budget. That's the kind of "here's the fix
*and* what the fix costs" answer that lands well.

---

## A5. Human-in-the-loop, allow-lists vs deny-lists, defence in depth

### Human-in-the-loop (HITL)

An automated system that pauses and asks a human to approve before taking
certain actions. It exists because **automation is fast and confident, and both
of those are bad when it's wrong.**

AURA's version is `aura/confirm.py`: print a panel describing the action, read
Y/N, return a bool. Every risky tool calls it *before* acting:

| Tool | Line | Gated action |
| --- | --- | --- |
| `shell.run` | `shell.py:37` | Dangerous commands only |
| `write_file` | `filesystem.py:103` | Always (with content preview) |
| `patch_file` | `filesystem.py:123` | Always (with before/after preview) |
| `delete_file` | `filesystem.py:153` | Always, `force=True` — unconditional |
| `browser_*` | `browser.py:115` etc. | Navigation, clicks, fills |
| `desktop_*` | `desktop.py:144` etc. | **Auto-approved** — see below |

### Deny-lists vs allow-lists

This distinction comes up constantly in security questions, so know it cold.

A **deny-list** (blacklist) enumerates what's *forbidden*; everything else is
allowed. An **allow-list** (whitelist) enumerates what's *permitted*; everything
else is forbidden.

Yours is a deny-list, `aura/config.py:28-32`:

```python
ALWAYS_CONFIRM_PATTERNS = [
    "rm ", "rmdir", "sudo", "chmod", "chown",
    "dd ", "mkfs", ":(){:|:&};:", "shutdown", "reboot",
    "git push", "pip install", "npm install",
]
```

matched by substring at `confirm.py:11`.

**Allow-lists are strictly more secure, and the reason is structural, not about
effort.** A deny-list has to anticipate every dangerous thing. An allow-list only
has to anticipate every *safe* thing. The set of dangerous things is unbounded
and adversaries add to it; the set of safe things is yours to define. **When you
forget an entry, a deny-list fails open (dangerous thing allowed) and an
allow-list fails closed (safe thing blocked).** Failing closed is an
inconvenience; failing open is a breach.

Your deny-list has a very concrete hole and you should name it before anyone
else does: **`"rm "` does not match `Remove-Item`**, which is the native delete
command on Windows — the platform this project actually targets. The deny-list
has a gap shaped like the primary use case. It also doesn't survive trivial
obfuscation: a tab instead of a space, `$(echo rm)`, a variable.

So: it's a speed bump that catches honest mistakes. That has real value. It is
**not a security boundary** and you shouldn't describe it as one.

### Defence in depth

The principle that you don't rely on a single control. If one layer fails,
another catches it.

Here's the part of your design that's genuinely good, and it's easy to miss:
**confirmation is enforced inside each tool, not once in the agent loop.**

```python
# aura/tools/filesystem.py:102
def write_file(path: str, content: str) -> str:
    approved = confirm_write(path, preview=content)   # ← inside the tool
    if not approved:
        return "[ AURA ] File write cancelled by user."
```

Why this matters: if the check lived in `dispatch()` or in `run_agent()`, then
*any* code path that called `filesystem.write_file` directly would bypass it. A
future feature, a test helper, a refactor — any of them could route around the
gate without anyone noticing. Putting it in the tool means **the check cannot be
separated from the action.**

Say it that way in an interview: *"I put the gate inside the tool rather than in
the dispatcher specifically so no caller can route around it."*

### The exception that undercuts it

`aura/confirm.py:80-86`:

```python
def confirm_desktop(action: str, target: str) -> bool:
    detail = f"Target: {target}"
    if _is_dangerous(detail) or _is_dangerous(action):
        return confirm_action(f"perform desktop action ({action})", detail, force=True)

    # Bypass SAFE_MODE for safe desktop operations
    console.print(f"  [dim]▶ Auto-approved desktop action: {action}[/dim]")
    return True
```

Desktop actions auto-approve. It prints a dim line and returns `True`.

The reasoning is obvious and legitimate: a desktop task is 30+ clicks, and 30
Y/N prompts is an unusable feature. But the *result* is that synthetic mouse and
keyboard events — which can click literally anything on your screen, including
"confirm transfer" — are the **least** gated surface in the application. That's
backwards from a risk standpoint.

The better design, which you should offer: confirm **once per task** rather than
once per action ("AURA wants desktop control for this subtask — Y/N"), plus a
screen-region restriction, plus a kill switch. You have a crude kill switch
already — `pyautogui.FAILSAFE = True` at `desktop.py:6` aborts if the mouse hits
a screen corner — and that's probably why shipping this felt acceptable. It's
not a substitute for a real gate.

### Fail-open vs fail-closed

Worth knowing as a phrase. When a security control errors out, does it let
things through (**fail-open**) or block them (**fail-closed**)?

`confirm.py:52-54` treats empty input as **No**:

```python
elif response in ("N", "NO", ""):
```

Press Enter without typing anything and the action is **cancelled**. That's
fail-closed, and it's the right default — the safe outcome is the one you get by
doing nothing.

---

## A6. Retries, backoff, fail-fast, graceful degradation

### Transient vs permanent failures

The whole of retry logic rests on one distinction:

- **Transient** — will probably work if you try again. Network blip, server
  overloaded (503), timeout, cold start.
- **Permanent** — will never work no matter how many times you try. Bad API key
  (401), nonexistent model (404), malformed request (400).

**Retrying a permanent failure is pure waste**: you burn the full backoff
duration and then fail anyway, having made the user wait for nothing.

Your classifier, `agent.py:135-139`:

```python
is_retryable = (
    "502" in err_str or "500" in err_str or "503" in err_str
    or "timed out" in err_str or "timeout" in err_str
    or "connection" in err_str or "read error" in err_str
)
```

Server errors and network problems retry. Everything else — including a 401 —
breaks out immediately. **That's fail-fast**: recognising a hopeless case and
surfacing it now instead of after 15 seconds of theatre.

The weakness: it's substring matching on an error *message*. `"500" in err_str`
would match an error that merely mentioned "500 tokens." Fragile. Checking a
structured status code from the exception object would be correct.

### Exponential backoff

Retry with increasing delays rather than immediately or at a fixed interval.

```python
wait = (p_retry + 1) * 5     # agent.py:141 → 5s, then 10s
```

Two reasons the delay grows. **A retry that's too fast doesn't help** — if the
server needed 3 seconds to recover, hammering it at 100ms just fails ten more
times. And **retries add load to a system that's already struggling**; backing
off gives it room.

Pedantic note you can use if someone's being precise: 5s→10s is *linear*
backoff, not strictly exponential (which would be 5→10→20, doubling). At three
attempts the distinction doesn't matter, but knowing it is free credibility.

### Jitter

The piece you don't have, and it's fine that you don't.

If a thousand clients all fail at the same moment and all back off by exactly
5 seconds, they all retry at exactly the same moment — a **thundering herd** that
re-crashes the server you were waiting for. **Jitter** adds randomness
(`wait = base * random.uniform(0.5, 1.5)`) so retries spread out.

With one CLI client, jitter is pointless. The correct answer is: *"No jitter,
because there's one client. It'd matter immediately if AURA ran multi-instance,
and that's exactly the kind of thing I'd get for free by using `tenacity`
instead of hand-rolling."*

### Timeouts

`agent.py:21-25`, and the comment is the good part:

```python
# Generous timeout: Render free-tier can be slow on cold starts.
# connect=15s  (time to establish TCP connection)
# read=180s    (time to receive the full streamed response)
_client = OpenAI(..., timeout=httpx.Timeout(timeout=180.0, connect=15.0))
```

Two *separate* timeouts, which is the sophisticated part. **Connect timeout** is
how long to wait to establish a TCP connection — if that takes more than 15
seconds, the host is unreachable and waiting longer won't help. **Read timeout**
is how long to wait for the response body — legitimately long, because a model
generating 4096 tokens genuinely takes minutes.

Collapsing these into one number means either giving up too early on slow
generation, or waiting three minutes to discover a host is down. Splitting them
is correct, and the comment proves it was deliberate.

### Graceful degradation

Reduced functionality instead of total failure. You have three instances, and
naming all three shows it was a pattern rather than a one-off:

| Where | Primary | Degrades to |
| --- | --- | --- |
| `planner.py:87` | LLM-generated plan | The raw goal as one task |
| `web.py:92-98` | DuckDuckGo scrape | Google scrape, then an error string |
| `browser.py:88-112` | Connect to running Chrome via CDP | Launch your Chrome profile, then a clean Chromium |

That third one is the nicest, because it degrades along an axis that *matters*:
tier 1 and 2 give you the user's real cookies and logins; tier 3 gives you a
working browser that's logged into nothing. And it tells the user what happened
and how to fix it (`browser.py:107-109`) rather than silently doing something
worse. **Degrading loudly beats degrading silently** — compare that to §A3's
`except: pass`, which is the same codebase doing the opposite.

### One more pattern worth naming: errors as return values

Every tool in AURA returns a *string* on failure rather than raising:

```python
except Exception as e:
    return f"[ AURA ] Error running command: {e}"
```

This looks sloppy and is actually deliberate. The string goes back to the model
as a tool result — so **the model can read the error and react to it**. A raised
exception would crash the loop; a returned error message becomes an observation
the agent can recover from. That's the self-correction mechanism from A2, and it
only works because errors are data rather than control flow.

`dispatch()` in `tools/__init__.py:44-51` is the safety net: it wraps every tool
call, so even a tool that forgets to handle its own errors can't take down the
agent.

---

## A7. Persistence: write-through, atomicity, write amplification

### Write-through vs write-back

Two strategies for when to put data on disk.

- **Write-back** (or write-behind): keep changes in memory, flush later — at
  exit, on a timer, when a buffer fills. Fast, fewer disk operations. **You lose
  everything since the last flush if the process dies.**
- **Write-through**: every change goes to disk immediately. Slower, more I/O.
  **Nothing is ever lost.**

AURA is write-through. `memory.py:_save()` is called from `add_user` (`:33`),
`add_assistant` (`:38`), and directly from the agent after every tool batch
(`agent.py:189`, `:251`).

**Why that's the right call here:** an agent that controls a desktop gets killed
*constantly*. A misclick, Ctrl-C, the FAILSAFE corner trip, a tool that hangs.
Crashing mid-task is the normal case, not the exception. Write-back would lose
the transcript exactly when you most want to read it.

### Atomicity — the bug in this code

An operation is **atomic** if it either fully happens or doesn't happen at all.
There's no observable halfway state.

`memory.py:49-56` is **not** atomic:

```python
def _save(self):
    path = SESSIONS_DIR / f"{self.session_id}.json"
    with open(path, "w") as f:                    # ← truncates the file NOW
        json.dump({...}, f, indent=2)             # ← then writes
```

`open(path, "w")` **empties the file immediately**, before a single byte of new
content is written. If the process dies in that window — Ctrl-C at the wrong
millisecond, power loss — the session file is left truncated or half-written.
And `_load()` at `:58` will throw a `JSONDecodeError`, so the session is
unrecoverable.

The standard fix is **write-to-temp-then-rename**:

```python
tmp = path.with_suffix(".tmp")
with open(tmp, "w") as f:
    json.dump({...}, f, indent=2)
os.replace(tmp, path)     # atomic on POSIX and on Windows
```

`os.replace` is atomic at the filesystem level: the path points at either the
complete old file or the complete new one, never at a partial one. Two lines.
Know this fix — "how would you make a file write crash-safe" is a common
question and this is the textbook answer.

### Write amplification

Writing far more bytes than the logical change requires.

Your `_save()` re-serialises **the entire message list** on every append. So:

```
message 1  → write 1 message
message 2  → write 2 messages
message 3  → write 3 messages
...
message n  → write n messages
             ─────────────────
  total:     1+2+3+...+n = n(n+1)/2  →  O(n²)
```

Appending one message costs time proportional to everything written so far. With
50 messages containing base64 screenshots, you're rewriting megabytes, dozens of
times.

**The fix is an append-only log** — JSONL, one JSON object per line:

```python
with open(path, "a") as f:
    f.write(json.dumps(message) + "\n")    # O(1) per message
```

The trade-off is real though: you lose the single-readable-document property.
Right now you can open a session file and it's valid, pretty-printed JSON — which
genuinely helps when you're debugging a strange agent run, and that's worth
something at this stage of a project. JSONL needs a parse loop, and metadata
needs somewhere else to live.

### The wire-format detail worth pointing at

`agent.py:173-187` stores assistant messages in exactly the shape the API
expects to receive back:

```python
assistant_msg = {
    "role": "assistant",
    "content": message.content or "",
    "tool_calls": [
        {"id": tc.id, "type": "function",
         "function": {"name": tc.function.name,
                      "arguments": tc.function.arguments}}  # stays a JSON string
        for tc in message.tool_calls
    ],
}
```

Note the comment in your own code: `# stays as JSON string`. You're deliberately
*not* parsing `arguments` into a dict before storing it, because the API expects
a string there. Parse it for your own use (which you do separately at `:199`),
store it as received.

This is what makes `/resume` work at all: the session file can be loaded and
sent straight back to the model with no transformation. **Store data in the
format your consumer needs, not the format that's convenient to look at** —
that's a general lesson and this is a clean example of it.

### The unbounded-growth problem

`get_messages()` returns everything, always. No trimming, no summarisation, no
cap. Combined with the context-window wall from A0, long sessions are on a
collision course and there's no handling for it.

One detail shows you *saw* part of this problem — `agent.py:226-233` intercepts
base64 screenshots and strips them out of the stored tool message, replacing
them with `"[ screenshot attached in next message ]"`. That's deliberate
anti-bloat work. But the image still gets appended as a user message at `:242`
and lives in the history forever, so it's a partial fix. Worth mentioning both
halves — it demonstrates you were thinking about context cost, and it's honest
about the limit.

---

## A8. Tiered perception: OCR, centroids, vision fallback

### The problem

To click a button on screen, something has to know where the button *is*. Three
options:

1. **Hardcode coordinates.** Works until anything moves. (This is what your
   *generated* tools do, and it's their main flaw.)
2. **Ask a vision model.** "Where's the search box?" Flexible, expensive, slow,
   and VLM coordinate estimates are genuinely unreliable.
3. **OCR the screen.** Extract every text string with its exact pixel position.
   Fast, local, free — but blind to anything that isn't text.

AURA does 3 with 2 as a fallback. That's **tiered perception**: cheap method
first, escalate only when it fails.

### What OCR gives you here

`desktop_read_screen` (`desktop.py:212`) uses `winsdk.windows.media.ocr` — the
OCR engine **built into Windows**. Not Tesseract, not a cloud API. Locally
installed, no network, no per-call cost.

The output is a spatial map:

```
[ AURA ] Screen Map (1920x1080) — 47 text regions found:
   [  X ,   Y ]  Text
  -------------------------------------------------------
  [  84,   18]  File Edit View History Bookmarks
  [ 640,   52]  Search or enter address
  [ 312,  240]  Sign in to your account
  [ 456,  388]  Continue
```

The model reads that and calls `desktop_click(x=456, y=388)`. **Perception
becomes text**, and text is what the model consumes natively.

### Centroids — what that word means

A **centroid** is the geometric centre of a shape. The OCR engine returns a
bounding *rectangle* per word (x, y, width, height), but to click you need a
single point.

`desktop.py:247-250`:

```python
xs = [w.bounding_rect.x + w.bounding_rect.width / 2 for w in words]
ys = [w.bounding_rect.y + w.bounding_rect.height / 2 for w in words]
cx = int(sum(xs) / len(xs))
cy = int(sum(ys) / len(ys))
```

For each word: centre = left edge + half the width. Then average across all
words in the line, giving the centre of the whole line.

**The approximation this bakes in:** the centre of a *text label* is not
necessarily inside its *clickable control*. For a button with a centred label
they coincide and it works perfectly. For a wide table row, or a label sitting
beside its checkbox rather than on it, the centroid can land outside the hit
area. This is a known limit, not a bug, and it's a good honest detail to raise.

### The async bridge — a smell worth being able to explain

`desktop.py:262-264`:

```python
import concurrent.futures
with concurrent.futures.ThreadPoolExecutor(1) as pool:
    return pool.submit(asyncio.run, _read()).result()
```

Why this exists: the WinRT OCR API is **async** (`await engine.recognize_async`),
but your tool functions are **sync** — `dispatch()` calls them plainly and the
whole agent loop is synchronous. You can't `await` from sync code, and calling
`asyncio.run()` directly fails if an event loop is already running in the
thread.

The workaround: spawn a one-thread pool, run `asyncio.run` inside *that* thread
(which has no event loop of its own), and block on the result.

It works. It's also a smell: a fresh thread pool created and destroyed on every
single screen read. The cleaner fix is one long-lived worker thread with a
persistent loop, or making the tool layer async throughout. Being able to say
"here's why this odd code exists, here's what I'd do instead" is much better
than hoping nobody asks.

### The vision fallback

`desktop_analyze_screen` (`:320`) is tier 2: screenshot → downscale to 1024px →
JPEG at quality 85 → base64 → send to a vision model.

The downscale and compression are deliberate cost control. A raw 1920×1080 PNG
is enormous as base64; 1024px JPEG is a fraction of the tokens and loses nothing
the model needs.

Then `agent.py:226-249` does something a bit clever: the tool returns the image
as `[ IMAGE_BASE64: data:image/jpeg;base64,... ]`, and the agent **intercepts
that marker**, strips the payload out of the tool-result message, and re-attaches
it as a proper `image_url` content block on a following user message. Tools
return strings (that's the contract), but images need structured multimodal
content — so the marker is a channel for smuggling non-string data through a
string-typed interface.

It's a workaround, and the cleaner design is for tools to return a structured
type rather than a string. But it solves a real problem and you should be able
to explain the constraint that forced it.

### The platform lock-in

`winsdk` is Windows-only — it's a binding to WinRT. `pyproject.toml` marks it
`sys_platform == 'win32'`, so on Linux it isn't installed, the import at
`desktop.py:216` fails, and §A3's `except: pass` silently swallows it. Result:
every `desktop_*` tool simply doesn't exist on Linux, **with no message
explaining why**. Two weaknesses compounding — worth naming as an example of how
silent failure handling makes other problems harder to diagnose.

### The better long-term answer: accessibility APIs

Know this as your "what I'd build next" for desktop.

Operating systems expose **accessibility APIs** — UI Automation on Windows,
AT-SPI on Linux, NSAccessibility on macOS — built for screen readers. They give
you the actual **widget tree**: this is a button, it's named "Submit", it's
enabled, here's its bounds, here's its parent dialog.

That's categorically better than OCR. A button is *a button*, not a string that
happens to sit at (456, 388). You get element types, states, and stable handles
that survive the window moving.

The costs: much more implementation work, deeply platform-specific, and it
doesn't cover apps that draw their own UI (Electron, games, canvas-based apps) —
which is precisely where OCR still wins. The realistic answer is both: a11y tree
when available, OCR when not.

---

## A9. Runtime code generation & imitation learning

### The idea

Some tasks can't be automated by API because there is no API, and can't be
automated by OCR navigation because the UI is too idiosyncratic. The remaining
option: **have the user demonstrate it once, and generate code from the
demonstration.**

That's imitation learning in the loosest sense — learning a behaviour from
observed examples rather than from a specification.

### The pipeline

```
 aura learn "check my bank balance"
        │
        ▼
 ┌──────────────┐  pynput hooks the OS input stream
 │  RECORD      │  → "T+2.3s: Clicked left at (450, 210)"
 │ learning.py  │  → "T+3.1s: Typed 'a'" ...
 │   :45-70     │  + screenshot before, screenshot after
 └──────────────┘
        │
        ▼
 ┌──────────────┐  trace + both images → vision model
 │  GENERATE    │  prompt: "write a self-contained module with
 │   :82-130    │           TOOL_DEFS + a pyautogui function"
 └──────────────┘
        │
        ▼
 ┌──────────────┐  strip fences, regex the function name,
 │  INSTALL     │  write aura/tools/<name>.py,
 │  :145-166    │  call _init_tools() → live immediately
 └──────────────┘
```

### Why an LLM is in the loop at all

This is the question worth having a crisp answer for, because "why not just
replay the recording?" is the obvious challenge.

A raw macro replay is **more faithful and fully deterministic** — it does exactly
what you did. But it hardcodes everything, including the literal characters you
typed. It cannot generalise.

The LLM's job is **abstraction**: turning a specific trace into a parameterised
function. And you have proof it worked — `jiohotstar.py:23`:

```python
def jiohotstar_play(query: str) -> str:
```

The recording contained you typing one specific show name, character by
character. The generated tool takes `query` as a **parameter** and does
`pyautogui.write(query, interval=0.05)` (`:46`). Thirty individual keystroke
events in the trace became one parameterised call. That generalisation is
entirely the model's contribution, and it's the whole justification for the
approach.

### The security property — say this before they ask

```python
file_path.write_text(code, encoding="utf-8")   # learning.py:165
aura.tools._init_tools()                       # :166  → imports it
```

**Model output is written to disk as Python and then imported and executed, with
no review of any kind.** No diff shown to the user, no `ast.parse`, no sandbox.
Module-level code in that file runs at import; the function runs on the next
dispatch. All with your user's permissions.

This is the most serious security property in the project. The right posture in
an interview is to raise it yourself, in plain terms, along with the fix ladder:

1. **Show the code and ask Y/N.** You already have exactly this pattern —
   `confirm_write` at `confirm.py:60` shows a preview and asks. It's *inconsistent*
   that ordinary file writes are gated and codegen isn't. That inconsistency is
   the interesting part: it means you weren't thinking of the codegen path as a
   write at all.
2. **AST allow-list.** Parse the generated module with `ast.parse` and reject
   anything outside a permitted set. A recorded GUI macro should only ever need
   `time` and `pyautogui` — so an `import subprocess`, an `open()`, or an
   `eval` is mechanically rejectable. Cheap and high value.
3. **Sandbox execution.** The real answer, and the expensive one. See B8.

### The brittleness — and the fix that makes this feature good

Look at what actually got generated,
`check_bitcoin_price_coinmarketcap.py:22-33`:

```python
pyautogui.press('cmd')           # ← wrong key for Windows
time.sleep(1.5)
pyautogui.click(1287, 1052)      # ← frozen pixel coordinate
time.sleep(0.5)
pyautogui.write('coinmarketcap.com')
pyautogui.press('enter')
time.sleep(5.0)                  # ← a guess, not a wait
```

Three distinct problems:

- **Frozen coordinates.** `click(1287, 1052)` breaks on a different resolution, a
  moved window, or a changed page layout. Nothing about it is robust.
- **Wrong platform assumption.** `press('cmd')` is the macOS key. This is a
  Windows project. The model got it wrong and nothing caught it.
- **`time.sleep()` as synchronisation.** Sleeping 5 seconds and hoping the page
  loaded is a race condition. Sometimes it's too short (fails), usually it's too
  long (slow). It is not a wait — a wait checks a condition.

**And here's the fix that ties the whole project together, which is why it's
your best "what's next" answer:** you already built a perception layer.
`desktop_find_text("Search")` returns live coordinates *at run time*. If the
code generator emitted **OCR anchors instead of pixel coordinates** —

```python
# instead of:  pyautogui.click(1287, 1052)
# emit:        loc = desktop_find_text("Search"); click there
```

— then generated tools would relocate their targets on every run, surviving
window moves and resolution changes entirely. Same recording, durable output.

It's mostly a prompt change (tell the generator what to emit) plus a helper
function. Not a rewrite. That's the single change that would take
watch-and-learn from impressive demo to genuinely useful, and being able to name
it precisely is worth a lot.

### The fragile parsing

`learning.py:145-158` strips markdown fences by hand and then:

```python
match = re.search(r'def\s+([a-zA-Z0-9_]+)\(', code)
tool_name = match.group(1)
```

The tool name is taken from **the first `def` in the file** — by regex. If the
model emits a helper function first, you get the helper's name, the file is
saved under the wrong name, and the registry's name-matching convention (§A3)
silently fails to bind it.

The robust version is to `ast.parse` the code and find the function whose name
matches the name declared in the generated `TOOL_DEFS` — which also validates the
one invariant the registry actually requires. Same parse pass gives you the
security check from the fix ladder above. Two birds.

---

## A10. Lazy initialisation & singletons

### Lazy initialisation

Don't create an expensive thing until someone actually needs it.

`browser.py:80`:

```python
def _ensure_started(self):
    if self._page is None:
        from playwright.sync_api import sync_playwright
        self._playwright = sync_playwright().start()
        ...
```

The guard `if self._page is None` is the whole pattern: first call does the
setup, every later call is a no-op. Every public browser function calls
`_ensure_started()` first (`:117`, `:128`, `:141`, ...), so the browser comes up
on first use regardless of which tool triggers it.

**Why here:** launching Chromium takes seconds and hundreds of megabytes, and
most AURA tasks never touch the browser at all. Eager initialisation would tax
every single startup for a capability usually unused. Note also that the
`playwright` import itself is inside the function — even the import cost is
deferred.

**The cost:** the first browser call is mysteriously slow, and the model may read
that latency as a failure. And you find out the browser is broken mid-task
rather than at startup, which is a worse time to find out.

### Singleton

Exactly one instance of something, shared by everyone.

`browser.py:184-191`:

```python
_session: BrowserSession | None = None

def _get_session() -> BrowserSession:
    global _session
    if _session is None:
        _session = BrowserSession()
    return _session
```

**Why here — and this is the important part:** your tool API is *stateful*.
`browser_click(selector)` acts on "the current page." That phrase only means
something if the page persisted from the previous `browser_navigate`. A fresh
browser per call would break the entire design, not merely be slower.

### The costs, which are the standard criticisms of singletons

- **Global mutable state.** Hard to test — you can't construct an isolated
  `BrowserSession` in a test without monkeypatching the module global. Hard to
  reason about — any code anywhere can mutate it.
- **Not thread-safe.** Two threads could both evaluate `_session is None` as true
  and both construct a browser. Irrelevant for a single-threaded CLI; a real bug
  the moment AURA runs tasks in parallel. The same race exists in
  `_ensure_started`.
- **Lifecycle is nobody's job.** `close_browser()` exists at `:211` and **is
  never called anywhere in the codebase.** The Playwright process leaks until
  AURA exits. An `atexit` hook or a REPL shutdown handler would fix it. Worth
  volunteering — "I have a cleanup function I forgot to wire up" is a small,
  honest, very human admission.

### The three-tier fallback — the good part of this file

`browser.py:88-112` is genuinely nice engineering and deserves airtime:

1. **`connect_over_cdp("http://localhost:9222")`** — attach to a Chrome the user
   already launched with remote debugging. Best case: their real browser, real
   session, nothing disrupted.
2. **`launch_persistent_context(user_data_dir=...)`** — launch Chrome with the
   user's actual profile directory. Their cookies and logins, but AURA controls
   the process. Fails if Chrome is already running (profile directories are
   exclusively locked).
3. **`chromium.launch()`** — a clean isolated Chromium. Works always, logged into
   nothing.

The degradation is along the axis that matters — **authenticated session state**
— and the failure message at `:107-109` tells the user precisely what went wrong
and how to get tier 1 or 2 back.

And then, in the same function at `:85`:

```python
user_data_dir = r"C:\Users\Abhishek Pandey\AppData\Local\Google\Chrome\User Data"
```

Thoughtful fallback design and a hardcoded personal absolute path, eight lines
apart. Point at both — it's a good illustration of the difference between design
thinking and debugging residue, and owning that distinction reads well.

---

## A11. Prompt-as-configuration

### The idea

In a normal program, behaviour lives in control flow — `if`, `for`, function
calls. In an LLM system, a large part of behaviour lives in **prose**. The
system prompt is configuration: it's where policy is written.

`aura/agent.py:27-93` is ~70 lines of this, templated at runtime with live
environment facts (`:106`):

```python
system = SYSTEM_PROMPT.format(cwd=cwd, now=now, os_name=os_name, shell=shell)
```

### Injecting environment facts — a small, clever thing

Look at what gets templated in: OS, shell, current working directory, and
**current date/time**. Then this rule at `:57-59`:

> CRITICAL DATE RULE:
> - You already know the current date and time from the system info above. NEVER
>   call bash just to get the date.

Without that, the model would burn a whole iteration — an API round trip, a
subprocess spawn, tokens — to learn something you could have simply told it.
**Putting known facts in the prompt eliminates entire classes of tool call.**
That's a concrete, cheap optimisation and a good detail to mention.

### The CRITICAL rules are a changelog of bugs

Read them as history rather than as documentation:

| Rule | The failure it's responding to |
| --- | --- |
| `:62` "NEVER use smtplib, yagmail" | The model wrote SMTP scripts instead of using `gmail_send` |
| `:58` "NEVER call bash just to get the date" | It shelled out for `date` |
| `:45` "use PowerShell syntax, NOT `date +%Y-%m-%d`" | It emitted Unix commands on Windows |
| `:69` "NEVER create a Meet via browser tools" | It tried to automate the Meet UI instead of calling the API |
| `:86` "PERCEPTION FIRST" | It guessed coordinates instead of reading the screen |

Every one is something you watched go wrong. Say it exactly that way in an
interview: *"those rules are a changelog of failures I observed."* It's honest,
it's specific, and it shows the prompt was developed empirically rather than
written once and forgotten.

### Prompts vs code — the real trade-off

| | Prompt rule | Code enforcement |
| --- | --- | --- |
| **Strength** | A strong suggestion | An absolute guarantee |
| **Cost to write** | One line of English | A real implementation |
| **Cost to run** | Tokens, on every single call | Effectively zero |
| **Testable?** | Not really | Yes, trivially |
| **Failure mode** | Model ignores it, silently | Fails loudly and predictably |

The smtplib rule is the clean example. As a prompt rule it costs ~20 tokens per
call and the model *usually* complies. As a code check in `dispatch()` —
"reject any `bash` call whose command contains `smtplib`" — it's free at runtime
and **cannot** be violated. But it's more brittle to write and it fails closed in
ways that might surprise a user with a legitimate reason to use smtplib.

The honest summary: prompt rules were the fastest available lever, they're
unenforced, and the ones that matter most should eventually migrate into code.

### The token cost, quantified

The system prompt is ~70 lines (~900 tokens), and **every tool schema goes in
every request** (`agent.py:125`). With 30-plus tools at roughly 100 tokens of
schema each, that's ~3,000 more. So roughly **4,000 tokens of fixed overhead
before the conversation even starts** — paid on every iteration of every task,
including "read this one file."

That's the number behind Axis 2 of §4 in the main doc: at 300 tools it becomes
untenable, and the fix is retrieval over tools (see B6).

---

## A12. OAuth 2.0, the way you actually used it

### The problem OAuth solves

You want AURA to send email as you. The naive approach — store your Gmail
password — is terrible: the app gets unlimited access forever, revoking it means
changing your password, and any breach exposes the credential itself.

**OAuth 2.0** replaces that with delegated, scoped, revocable access. You
authenticate with *Google*, not with AURA. Google hands AURA a **token** that
grants specific permissions and can be revoked independently.

### The flow in your code

You're using the **Installed Application** flow (also called the desktop flow),
`gmail.py:102-103`:

```python
flow = InstalledAppFlow.from_client_secrets_file(creds_path, SCOPES)
creds = flow.run_local_server(port=0)
```

What actually happens:

1. `credentials.json` identifies **the app** (client id/secret from Google Cloud
   Console). It's not a user credential.
2. `run_local_server(port=0)` spins up a temporary local HTTP server on a random
   free port and opens your browser to Google's consent screen.
3. You log in *to Google* and approve the requested scopes. AURA never sees your
   password.
4. Google redirects back to that local server with an authorisation code, which
   is exchanged for tokens.
5. Tokens are written to `token.json` (`:105-106`). Next run reuses them — the
   browser flow happens **once**.

### Access tokens vs refresh tokens

Two different things and interviewers do ask.

- **Access token** — short-lived (typically ~1 hour), sent with each API call.
  Short-lived deliberately: a leaked one expires fast.
- **Refresh token** — long-lived, used only to obtain new access tokens without
  re-prompting the user. This is the sensitive one.

`gmail.py:88-90`:

```python
if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
```

Access token expired but a refresh token is present → refresh silently. Only if
that's impossible do you fall back to the full browser flow. That's why AURA
asks you to log in once and never again.

### Scopes — least privilege

**Scopes** are the specific permissions requested. `gmail.py:15-19`:

```python
SCOPES = [
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/calendar",
]
```

Note `gmail.send` and `gmail.readonly` rather than full `https://mail.google.com/`.
That's **least privilege** — request the narrowest permission that does the job,
so a compromised token does less damage. Worth pointing out; it's the kind of
detail that signals you understand *why* scopes exist rather than just copying a
sample.

### The live bug — know this one

The three Google modules declare **different scope lists**:

| File | Line | Scopes declared |
| --- | --- | --- |
| `gmail.py` | `:15` | gmail.send, gmail.readonly, calendar |
| `meet.py` | `:17` | calendar, gmail.send, gmail.readonly |
| **`calendar.py`** | **`:17`** | **calendar only** |

All three read and write **the same `token.json`**. And
`Credentials.from_authorized_user_file(token_path, SCOPES)` is passed whichever
list the calling module happens to declare.

So: if `calendar.py` is what triggers the initial OAuth flow, the token is
minted with calendar scope only — and a later `gmail_send` fails with a scope
error. If `gmail.py` goes first, everything works. **Behaviour depends on which
tool the user happens to invoke first**, which is exactly the kind of bug that
only reproduces for a brand-new user and therefore never reproduced for you.

The fix: one `aura/google_auth.py` with a single superset scope list, imported by
all three. That also removes the ~35 lines of near-identical `_get_service()`
duplication.

This is a strong thing to raise unprompted, because finding a real ordering-
dependent bug in your own code — and explaining *why* you wouldn't have hit it —
demonstrates genuine analysis rather than rehearsed talking points.

### Token storage

`token.json` sits unencrypted in the project root. It's gitignored (correctly —
check `.gitignore`), but it's a live refresh token in plaintext on disk. Anyone
with filesystem access has your Gmail and Calendar.

For a local single-user tool that's a defensible trade (it's the same threat
model as your browser's cookie store). For anything hosted, it isn't — see B8
and the multi-user section of the main doc.

---

# Part B — Concepts that aren't in your code

You did not use these. **That's correct** — AURA is a local single-user CLI and
adding them would be architecture for its own sake. But interviewers will raise
them, and "we didn't need that, here's why, and here's exactly when I would"
is a much stronger answer than a blank look or a made-up justification.

## B1. Caching

**What it is.** Store the result of expensive work so you don't redo it. The
cost is that cached data can go **stale** — the underlying truth changes and your
copy doesn't.

The central question in any caching design is **invalidation**: how do you know
when to throw the copy away? Options are time-based (TTL — expire after N
seconds, simple, sometimes wrong), event-based (invalidate when the source
changes, correct, needs plumbing), or never (fine only for immutable data).

**Where it would apply to AURA:**

- **Prompt caching.** Providers can cache the processed form of a static prompt
  prefix. Your ~4,000-token system-prompt-plus-schemas block (see A11) is
  identical on every iteration — exactly the shape prompt caching exists for.
  You can't use it because you're on a self-hosted proxy, and that's a real,
  quantifiable cost of the model-independence trade. Good detail.
- **Semantic caching of plans.** Same goal → same plan. You could cache
  `planner.plan()` results keyed by goal text. **Danger:** the plan may be
  correct for the goal but wrong for the *current environment*, which has
  changed. Stale plans are worse than slow plans.
- **`web_fetch` results.** Fetching the same URL twice in one session is pure
  waste. Easy win, low risk with a short TTL.

**What you'd say:** *"Caching applies in three places, and the one I'd actually
want is prompt caching for the static prefix — but I can't have it because I'm
self-hosting. That's a genuine cost of the portability choice."*

## B2. Queues and async work

**What it is.** Instead of doing work in the request, put a **message** on a
queue; **worker** processes pull and execute it. Decouples the requester from the
executor.

**Why anyone does it:** absorb bursts (the queue buffers), scale workers
independently, retry failed work durably, and survive worker crashes without
losing the job.

**Where it would apply:** only in the multi-user case. A session becomes a
durable job; workers pull them; the UI polls for status.

**The catch you should absolutely mention**, because it shows systems thinking:
**a queue breaks your confirmation model.** A background worker cannot call
`console.input()` (`confirm.py:46`) — there's no terminal attached and nobody
watching. You'd need **asynchronous approval**: the job suspends, persists its
pending-decision state, notifies the user out-of-band, and resumes when a
decision arrives.

So moving to a queue is not a drop-in change — it's a redesign of the safety
layer from A5. Naming that coupling unprompted is the strong version of this
answer.

## B3. Load balancing, replication, sharding

Three different things that get conflated. Know the distinction.

**Load balancing** — distribute incoming requests across multiple identical
servers. Solves: one server can't handle the volume. Needs the servers to be
interchangeable, which means **statelessness** (or sticky sessions, which
partially defeats the point).

**Replication** — keep copies of the same data on multiple machines. Solves:
read capacity and availability (a replica can take over if the primary dies).
Introduces **replication lag**: a write to the primary isn't instantly visible on
replicas, so a user can write something and then not see it. That's
**eventual consistency**, and it's the standard trade.

**Sharding** — split data across machines by key, so each machine holds a
*different* subset. (Users A–M here, N–Z there.) Solves: the data doesn't fit on
one machine, or write volume exceeds one machine. Costs: queries spanning shards
become expensive, cross-shard transactions are hard, and **choosing a shard key
badly creates hot spots** that undo the whole exercise.

**Where they'd apply to AURA:** load balancing across inference replicas, if you
hosted it. Replication and sharding — essentially nowhere, because there's no
shared dataset. Session files are per-user and never queried across users.

**What you'd say:** *"Load balancing across inference replicas, yes. Sharding,
no — there's no shared dataset to split. Sessions are per-user and nothing ever
queries across them, so sharding would solve a problem I don't have."*

## B4. Rate limiting

**What it is.** Cap how much a client can consume in a time window. Protects
shared resources from being monopolised — whether by abuse or by one honest
runaway process.

**Common algorithms**, worth knowing by name:

- **Token bucket** — a bucket refills at a steady rate; each request takes a
  token. Allows bursts up to bucket size, then throttles to the refill rate. The
  most commonly used.
- **Leaky bucket** — requests drain at a fixed rate. Smooths bursts entirely.
- **Fixed window** — N requests per minute. Simple, but has a boundary problem:
  you can do 2N across a window boundary.
- **Sliding window** — fixes the boundary problem at the cost of more state.

**Where it would apply:** multi-user hosting. One user's 200-iteration agent loop
could saturate a self-hosted model and starve everyone else. Per-user limits on
iterations, tokens, or concurrent sessions.

**The trade-off worth stating:** an agent that gets throttled *mid-task* is worse
UX than one that's uniformly slow — it stalls in an unfinished state, which is a
confusing thing for a user to look at. You'd want limiting at *session admission*
(refuse to start) rather than mid-loop where possible.

## B5. CDNs

**What it is.** Content Delivery Network — copies of static assets cached at
servers geographically near users, so a request travels 50km instead of 5,000.
Cuts latency and takes load off the origin.

**Where it applies to AURA: nowhere, and say so directly.** There are no static
assets, no web frontend, no geographic distribution of users. There is one
process on one laptop.

If you built the web dashboard from your README roadmap, a CDN would serve its
JS and CSS. That's the entire answer. Don't manufacture more — confidently
saying "not applicable, and here's the only scenario where it would be" is the
right response, and pretending otherwise is exactly the failure mode this
question is designed to detect.

## B6. RAG and vector search

**RAG** — Retrieval-Augmented Generation. Rather than putting everything in the
prompt, store your corpus externally, **retrieve** only the relevant parts at
query time, and inject those.

**How retrieval works.** An **embedding model** turns text into a vector — a list
of numbers positioning that text in a semantic space where similar meanings land
near each other. Store vectors in a **vector database** (Chroma, FAISS, pgvector,
Pinecone). At query time, embed the query and find the nearest vectors by cosine
similarity. "Nearest" means *semantically* similar, not keyword-matching — which
is why it finds "automobile" for a query about "car."

**The two places it applies to AURA:**

**1. Tool retrieval** (Axis 2 of §4). At 300 tools you can't put every schema in
every prompt. Embed the descriptions; inject only the top-k relevant to the
current goal. `_init_tools()` is already the natural place to build the index.

**The trade-off is important and specific:** a retrieval miss means the agent
**cannot see** the tool it needs and will confidently do something worse with a
tool it *can* see. That's a nastier failure than a big prompt, because it's
silent. Mitigation: **pin** the core tools — bash, file ops — as always-present
regardless of retrieval, and only make the long tail retrievable.

**2. Long-term memory.** Embed past session transcripts; retrieve relevant ones
when starting a new task. This is your README's "Long-term Memory (RAG)" roadmap
item and it's the natural evolution of `memory.py`. Also where SQLite or a real
vector store finally earns its place over JSON files.

## B7. Context compaction

**What it is.** Managing a growing conversation so it stays inside the context
window (A0). Strategies:

- **Truncation** — drop the oldest messages. Trivial, and it loses the goal
  itself, which is usually the first message. Bad.
- **Sliding window** — keep the last N, plus always pin the original goal.
  Better, still loses the middle.
- **Summarisation** — periodically compress older turns into a digest with a
  cheap model; keep recent turns verbatim. The usual answer.
- **Hierarchical** — summaries of summaries for very long runs.

**Where it applies: directly, and it's the answer to "what breaks first."**
`memory.get_messages()` returns everything, forever. Around 20 iterations you're
near the limit of a mid-sized model.

**The trade-off to name:** summarisation is **lossy and irreversible**. Compact
away the one detail the agent needed later and you get a bug that is nearly
impossible to reproduce, because the information is simply gone. Plus an extra
LLM call at each compaction boundary.

A practical refinement worth offering: **tool results are usually the biggest and
least reusable part of the history.** A 4,000-character page fetch matters for
one or two iterations and then never again. Compacting *tool results
specifically* — while keeping the assistant's reasoning verbatim — gets most of
the savings with much less risk than summarising everything uniformly.

## B8. Sandboxing and isolation

**What it is.** Restricting what code can do, so untrusted code can't harm the
host. Layers, weakest to strongest:

- **Process isolation** — separate user accounts, dropped privileges. Weak.
- **Containers** (Docker) — isolated filesystem, network and process namespaces,
  but a **shared kernel**. A kernel exploit escapes. Fine for trusted-ish code.
- **gVisor** — a user-space kernel intercepting syscalls, so the real kernel is
  shielded. Stronger, some performance cost.
- **MicroVMs** (Firecracker) — a real VM with its own kernel, booting in
  milliseconds. Strongest practical option, and what serverless platforms use to
  run untrusted code.

Add **egress filtering** (what it can reach on the network) and **resource
caps** (CPU, memory, disk, time) on top of any of these.

**Where it applies to AURA.** Two surfaces, both serious:

- LLM-generated code executed with no review (A9).
- `subprocess.run(shell=True)` with model-authored commands (`shell.py:44`).

**The framing that matters — and this is the point to get right:** AURA's current
security model is *"it's your machine, your risk, gated for accidents not
adversaries."* That's defensible for a local tool you run on your own laptop.

It becomes **indefensible the moment it's hosted**, because you'd be running
LLM-generated code and arbitrary shell commands on *your* infrastructure on
behalf of other people. Multi-tenant AURA needs gVisor or Firecracker, egress
filtering and per-tenant caps **before it could responsibly accept one external
user**.

And the reason you didn't sandbox locally is not laziness — it's that sandboxing
removes the entire point. AURA needs your *real* desktop, your *real* logged-in
Chrome profile, your *real* Gmail token. A sandboxed AURA is a cloud coding
agent, which is the thing it exists to not be. Frame it as a deliberate trade
with a known boundary, not an oversight.

## B9. Observability

**What it is.** The ability to understand what a system did from its outputs —
crucially, *after the fact*, without reproducing the problem. Three pillars:

- **Logs** — discrete timestamped events. What happened.
- **Metrics** — aggregated numbers over time. How much, how often, how slow.
- **Traces** — one request's path through the system. Where the time went.

**Where it applies to AURA: everywhere, and this is your best "what next"
answer**, because it's cheap and it makes everything after it easier.

Right now there is **no logging at all**. Everything is `console.print` (Rich
markup, human-readable, ephemeral). If a user's run goes wrong there is no
artifact to inspect. And §A3's `except: pass` means some failures leave no trace
whatsoever.

Concretely for AURA:

- **Logs** — Python `logging` with a session-scoped file handler. Every tool
  call, arguments, result, duration. Registry import failures with the exception.
- **Metrics** — tokens per iteration, cost per task, iterations per task, tool
  success/failure rates, retry counts. You currently cannot answer "what did that
  task cost," and for something that loops 30 times, you should be able to.
- **Traces** — a trace id per session threading through planner → agent →
  dispatch, so one run is reconstructable end to end.

Note that you already have the *display* half solved — the Rich output in
`agent.py:257-330` makes a live run followable. What's missing is the durable
half. Framing it that way ("I built for watching, not for reviewing") is precise
and honest.

## B10. Idempotency

**What it is.** An operation is **idempotent** if doing it twice has the same
effect as doing it once. `DELETE /users/5` is idempotent (the user ends up
deleted either way). `POST /charge-card` is emphatically not.

**Why it matters, and why it matters *here*:** it's the property that makes
retries safe. If you retry a non-idempotent operation after a timeout, you may
do it twice — and you can't tell, because a timeout doesn't tell you whether the
request was processed before the connection dropped.

**Where it applies to AURA, sharply.** Your retry logic (A6) retries the **LLM
call**, which is safe — generating text twice costs money but breaks nothing.

But **tool calls are not retried**, and that's *correct*, because many of them
are aggressively non-idempotent:

| Tool | Idempotent? | Running it twice |
| --- | --- | --- |
| `read_file`, `list_dir`, `web_fetch` | Yes | Harmless |
| `write_file` | Yes-ish | Same content → same result |
| `gmail_send` | **No** | Two emails sent |
| `calendar_add_event` | **No** | Two calendar events |
| `meet_create` | **No** | Two meetings, two sets of invites |
| `desktop_click` | **No** | Two clicks — possibly two purchases |

There's a live example in `meet.py:168`:

```python
"requestId": f"aura-meet-{int(datetime.datetime.now().timestamp())}",
```

Google uses `requestId` as an **idempotency key** — send the same one twice and
Google dedupes rather than creating two conferences. But you generate it from
`now()`, so a retry produces a *different* key and Google would happily create a
second Meet. Using a stable key derived from the event content would make
`meet_create` genuinely retry-safe.

**What you'd say:** *"I retry the LLM call, not tool calls, and that's deliberate
— `gmail_send` and `calendar_add_event` aren't idempotent, so a retry means a
duplicate email or a duplicate event. If I wanted tool-level retries I'd need
idempotency keys. There's actually a near-miss in `meet.py` where Google gives me
one via `requestId` and I'm generating it from a timestamp, which defeats the
purpose."*

That's a strong close: it shows you understand the concept, know where it lives
in your code, and found a real bug with it.

---

## Quick glossary

| Term | One line |
| --- | --- |
| **Atomic** | Fully happens or doesn't; no observable halfway state |
| **Backoff** | Increasing delay between retries |
| **Context window** | Max tokens a model can consider in one request. A hard wall |
| **Centroid** | Geometric centre of a shape; how you turn a bounding box into a click point |
| **Deny-list / allow-list** | Enumerate the forbidden / enumerate the permitted. Allow-lists fail closed |
| **Defence in depth** | Multiple independent controls, so one failure isn't a breach |
| **Eventual consistency** | Replicas converge, but not instantly |
| **Fail-fast** | Recognise a hopeless case and surface it now |
| **Fail-open / fail-closed** | On error, allow through / block. Closed is safer |
| **Graceful degradation** | Reduced function instead of total failure |
| **Hard / soft dependency** | Failure stops the system / failure only degrades it |
| **HITL** | Human-in-the-loop — pause for approval before acting |
| **Idempotent** | Doing it twice equals doing it once. Makes retries safe |
| **Jitter** | Randomness in backoff, to stop synchronised retry storms |
| **Lazy initialisation** | Create the expensive thing on first use, not at startup |
| **Least privilege** | Request the narrowest permission that does the job |
| **RAG** | Retrieve relevant context at query time instead of prompting everything |
| **ReAct** | Reasoning + Acting interleaved in a loop |
| **Shard** | Split data across machines by key; each holds a different subset |
| **Singleton** | Exactly one shared instance |
| **Stale** | Cached data that no longer matches the truth |
| **Temperature** | Randomness dial on model output. Low = deterministic |
| **Thundering herd** | Many clients retrying in sync and re-crashing a recovering service |
| **Token** | Model's unit of text, ≈ ¾ of a word. What you pay and are limited by |
| **Write amplification** | Writing far more bytes than the logical change needs |
| **Write-through** | Persist on every change, rather than batching for later |
