/** Convert Word/Excel clipboard tables into markdown. */

export interface ClipboardConversion {
  text: string;
  foundTable: boolean;
}

const SKIP_TAGS = new Set(["SCRIPT", "STYLE", "META", "LINK", "COLGROUP", "COL"]);

export function clipboardToMarkdown(html: string, plain: string): ClipboardConversion {
  const trimmedHtml = html.trim();
  if (trimmedHtml) {
    const fromHtml = htmlFragmentToMarkdown(trimmedHtml);
    if (fromHtml.foundTable) {
      return fromHtml;
    }
  }
  return tsvBlocksToMarkdown(plain);
}

export function insertText(
  value: string,
  start: number,
  end: number,
  insert: string,
): { value: string; cursor: number } {
  const next = `${value.slice(0, start)}${insert}${value.slice(end)}`;
  return { value: next, cursor: start + insert.length };
}

function htmlFragmentToMarkdown(html: string): ClipboardConversion {
  const doc = new DOMParser().parseFromString(html, "text/html");
  const blocks: string[] = [];
  let foundTable = false;

  const visit = (node: Node): void => {
    if (node.nodeType === Node.COMMENT_NODE) {
      return;
    }
    if (node.nodeType === Node.TEXT_NODE) {
      const text = collapseWhitespace(node.textContent ?? "");
      if (text) {
        blocks.push(text);
      }
      return;
    }
    if (!(node instanceof Element)) {
      return;
    }
    if (SKIP_TAGS.has(node.tagName)) {
      return;
    }
    if (node.tagName === "TABLE") {
      const markdown = tableElementToMarkdown(node);
      if (markdown) {
        foundTable = true;
        blocks.push(markdown);
      }
      return;
    }
    if (node.tagName === "BR") {
      return;
    }
    if (isBlockElement(node) && !node.querySelector("table")) {
      const text = collapseWhitespace(node.textContent ?? "");
      if (text) {
        blocks.push(text);
      }
      return;
    }
    Array.from(node.childNodes).forEach(visit);
  };

  Array.from(doc.body.childNodes).forEach(visit);
  return { text: blocks.join("\n\n").trim(), foundTable };
}

function tableElementToMarkdown(table: Element): string {
  const rows: string[][] = [];
  table.querySelectorAll("tr").forEach((row) => {
    const cells = Array.from(row.querySelectorAll("th, td")).map((cell) =>
      escapeCell(collapseWhitespace(cell.textContent ?? "")),
    );
    if (cells.length > 0) {
      rows.push(cells);
    }
  });
  return rowsToMarkdown(rows);
}

function tsvBlocksToMarkdown(plain: string): ClipboardConversion {
  const lines = normalizeNewlines(plain).split("\n");
  const out: string[] = [];
  let foundTable = false;
  let index = 0;
  while (index < lines.length) {
    const tsv = takeTsvTable(lines, index);
    if (tsv !== null) {
      foundTable = true;
      out.push(rowsToMarkdown(tsv.rows));
      index = tsv.nextIndex;
      continue;
    }
    out.push(lines[index] ?? "");
    index += 1;
  }
  return { text: out.join("\n").trimEnd(), foundTable };
}

function takeTsvTable(
  lines: string[],
  start: number,
): { rows: string[][]; nextIndex: number } | null {
  if (!isTsvLine(lines[start] ?? "")) {
    return null;
  }
  const rows: string[][] = [];
  let index = start;
  while (index < lines.length && isTsvLine(lines[index] ?? "")) {
    rows.push((lines[index] ?? "").split("\t").map((cell) => cell.trim()));
    index += 1;
  }
  if (rows.length < 2) {
    return null;
  }
  return { rows, nextIndex: index };
}

function rowsToMarkdown(rows: string[][]): string {
  const grid = normalizeWidth(rows);
  if (grid.length === 0) {
    return "";
  }
  const header = grid[0] ?? [];
  const body = grid.slice(1);
  const separator = header.map(() => "---");
  return [
    formatMarkdownRow(header),
    formatMarkdownRow(separator),
    ...body.map((row) => formatMarkdownRow(row)),
  ].join("\n");
}

function normalizeWidth(rows: string[][]): string[][] {
  const width = rows.reduce((max, row) => Math.max(max, row.length), 0);
  if (width === 0) {
    return [];
  }
  return rows.map((row) => {
    const next = row.map((cell) => cell.trim());
    while (next.length < width) {
      next.push("");
    }
    return next;
  });
}

function formatMarkdownRow(cells: string[]): string {
  return `| ${cells.join(" | ")} |`;
}

function isTsvLine(line: string): boolean {
  return line.includes("\t") && line.split("\t").length >= 2;
}

function isBlockElement(node: Element): boolean {
  return /^(P|H[1-6]|LI|BLOCKQUOTE|PRE|DIV)$/.test(node.tagName);
}

function collapseWhitespace(value: string): string {
  return value.replace(/\u00a0/g, " ").replace(/\s+/g, " ").trim();
}

function escapeCell(value: string): string {
  return value.replace(/\|/g, "\\|");
}

function normalizeNewlines(value: string): string {
  return value.replace(/\r\n/g, "\n").replace(/\r/g, "\n");
}
