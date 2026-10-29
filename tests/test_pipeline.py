from scripts.collect_gbif import license_allowed
from scripts.extract_tips import normalize_tip

def test_license_allowlist():
    assert license_allowed("https://creativecommons.org/licenses/by/4.0/")
    assert license_allowed("https://creativecommons.org/licenses/by-sa/4.0/")
    assert license_allowed("https://creativecommons.org/publicdomain/zero/1.0/")
    assert not license_allowed("https://creativecommons.org/licenses/by-nc/4.0/")
    assert not license_allowed("https://creativecommons.org/licenses/by-nd/4.0/")
    assert not license_allowed("")
    assert not license_allowed("All rights reserved")

def test_tip_requires_source():
    src={"url":"https://example.org/guide","title":"Guide","domain":"example.org","retrieved_at":"2026-10-29T00:00:00+00:00"}
    tip=normalize_tip({"title":"Keep water safe","category":"water","summary":"Follow current public health guidance." ,"steps":["Check official guidance"],"warnings":[],"confidence":"medium"},src,"test")
    assert tip and tip["verification"]["status"]=="needs_review"
    assert tip["sources"][0]["url"]==src["url"]
    assert "03-water-sanitation" in tip["stage_ids"]
    assert normalize_tip({"title":"No source"},{}, "test") is None
