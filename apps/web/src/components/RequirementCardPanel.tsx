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

function DimensionGroup({
  heading,
  children,
}: {
  heading: string;
  children: React.ReactNode;
}) {
  return (
    <div className="dimension-group">
      <h3 className="dimension-heading">{heading}</h3>
      <dl className="field-list">{children}</dl>
    </div>
  );
}

export function RequirementCardPanel({
  card,
  title = "Coding dimensions",
}: RequirementCardPanelProps) {
  const tech = card.technical_context;
  const task = card.core_task_scope;
  const io = card.inputs_outputs_contracts;
  const arch = card.architectural_rules;
  const edge = card.edge_cases_error_strategy;
  const fmt = card.response_formatting;

  return (
    <aside className="panel side-panel">
      <h2>{title}</h2>
      {card.unresolved_fields.length > 0 && (
        <div className="callout callout-warn">
          <strong>Unresolved</strong>
          <p>{card.unresolved_fields.join(", ")}</p>
        </div>
      )}

      <DimensionGroup heading="1. Technical Context">
        <FieldBlock label="Environment" value={tech.environment} />
        <ListBlock label="Integration points" items={tech.integration_points} />
        <FieldBlock label="Dependency policy" value={tech.dependency_policy} />
        <ListBlock label="Forbidden libraries" items={tech.forbidden_libraries} />
      </DimensionGroup>

      <DimensionGroup heading="2. Core Task & Scope">
        <FieldBlock label="Task type" value={task.task_type} />
        <FieldBlock label="Objective" value={task.objective} />
        <ListBlock label="Out of scope" items={task.out_of_scope} />
      </DimensionGroup>

      <DimensionGroup heading="3. Inputs, Outputs & Contracts">
        <FieldBlock label="Inputs" value={io.inputs} />
        <FieldBlock label="Output contract" value={io.output_contract} />
        <ListBlock label="Examples" items={io.examples} />
      </DimensionGroup>

      <DimensionGroup heading="4. Architectural Rules">
        <ListBlock label="Design patterns" items={arch.design_patterns} />
        <FieldBlock label="Coding style" value={arch.coding_style} />
        <ListBlock label="Non-functional" items={arch.non_functional} />
      </DimensionGroup>

      <DimensionGroup heading="5. Edge Cases & Errors">
        <FieldBlock label="Failure handling" value={edge.failure_handling} />
        <ListBlock label="Bad inputs" items={edge.bad_inputs} />
        <ListBlock label="Edge cases" items={edge.edge_cases} />
      </DimensionGroup>

      <DimensionGroup heading="6. Response Formatting">
        <FieldBlock label="Explanation level" value={fmt.explanation_level} />
        <FieldBlock label="Verbosity" value={fmt.verbosity} />
        <ListBlock label="Extra artifacts" items={fmt.extra_artifacts} />
      </DimensionGroup>
    </aside>
  );
}
