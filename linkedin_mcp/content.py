"""
Content strategy helpers — the *safe* way to grow a profile: a steady stream of
strong posts, not engagement bots.

These functions don't call any AI themselves; they return structured briefs and
proven post templates that the assistant using this MCP (or you) fills in with
real substance. That keeps the tool dependency-free and puts the quality where
it belongs — in genuine, specific content.
"""

from __future__ import annotations

# Post archetypes that reliably perform on LinkedIn for a builder/engineer.
TEMPLATES: dict[str, dict[str, str]] = {
    "build_in_public": {
        "when": "You shipped or improved something.",
        "shape": "Hook (the result) → what you built → one hard problem you hit → how you solved it → what you'd tell someone starting. End with a soft question.",
        "example_hook": "I shipped an open-source X this week. Here's the one bug that almost killed it.",
    },
    "lesson": {
        "when": "You learned something the hard way.",
        "shape": "A short story of a mistake → the cost → the lesson → how you apply it now. Concrete, no platitudes.",
        "example_hook": "A cleanup routine I wrote deleted live data. Here's what it taught me about automation.",
    },
    "teardown": {
        "when": "You can explain how something works clearly.",
        "shape": "Pick one concept (e.g. prompt injection, PDF from HTML) → explain it simply → show a tiny concrete example → why it matters.",
        "example_hook": "Most 'AI security' tools are grep with extra steps. Here's what actually catches prompt injection.",
    },
    "opinion": {
        "when": "You have a considered take.",
        "shape": "State the take plainly → why the common view is incomplete → your reasoning with a concrete example → invite disagreement.",
        "example_hook": "Hiring another person won't fix your ops. Here's the math.",
    },
    "result": {
        "when": "You have a verifiable number.",
        "shape": "The number up top → what it measures → how you got it → what it means for the reader.",
        "example_hook": "One command, a 617-item catalog, filtering in 0 ms. How the client's price list stopped being a spreadsheet.",
    },
}

# A simple weekly cadence that grows a profile without spamming.
DEFAULT_CADENCE = [
    ("Mon", "build_in_public"),
    ("Wed", "teardown"),
    ("Fri", "lesson"),
]

RULES = [
    "Write like you talk. One idea per post.",
    "First line is the whole game — it's all most people see. Make it a hook, not a preamble.",
    "Be specific: real numbers, real files, real mistakes. Vague = ignored.",
    "Short lines and white space. No walls of text.",
    "3–5 relevant hashtags max, at the end.",
    "End with a genuine question to invite comments — real engagement, not bait.",
    "Post consistently (2–3x/week) — consistency beats volume.",
    "Never buy followers or use engagement bots — it risks a ban and hollow reach.",
]


def brief(topic: str, archetype: str = "build_in_public") -> dict:
    """Return a structured brief the assistant fills with real content."""
    t = TEMPLATES.get(archetype, TEMPLATES["build_in_public"])
    return {
        "topic": topic,
        "archetype": archetype,
        "use_when": t["when"],
        "structure": t["shape"],
        "example_hook": t["example_hook"],
        "rules": RULES,
    }


def calendar() -> dict:
    return {
        "cadence": [{"day": d, "archetype": a, "focus": TEMPLATES[a]["when"]}
                    for d, a in DEFAULT_CADENCE],
        "archetypes": list(TEMPLATES.keys()),
        "rules": RULES,
    }
