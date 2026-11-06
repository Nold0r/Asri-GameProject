"""Deterministic implementation of the narrative-design skill's checkable rules.

The skill is prose, so we encode only its concrete, checkable parts:
  * Required document structure (sections/fields/headings).
  * Critical rules as validators (choice kinds, lore optional, gameplay link,
    "as you know" ban, real-person line test via explicit tags).
  * Branch-graph checks: every choice leads somewhere, every flag read is set.
  * Consequence window: every choice has an observable consequence within 2 scenes.
  * Routing: which prompts fire this skill vs. others.
  * Output file naming.

Content judgement (does a line "sound like a character"?) is NOT parsed from
prose. Fixtures carry explicit tags/fields (e.g. ``line_ok``, ``choice_kind``,
``consequence_scene``) and we validate those. See comments below.
"""

import re

# --- Required structure -----------------------------------------------------

REQUIRED_SECTIONS = ["characters", "beats", "choices", "lore"]
REQUIRED_BEAT_FIELDS = ["id", "summary", "gameplay_consequence"]
REQUIRED_CHOICE_FIELDS = ["id", "from_beat", "to_beat", "kind", "consequence_scene"]
LORE_TIERS = {"tier1", "tier2", "tier3"}
CRITICAL_LORE_TIER = "tier1"

# Consequence must be observable within this many scenes of the choice.
CONSEQUENCE_WINDOW = 2

# "as you know" style exposition ban (case-insensitive).
AS_YOU_KNOW = re.compile(r"\bas you know\b", re.IGNORECASE)


def missing_sections(doc):
    """Return required top-level sections absent from the doc."""
    return [s for s in REQUIRED_SECTIONS if s not in doc]


def missing_beat_fields(doc):
    """Return list of (beat_id, missing_field) for beats lacking required fields."""
    out = []
    for beat in doc.get("beats", []):
        for f in REQUIRED_BEAT_FIELDS:
            if f not in beat or beat[f] in (None, ""):
                out.append((beat.get("id", "?"), f))
    return out


def missing_choice_fields(doc):
    out = []
    for ch in doc.get("choices", []):
        for f in REQUIRED_CHOICE_FIELDS:
            if f not in ch or ch[f] in (None, ""):
                out.append((ch.get("id", "?"), f))
    return out


# --- Critical rules ---------------------------------------------------------

def choices_differ_in_kind(doc):
    """Choices from the same beat must differ in ``kind``, not just degree.

    ``kind`` is an explicit tag in the fixture (e.g. "mercy" vs "pragmatic").
    Two choices from one beat sharing a kind is a 'degree' violation.
    """
    by_beat = {}
    for ch in doc.get("choices", []):
        by_beat.setdefault(ch.get("from_beat"), []).append(ch.get("kind"))
    for beat, kinds in by_beat.items():
        if len(kinds) != len(set(kinds)):
            return False, beat
    return True, None


def lore_is_optional(doc):
    """Critical path must be comprehensible without Tier 2/3 lore.

    Rule: every beat reachable on the critical path must not *require* a
    non-critical lore entry. Fixtures mark ``requires_lore`` on beats.
    """
    for beat in doc.get("beats", []):
        if beat.get("on_critical_path") and beat.get("requires_lore"):
            tier = beat["requires_lore"]
            if tier in LORE_TIERS and tier != CRITICAL_LORE_TIER:
                return False, beat.get("id")
    return True, None


def every_beat_has_gameplay_consequence(doc):
    """Every major story beat must connect to a gameplay consequence."""
    bad = [b.get("id") for b in doc.get("beats", [])
           if not b.get("gameplay_consequence")]
    return (not bad), bad


def no_as_you_know(doc):
    """Reject any dialogue line containing 'as you know' exposition."""
    for line in doc.get("lines", []):
        if AS_YOU_KNOW.search(line.get("text", "")):
            return False, line.get("id")
    return True, None


def lines_pass_real_person_test(doc):
    """Every line must pass the 'would a real person say this?' test.

    We cannot judge prose; fixtures carry an explicit boolean ``line_ok``
    produced by the author/agent. Any ``line_ok is False`` fails.
    """
    bad = [l.get("id") for l in doc.get("lines", []) if l.get("line_ok") is False]
    return (not bad), bad


# --- Branch graph -----------------------------------------------------------

