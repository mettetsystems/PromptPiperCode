const UNSPECIFIED = "unspecified";

/** Combine toggled quick replies and optional custom text for one API answer. */
export function buildClarificationAnswer(
  selected: readonly string[],
  custom: string,
): string | null {
  const trimmedCustom = custom.trim();
  const normalized = selected.map((item) => item.trim()).filter(Boolean);

  if (normalized.includes(UNSPECIFIED)) {
    return UNSPECIFIED;
  }

  const parts = [...normalized];
  if (trimmedCustom) {
    parts.push(trimmedCustom);
  }

  if (parts.length === 0) {
    return null;
  }

  return parts.join("; ");
}

export function toggleClarificationOption(
  selected: readonly string[],
  option: string,
): string[] {
  const normalized = option.trim();
  if (!normalized) {
    return [...selected];
  }

  if (normalized === UNSPECIFIED) {
    return selected.includes(UNSPECIFIED) ? [] : [UNSPECIFIED];
  }

  const withoutUnspecified = selected.filter((item) => item !== UNSPECIFIED);
  if (withoutUnspecified.includes(normalized)) {
    return withoutUnspecified.filter((item) => item !== normalized);
  }
  return [...withoutUnspecified, normalized];
}
