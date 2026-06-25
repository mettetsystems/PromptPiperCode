import type { RequirementCard } from "../api/types";

interface RequirementCardPanelProps {
  card: RequirementCard;
  title?: string;
}

function FieldBlock({ label, value }: { label: string; value: string | undefined }) {
  if (!value?.trim()) {
    return null;
  }
  return (
    <div className="field-block">
      <dt>{label}</dt>
      <dd>{value}</dd>
    </div>
  );
}

function ListBlock({ label, items }: { label: string; items: string[] | undefined }) {
  if (!items || items.length === 0) {
    return null;
  }
  return (
    <div className="field-block">
      <dt>{label}</dt>
      <dd>
        <ul className="compact-list">
          {items.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
      </dd>
    </div>
  );
}

export function RequirementCardPanel({
  card,
  title = "Requirement card",
}: RequirementCardPanelProps) {
  return (
    <aside className="panel side-panel">
      <h2>{title}</h2>
      {card.unresolved_fields.length > 0 && (
        <div className="callout callout-warn">
          <strong>Unresolved</strong>
          <p>{card.unresolved_fields.join(", ")}</p>
        </div>
      )}
      <dl className="field-list">
        <FieldBlock label="Objective" value={card.objective} />
        <FieldBlock label="Background" value={card.context_background} />
        <FieldBlock label="Audience" value={card.audience} />
        <FieldBlock label="Persona / role" value={card.persona_role} />
        <FieldBlock label="Output shape" value={card.desired_output_shape} />
        <FieldBlock label="Tone / style" value={card.tone_style} />
        <FieldBlock label="Verbosity" value={card.verbosity} />
        <FieldBlock label="Language" value={card.language} />
        <ListBlock label="Constraints" items={card.constraints} />
        <ListBlock label="Success criteria" items={card.success_criteria} />
        <ListBlock label="Forbidden" items={card.forbidden_content_actions} />
        <ListBlock label="Edge cases" items={card.edge_cases} />
        <ListBlock label="Input materials" items={card.input_materials} />
        <ListBlock label="Example outputs" items={card.example_outputs} />
      </dl>
    </aside>
  );
}
