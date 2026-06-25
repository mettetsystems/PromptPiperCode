import type { RegistryPromptSummary } from "../api/types";

export function matchesRegistryKeyword(prompt: RegistryPromptSummary, query: string): boolean {
  const terms = query
    .trim()
    .toLowerCase()
    .split(/\s+/)
    .filter(Boolean);
  if (terms.length === 0) {
    return true;
  }
  const haystack = [
    prompt.title,
    prompt.prompt_id,
    prompt.abstract,
    prompt.output_form,
    ...prompt.tags,
  ]
    .join(" ")
    .toLowerCase();
  return terms.every((term) => haystack.includes(term));
}

export function filterRegistryPrompts(
  prompts: RegistryPromptSummary[],
  query: string,
): RegistryPromptSummary[] {
  return prompts.filter((prompt) => matchesRegistryKeyword(prompt, query));
}
