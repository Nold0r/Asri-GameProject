import os
import sys

HERE = os.path.dirname(__file__)
EXAMPLES = os.path.dirname(HERE)
sys.path.insert(0, EXAMPLES)

import json
import narrative as N

FIX = os.path.join(EXAMPLES, "fixtures")


def load(name):
    with open(os.path.join(FIX, name), encoding="utf-8") as f:
        return json.load(f)


passed = 0
total = 0


def check(name, cond, detail=""):
    global passed, total
    total += 1
    if cond:
        passed += 1
        print(f"PASS {name}")
    else:
        print(f"FAIL {name}: {detail}")


good = load("good_lantern_moth.json")
bad_kind = load("bad_same_kind.json")
bad_flag = load("bad_flag_unset.json")
bad_lore = load("bad_lore_required.json")
bad_ayk = load("bad_as_you_know.json")

# Required structure
check("required_sections_present", N.missing_sections(good) == [],
      N.missing_sections(good))
check("missing_section_detected",
      N.missing_sections({"characters": [], "beats": []}) == ["choices", "lore"],
      N.missing_sections({"characters": [], "beats": []}))
check("beat_fields_complete", N.missing_beat_fields(good) == [],
      N.missing_beat_fields(good))
check("choice_fields_complete", N.missing_choice_fields(good) == [],
      N.missing_choice_fields(good))

# Critical rules
check("choices_differ_in_kind_good", N.choices_differ_in_kind(good)[0])
check("choices_same_kind_rejected", not N.choices_differ_in_kind(bad_kind)[0],
      N.choices_differ_in_kind(bad_kind))
check("lore_optional_good", N.lore_is_optional(good)[0])
check("lore_required_on_critical_path_rejected",
      not N.lore_is_optional(bad_lore)[0], N.lore_is_optional(bad_lore))
check("every_beat_has_gameplay_consequence",
      N.every_beat_has_gameplay_consequence(good)[0])
check("as_you_know_rejected", not N.no_as_you_know(bad_ayk)[0],
      N.no_as_you_know(bad_ayk))
check("real_person_test_good", N.lines_pass_real_person_test(good)[0])

# Branch graph
check("every_choice_leads_somewhere_good",
      N.every_choice_leads_somewhere(good)[0])
check("choice_leads_nowhere_rejected",
      not N.every_choice_leads_somewhere(
          {"beats": [{"id": "b1"}],
           "choices": [{"id": "c1", "from_beat": "b1", "to_beat": "bX"}]})[0])
check("flag_read_is_set_good", N.every_flag_read_is_set(good)[0])
check("flag_read_never_set_rejected", not N.every_flag_read_is_set(bad_flag)[0],
      N.every_flag_read_is_set(bad_flag))
check("consequence_within_window_good",
      N.consequences_within_window(good)[0])
check("consequence_outside_window_rejected",
      not N.consequences_within_window(
          {"choices": [{"id": "c1", "choice_scene": 1,
                        "consequence_scene": 5}]})[0])

# Routing
check("route_branching_dialogue",
      N.route("write branching dialogue trees with player choice") == "narrative-design")
check("route_novel_to_book_writing",
      N.route("write a book manuscript or novel chapter") == "book-writing")
check("route_combat_to_game_design",
      N.route("design core gameplay rules and combat balance curves") == "game-design")

# Output naming
check("output_path_format",
      N.output_path("lantern_moth", "dialogue") ==
      "docs/narrative/lantern_moth_dialogue.md")

# Aggregate verdicts
check("good_doc_validates", N.validate(good)[0], N.validate(good)[1])
check("bad_same_kind_invalid", not N.validate(bad_kind)[0])
check("bad_flag_invalid", not N.validate(bad_flag)[0])
check("bad_lore_invalid", not N.validate(bad_lore)[0])
check("bad_as_you_know_invalid", not N.validate(bad_ayk)[0])

print(f"RESULT {passed}/{total}")
if passed != total:
    sys.exit(1)
