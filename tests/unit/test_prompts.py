import pytest

from app.prompts import PROMPTS, get_prompt


@pytest.mark.unit
def test_all_prompts_have_required_fields():
    for prompt_id, p in PROMPTS.items():
        assert p.id == prompt_id
        assert p.version
        assert p.system
        assert p.user_template
        assert "{" in p.user_template  # has at least one placeholder


@pytest.mark.unit
def test_prompt_rendering():
    p = get_prompt("root_cause")
    rendered = p.render(issue="x", component="y", history="[]", evidence="z")
    assert "x" in rendered
    assert "y" in rendered
    assert "z" in rendered


@pytest.mark.unit
def test_unknown_prompt_raises():
    with pytest.raises(KeyError):
        get_prompt("nonexistent")
