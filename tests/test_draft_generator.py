from prompt_piper_api.domain.requirement_card import RequirementCard
from prompt_piper_api.services.draft_generator import DraftGenerator


def test_missing_fields_are_marked_unspecified() -> None:
    card = RequirementCard(objective="Summarize incident reports")
    result = DraftGenerator(llm=None).generate(card)

    assert "audience" in result.unresolved_fields
    assert "Audience: unspecified" in result.body
    assert "desired_output_shape" in result.unresolved_fields
    assert result.unspecified_note.startswith("Still unspecified:")


def test_prompt_includes_objective_and_output_shape_when_known() -> None:
    card = RequirementCard(
        objective="Draft a weekly status update",
        desired_output_shape="Bulleted summary with risks and next steps",
    )
    result = DraftGenerator(llm=None).generate(card)

    assert "Draft a weekly status update" in result.body
    assert "Bulleted summary with risks and next steps" in result.body
    assert "Mission" in result.body
    assert "Output contract" in result.body
    assert "desired_output_shape" not in result.unresolved_fields


def test_no_hallucinated_audience() -> None:
    card = RequirementCard(
        objective="Create a product changelog prompt",
        desired_output_shape="Short release notes",
    )
    result = DraftGenerator(llm=None).generate(card)

    assert "Audience: unspecified" in result.body
    assert "engineering team" not in result.body.lower()
    assert "executive stakeholders" not in result.body.lower()


def test_forbidden_actions_included_when_present() -> None:
    card = RequirementCard(
        objective="Summarize legal documents",
        forbidden_content_actions=["provide legal advice", "invent case citations"],
    )
    result = DraftGenerator(llm=None).generate(card)

    assert "Forbidden content or actions" in result.body
    assert "Do not provide legal advice" in result.body
    assert "Do not invent case citations" in result.body


def test_forbidden_section_omitted_when_not_specified() -> None:
    card = RequirementCard(objective="Write meeting notes")
    result = DraftGenerator(llm=None).generate(card)

    assert "Forbidden content or actions" not in result.body


def test_output_is_plain_text_without_markdown_or_xml() -> None:
    card = RequirementCard(
        objective="Extract action items",
        audience="project managers",
        desired_output_shape="Numbered list",
        success_criteria=["Every action has an owner"],
        tone_style="concise and direct",
        constraints=["Keep responses concise"],
    )
    result = DraftGenerator(llm=None).generate(card)

    assert result.body
    assert "# " not in result.body
    assert "<prompt" not in result.body.lower()
    assert "<" not in result.body
    assert "Mission" in result.body
    assert "Context" in result.body
    assert "Constraints" in result.body
    assert "Style" in result.body
    assert "Acceptance criteria" in result.body
    assert "Meet this criterion: Every action has an owner" in result.body


def test_constraints_use_positive_instruction_phrasing_when_possible() -> None:
    card = RequirementCard(
        objective="Write FAQ answers",
        constraints=["do not exceed 200 words"],
    )
    result = DraftGenerator(llm=None).generate(card)

    assert "Keep the response within 200 words" in result.body


def test_generate_body_returns_only_text() -> None:
    card = RequirementCard(objective="Help draft support macros")
    body = DraftGenerator(llm=None).generate_body(card)

    assert isinstance(body, str)
    assert "Mission" in body
