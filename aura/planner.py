import json
import os
import time
import httpx
from openai import OpenAI
from aura.config import INFERX_BASE_URL, INFERX_API_KEY, INFERX_MODEL

_client = OpenAI(
    base_url=INFERX_BASE_URL,
    api_key=INFERX_API_KEY,
    timeout=httpx.Timeout(timeout=120.0, connect=15.0),
)

PLANNER_SYSTEM = """You are a task planner for AURA, an autonomous CLI agent.
The user gives you a goal. You must break it into a clear list of concrete subtasks.

AURA has these built-in tools — plan around them, do NOT plan "install library" or "write script" steps for these:
- gmail_send: send emails via Gmail OAuth2 (already configured, no setup needed)
- gmail_read_inbox: read emails from Gmail
- calendar_add_event / calendar_list_events / calendar_delete_event: Google Calendar (already configured)
- meet_create: create a Google Meet video call + calendar event, email the link to people (one tool call, no browser needed)
- forms_load_profile: load user's personal data (name, email, phone, college, etc.) for form filling
- forms_update_profile: save a field to user's personal profile
- forms_generate_prefill_url: generate a pre-filled Google Forms URL
- bash, read_file, write_file, web_search, web_fetch, desktop_*: everything else

Rules:
- Return ONLY valid JSON, no explanation, no markdown fences.
- Format: {"tasks": ["step 1", "step 2", ...]}
- Each task should be one clear, actionable step.
- Maximum 10 tasks. If the goal is simple, use 1 task.
- For email/calendar tasks: 1 task — built-in tools handle it directly.
- For Meet tasks: 1 task — meet_create does everything (Meet link + calendar + email) in one call.
- For form-filling tasks: 2 tasks max — (1) load profile, (2) fill and submit the form.
- Tasks should be ordered so each builds on the previous.
- Be specific — bad: "set up project", good: "create a directory called myapp with app.py and requirements.txt"
"""


def plan(goal: str, cwd: str) -> list[str]:
    """
    Takes a user goal, returns an ordered list of subtask strings.
    Falls back to treating the goal as a single task if LLM fails.
    """
    try:
        for attempt in range(3):
            try:
                response = _client.chat.completions.create(
                    model=INFERX_MODEL,
                    max_tokens=512,
                    messages=[
                        {"role": "system", "content": PLANNER_SYSTEM},
                        {"role": "user", "content": f"Working directory: {cwd}\n\nGoal: {goal}"},
                    ],
                    temperature=0.2,
                )
                break  # success
            except Exception as e:
                err_str = str(e).lower()
                is_retryable = (
                    "502" in err_str or "500" in err_str or "503" in err_str
                    or "timed out" in err_str or "timeout" in err_str
                    or "connection" in err_str
                )
                if is_retryable and attempt < 2:
                    wait = (attempt + 1) * 5
                    time.sleep(wait)
                    continue
                raise  # non-retryable or exhausted retries
        raw = response.choices[0].message.content.strip()

        # Strip markdown fences if model added them anyway
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
            raw = raw.strip()

        data = json.loads(raw)
        tasks = data.get("tasks", [])
        if tasks and isinstance(tasks, list):
            return [str(t) for t in tasks]

    except Exception:
        pass

    # Fallback — treat whole goal as one task
    return [goal]