def build_graph(doc):
    """Return (beat_ids, edges) where edges are (from_beat, to_beat)."""
    beats = {b.get("id") for b in doc.get("beats", [])}
    edges = [(c.get("from_beat"), c.get("to_beat")) for c in doc.get("choices", [])]
    return beats, edges


def every_choice_leads_somewhere(doc):
    """Every choice's from_beat and to_beat must be a declared beat."""
    beats, edges = build_graph(doc)
    bad = []
    for frm, to in edges:
        if frm not in beats:
            bad.append(("from", frm))
        if to not in beats:
            bad.append(("to", to))
    return (not bad), bad


def every_flag_read_is_set(doc):
    """Every flag read (``reads``) must be set (``sets``) somewhere."""
    set_flags = set()
    for b in doc.get("beats", []):
        set_flags.update(b.get("sets", []))
    for c in doc.get("choices", []):
        set_flags.update(c.get("sets", []))
    read_flags = set()
    for b in doc.get("beats", []):
        read_flags.update(b.get("reads", []))
    for c in doc.get("choices", []):
        read_flags.update(c.get("reads", []))
    unset = sorted(read_flags - set_flags)
    return (not unset), unset


def consequences_within_window(doc):
    """All branching choices produce observable consequences within 2 scenes.

    ``consequence_scene`` is the scene index where the consequence is visible;
    ``choice_scene`` is where the choice is made. Delta must be <= 2.
    """
    bad = []
    for c in doc.get("choices", []):
        cs = c.get("choice_scene")
        cons = c.get("consequence_scene")
        if cs is None or cons is None:
            bad.append((c.get("id"), "missing_scene"))
        elif cons - cs > CONSEQUENCE_WINDOW or cons < cs:
            bad.append((c.get("id"), cons - cs))
    return (not bad), bad


# --- Routing ----------------------------------------------------------------

ROUTING_FIRE = [
    "branching dialogue", "character backstor", "worldbuilding lore",
    "non-linear narrative", "quest log", "lore collectible",
    "narrative story reveal", "player choice", "companion relationship",
]
ROUTING_OTHER = {
    "novel": "book-writing",
    "manuscript": "book-writing",
    "screenplay": "screenwriting",
    "film": "screenwriting",
    "combat balance": "game-design",
    "gameplay rules": "game-design",
}


def route(prompt):
    """Return 'narrative-design' or the other skill name."""
    p = prompt.lower()
    for key, other in ROUTING_OTHER.items():
        if key in p:
            return other
    for key in ROUTING_FIRE:
        if key in p:
            return "narrative-design"
    return "narrative-design"  # default: this skill's own domain


# --- Output naming ----------------------------------------------------------

def output_path(game_slug, doc_kind):
    """File path the skill asks to write, e.g. docs/narrative/<slug>_<kind>.md."""
    return f"docs/narrative/{game_slug}_{doc_kind}.md"


# --- Aggregate verdict ------------------------------------------------------

def validate(doc):
    """Run all rules; return (ok, list_of_failures)."""
    failures = []
    if missing_sections(doc):
        failures.append(("missing_sections", missing_sections(doc)))
    if missing_beat_fields(doc):
        failures.append(("missing_beat_fields", missing_beat_fields(doc)))
    if missing_choice_fields(doc):
        failures.append(("missing_choice_fields", missing_choice_fields(doc)))
    ok, beat = choices_differ_in_kind(doc)
    if not ok:
        failures.append(("choices_same_kind", beat))
    ok, beat = lore_is_optional(doc)
    if not ok:
        failures.append(("lore_required_on_critical_path", beat))
    ok, bad = every_beat_has_gameplay_consequence(doc)
    if not ok:
        failures.append(("beat_without_gameplay_consequence", bad))
    ok, lid = no_as_you_know(doc)
    if not ok:
        failures.append(("as_you_know", lid))
    ok, bad = lines_pass_real_person_test(doc)
    if not ok:
        failures.append(("line_fails_real_person_test", bad))
    ok, bad = every_choice_leads_somewhere(doc)
    if not ok:
        failures.append(("choice_leads_nowhere", bad))
    ok, bad = every_flag_read_is_set(doc)
    if not ok:
        failures.append(("flag_read_never_set", bad))
    ok, bad = consequences_within_window(doc)
    if not ok:
        failures.append(("consequence_outside_window", bad))
    return (not failures), failures
