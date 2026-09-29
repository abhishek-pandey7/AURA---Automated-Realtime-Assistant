# prep/ — Interview Prep Pack for AURA

Everything in this folder was written by reading the actual source in `aura/`, not
from a template. Every claim points at a file. Where the code couldn't tell me
*why* a decision was made, it says **[confirm with me]** instead of inventing a
motive — go fill those in before you walk into a room, because those are exactly
the spots an interviewer will press on.

## What's here

| File | What it's for | When to read it |
| --- | --- | --- |
| [INTERVIEW_PREP.md](INTERVIEW_PREP.md) | The main deck. Pitch, design concepts, stack defence, scaling story, weak spots, 15 Q&A. | The night before. Read it out loud. |
| [CONCEPTS_EXPLAINED.md](CONCEPTS_EXPLAINED.md) | Every concept named in the main doc, taught from scratch and then tied back to the exact lines in your repo. | First, if any term in the main doc feels like a word you're repeating rather than a thing you understand. |

## How to actually use this

1. **Read CONCEPTS_EXPLAINED.md first.** The main doc says "you used a plugin
   registry." That file explains what a plugin registry *is*, why anyone wants
   one, and shows you the 30 lines of `aura/tools/__init__.py` that are yours.
   You can't defend a term you can only recite.
2. **Then INTERVIEW_PREP.md, out loud, on a timer.** 60 seconds for the short
   pitch, 3 minutes for the long one. If you run over, cut adjectives, not facts.
3. **Hunt the `[confirm with me]` markers.** Search the folder for that string.
   Each one is a decision only you know the reason for. Write the real answer in.
   A guessed reason falls apart on the first follow-up; "I picked it because X"
   with a real X doesn't.
4. **Read the weak-spots section last, and don't flinch at it.** Section 5 of the
   main doc lists the things that are genuinely wrong or fragile in this
   codebase. Knowing them and naming them first is worth far more than hoping
   nobody looks. The hardcoded Windows path in `aura/tools/browser.py:85` will be
   found. Get there before they do.

## One honest framing note

AURA is a **single-user local CLI agent**, not a web service. There's no server,
no database, no load balancer, and no requests-per-second. If someone asks "how
does this handle 100x traffic," the correct answer is not to invent a Redis
cache — it's to say that the scaling axes here are *different* (tokens and
iterations per task, tool-count in the prompt, session-file growth, concurrent
desktop sessions if hosted) and then talk about those precisely. Section 4 of the
main doc does that. Don't let anyone talk you into defending an architecture you
didn't build.
