from prompt_piper_api.domain.requirement_card import RequirementCard
from prompt_piper_api.services.draft_generator import DraftGenerator


def test_missing_fields_are_marked_unspecified() -> None:
    card = RequirementCard(core_task_scope={"objective": "Add FastAPI user create endpoint"})
    result = DraftGenerator(llm=None).generate(card)

    assert "technical_context.environment" in result.unresolved_fields
    assert "Environment: unspecified" in result.body
    assert "inputs_outputs_contracts.output_contract" in result.unresolved_fields
    assert result.unspecified_note.startswith("Still unspecified:")


def test_prompt_includes_objective_and_output_shape_when_known() -> None:
    card = RequirementCard(
        core_task_scope={"objective": "Add a weekly status summary endpoint"},
        inputs_outputs_contracts={
            "output_contract": "JSON list of risk objects with owner and severity",
        },
    )
    result = DraftGenerator(llm=None).generate(card)

    assert "Add a weekly status summary endpoint" in result.body
    assert "JSON list of risk objects with owner and severity" in result.body
    assert "Core Task and Scope" in result.body
    assert "Inputs, Outputs, and Contracts" in result.body
    assert "inputs_outputs_contracts.output_contract" not in result.unresolved_fields


def test_no_hallucinated_environment() -> None:
    card = RequirementCard(
        core_task_scope={"objective": "Create a product changelog generator"},
        inputs_outputs_contracts={"output_contract": "Markdown release notes string"},
    )
    result = DraftGenerator(llm=None).generate(card)

    assert "Environment: unspecified" in result.body
    assert "engineering team" not in result.body.lower()
    assert "executive stakeholders" not in result.body.lower()


def test_forbidden_libraries_included_when_present() -> None:
    card = RequirementCard(
        core_task_scope={
            "objective": "Parse legal document text",
            "out_of_scope": ["provide legal advice", "invent case citations"],
        },
        technical_context={"forbidden_libraries": ["openai", "langchain"]},
    )
    result = DraftGenerator(llm=None).generate(card)

    assert "Out of scope" in result.body
    assert "provide legal advice" in result.body
    assert "invent case citations" in result.body
    assert "Forbidden libraries: openai; langchain" in result.body


def test_forbidden_libraries_unspecified_when_empty() -> None:
    card = RequirementCard(core_task_scope={"objective": "Write meeting notes exporter"})
    result = DraftGenerator(llm=None).generate(card)

    assert "Forbidden libraries: unspecified" in result.body


def test_output_is_plain_text_without_markdown_or_xml() -> None:
    card = RequirementCard(
        core_task_scope={"objective": "Extract action items from issue comments"},
        technical_context={"environment": "Python 3.12"},
        inputs_outputs_contracts={"output_contract": "Numbered list of action objects"},
        architectural_rules={
            "coding_style": "concise and direct",
            "non_functional": ["Every action has an owner", "Keep responses concise"],
        },
        response_formatting={"explanation_level": "brief rationale then code"},
    )
    result = DraftGenerator(llm=None).generate(card)

    assert result.body
    assert "# " not in result.body
    assert "<prompt" not in result.body.lower()
    assert "<" not in result.body
    assert "Technical Context" in result.body
    assert "Core Task and Scope" in result.body
    assert "Architectural Rules and Constraints" in result.body
    assert "Response Formatting" in result.body
    assert "Edge Cases and Error Strategy" in result.body
    assert "Every action has an owner" in result.body


def test_constraints_use_positive_instruction_phrasing_when_possible() -> None:
    card = RequirementCard(
        core_task_scope={"objective": "Write FAQ answer generator"},
        architectural_rules={"non_functional": ["do not exceed 200 words"]},
    )
    result = DraftGenerator(llm=None).generate(card)

    assert "Keep the response within 200 words" in result.body


def test_generate_body_returns_only_text() -> None:
    card = RequirementCard(core_task_scope={"objective": "Help draft support macros"})
    body = DraftGenerator(llm=None).generate_body(card)

    assert isinstance(body, str)
    assert "Core Task and Scope" in body
