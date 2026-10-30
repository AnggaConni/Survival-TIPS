from scripts.source_quality import evidence_matches, possible_conflict_pairs


def test_evidence_match_accepts_omitted_text_marked_by_ellipsis():
    source = "First supported sentence appears here. Intervening material. A second supported sentence appears here."
    excerpt = "First supported sentence appears here...A second supported sentence appears here."
    assert evidence_matches(excerpt, source)


def test_evidence_match_normalizes_unicode_and_whitespace():
    source = "Minimum 3.5m2 of covered living space per person."
    excerpt = "Minimum 3.5m² of covered living space per person."
    assert evidence_matches(excerpt, source)


def test_evidence_match_rejects_unsubstantiated_excerpt():
    assert not evidence_matches("Boiling removes every chemical.", "Boil water before drinking.")


def test_conflict_screen_does_not_treat_generic_use_avoid_as_contradiction():
    tips = [
        {"id": "a", "title": "Translate messages through community partners",
         "summary": "Use professional translation services and avoid online dictionaries.",
         "steps": ["Use community partners."]},
        {"id": "b", "title": "Use abbreviated messages for space-limited channels",
         "summary": "Use short messages for text systems and social media.",
         "steps": ["Use concise wording."]},
    ]
    assert possible_conflict_pairs(tips) == []


def test_conflict_screen_compares_numeric_values_only_with_matching_units():
    different_dimensions = [
        {"id": "a", "title": "Minimum shelter covered floor space",
         "summary": "Minimum shelter floor space is 3.5 m2 per person.",
         "steps": ["Provide covered living space."]},
        {"id": "b", "title": "Minimum shelter height",
         "summary": "Minimum shelter height is 2 m at the lowest point.",
         "steps": ["Measure the lowest point."]},
    ]
    assert possible_conflict_pairs(different_dimensions) == []

    same_dimension = [
        {"id": "c", "title": "Minimum emergency water storage",
         "summary": "Minimum water storage is 10 litres per person.",
         "steps": ["Store drinking water."]},
        {"id": "d", "title": "Minimum emergency water storage",
         "summary": "Minimum water storage is 5 litres per person.",
         "steps": ["Store drinking water."]},
    ]
    pairs = possible_conflict_pairs(same_dimension)
    assert len(pairs) == 1
    assert "different_numeric_values" in pairs[0]["signals"]
