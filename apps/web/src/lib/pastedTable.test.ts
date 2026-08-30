import { describe, expect, it } from "vitest";
import { clipboardToMarkdown, insertText } from "./pastedTable";

const WORD_HTML = `
<html xmlns:o="urn:schemas-microsoft-com:office:office">
<body>
<!--StartFragment-->
<p class="MsoNormal">Implement the routes in this chart.</p>
<table class="MsoTableGrid" border="1">
  <tr>
    <td><p class="MsoNormal">Endpoint</p></td>
    <td><p class="MsoNormal">Method</p></td>
  </tr>
  <tr>
    <td><p class="MsoNormal">/users</p></td>
    <td><p class="MsoNormal">POST</p></td>
  </tr>
</table>
<p class="MsoNormal">Match existing FastAPI patterns.</p>
<!--EndFragment-->
</body>
</html>
`;

describe("clipboardToMarkdown", () => {
  it("converts a Word-like HTML table and surrounding prose", () => {
    const result = clipboardToMarkdown(WORD_HTML, "flattened fallback");
    expect(result.foundTable).toBe(true);
    expect(result.text).toContain("Implement the routes in this chart.");
    expect(result.text).toContain("| Endpoint | Method |");
    expect(result.text).toContain("| --- | --- |");
    expect(result.text).toContain("| /users | POST |");
    expect(result.text).toContain("Match existing FastAPI patterns.");
  });

  it("converts tab-separated rows when HTML has no table", () => {
    const plain = [
      "Add these handlers.",
      "Path\tVerb",
      "/health\tGET",
      "/users\tPOST",
    ].join("\n");
    const result = clipboardToMarkdown("<p>Add these handlers.</p>", plain);
    expect(result.foundTable).toBe(true);
    expect(result.text).toContain("Add these handlers.");
    expect(result.text).toContain("| Path | Verb |");
    expect(result.text).toContain("| /health | GET |");
  });

  it("leaves ordinary prose paste unchanged", () => {
    const result = clipboardToMarkdown(
      "<p>Implement a FastAPI endpoint with pytest coverage.</p>",
      "Implement a FastAPI endpoint with pytest coverage.",
    );
    expect(result.foundTable).toBe(false);
    expect(result.text).toBe("Implement a FastAPI endpoint with pytest coverage.");
  });
});

describe("insertText", () => {
  it("inserts converted table text at the caret", () => {
    expect(insertText("before after", 7, 7, "| A | B |\n| --- | --- |")).toEqual({
      value: "before | A | B |\n| --- | --- |after",
      cursor: 7 + "| A | B |\n| --- | --- |".length,
    });
  });
});
