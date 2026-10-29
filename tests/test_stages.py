from scripts.stages import classify_tip, get_stages, tips_for_stage

def test_stage_catalog_and_filter():
    stages = get_stages()
    assert len(stages) >= 8
    assert len({stage["id"] for stage in stages}) == len(stages)
    tip = {"title": "How to purify drinking water", "summary": "Boil water following official guidance.", "category": "water"}
    assigned = classify_tip(tip)
    assert "03-water-sanitation" in assigned
    assert tip in tips_for_stage([tip], "03-water-sanitation")
    assert tip not in tips_for_stage([tip], "05-energy")

def test_explicit_stage_assignment_wins():
    tip = {"title": "A general guide", "summary": "General information", "category": "other", "stage_ids": ["05-energy"]}
    assert classify_tip(tip) == ["05-energy"]
