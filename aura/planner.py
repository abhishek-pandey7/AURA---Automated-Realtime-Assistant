import json
import os
from openai import OpenAI
from aura.config import INFERX_BASE_URL, INFERX_API_KEY, INFERX_MODEL

_client = OpenAI(base_url=INFERX_BASE_URL, api_key=INFERX_API_KEY)

PLANNER_SYSTEM = """You are a task planner for AURA, an autonomous CLI agent.
The user gives you a goal. You must break it into a clear list of concrete subtasks.

Rules:
- Return ONLY valid JSON, no explanation, no markdown fences.
- Format: {"tasks": ["step 1", "step 2", ...]}
- Each task should be one clear, actionable step.
- Maximum 10 tasks. If the goal is simple, use fewer.
- Tasks should be ordered so each builds on the previous.
- Be specific — bad: "set up project", good: "create a directory called myapp with app.py and requirements.txt"
"""


def plan(goal: str, cwd: str) -> list[str]:
    """
    Takes a user goal, returns an ordered list of subtask strings.
    Falls back to treating the goal as a single task if LLM fails.
    """
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
