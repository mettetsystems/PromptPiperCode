import { describe, expect, it } from "vitest";
import { buildExportFolderPreview, safeExportSlug } from "./exportFolder";

describe("exportFolder", () => {
  it("slugifies titles", () => {
    expect(safeExportSlug("Weekly Status Update")).toBe("weekly-status-update");
  });

  it("builds dated folder preview", () => {
    const preview = buildExportFolderPreview(
      "Weekly status",
      new Date("2026-06-15T14:30:00.000Z"),
    );
    expect(preview.startsWith("2026-06-15_")).toBe(true);
    expect(preview.endsWith("__weekly-status")).toBe(true);
  });
});
