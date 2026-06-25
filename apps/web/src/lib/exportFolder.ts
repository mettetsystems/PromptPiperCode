/** Mirror backend safe_export_slug for export folder previews. */
export function safeExportSlug(title: string, fallback = "export"): string {
  const cleaned = title
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "");
  const slug = cleaned.slice(0, 64).replace(/^-+|-+$/g, "");
  return slug || fallback;
}

export function buildExportFolderPreview(label: string, now = new Date()): string {
  const stamp = now.toISOString().slice(0, 19).replace("T", "_").replace(/:/g, "-");
  const slug = safeExportSlug(label);
  return `${stamp}__${slug}`;
}
