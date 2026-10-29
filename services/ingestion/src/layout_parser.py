"""Layout-aware statutory document parser.

Parses official notifications and circulars into hierarchical sections,
numbered clauses, provisos, and structured table grids (FR-004).
"""

import re
from services.ingestion.src.models import (
    ExtractedClause,
    ExtractedSection,
    ExtractedTable,
)


class LayoutAwareParser:
    """Extracts statutory structure, numbered clauses, and tables from raw text."""

    CLAUSE_PATTERN = re.compile(
        r"^(?:\((\w+)\)|(\d+[\.\)])|([A-Z]\.)|(Para(?:graph)?\s*\d+)|(Entry\s*\d+))\s*",
        re.MULTILINE,
    )
    HEADING_PATTERN = re.compile(
        r"^(?:(?:Section|Chapter|Part|Notification|Circular|Schedule)\s+[A-Z0-9IVX]+|#+\s+[^\n]+)",
        re.IGNORECASE | re.MULTILINE,
    )

    def parse_pages(self, pages: list[str]) -> list[ExtractedSection]:
        """Parses extracted page strings into a hierarchy of sections, clauses, and tables."""
        sections: list[ExtractedSection] = []
        current_section = ExtractedSection(path="Preamble", heading="Preamble")

        for page_idx, page_text in enumerate(pages, start=1):
            if not page_text.strip():
                continue

            lines = page_text.splitlines()
            line_idx = 0

            while line_idx < len(lines):
                line = lines[line_idx].strip()
                if not line:
                    line_idx += 1
                    continue

                # 1. Detect Tables (Delimited by | or tab structures)
                if line.startswith("|") and line.endswith("|") and "|" in line[1:-1]:
                    table, consumed = self._parse_table_block(lines[line_idx:], page_idx)
                    if table:
                        current_section.tables.append(table)
                        line_idx += consumed
                        continue

                # 2. Detect Headings
                if self.HEADING_PATTERN.match(line):
                    if current_section.clauses or current_section.tables:
                        current_section.page_to = page_idx
                        sections.append(current_section)
                    heading_text = re.sub(r"^#+\s*", "", line)
                    current_section = ExtractedSection(
                        path=heading_text,
                        heading=heading_text,
                        page_from=page_idx,
                        page_to=page_idx,
                    )
                    line_idx += 1
                    continue

                # 3. Detect Numbered Clauses
                clause_match = self.CLAUSE_PATTERN.match(line)
                if clause_match:
                    clause_label = line[:clause_match.end()].strip()
                    clause_body_lines = [line[clause_match.end():].strip()]
                    line_idx += 1

                    # Slurp continuation lines of the clause until next clause or heading
                    while line_idx < len(lines):
                        next_line = lines[line_idx].strip()
                        if not next_line:
                            line_idx += 1
                            continue
                        if self.CLAUSE_PATTERN.match(next_line) or self.HEADING_PATTERN.match(next_line) or (next_line.startswith("|") and next_line.endswith("|")):
                            break
                        clause_body_lines.append(next_line)
                        line_idx += 1

                    clause_text = " ".join(clause_body_lines).strip()
                    clause_path = f"{current_section.path} > {clause_label}"
                    clause_type = "proviso" if "provided that" in clause_text.lower() else "clause"

                    current_section.clauses.append(
                        ExtractedClause(
                            path=clause_path,
                            text=f"{clause_label} {clause_text}".strip(),
                            clause_type=clause_type,
                            page_number=page_idx,
                        )
                    )
                    continue

                # 4. Standard Paragraph
                para_lines = [line]
                line_idx += 1
                while line_idx < len(lines):
                    next_line = lines[line_idx].strip()
                    if not next_line or self.CLAUSE_PATTERN.match(next_line) or self.HEADING_PATTERN.match(next_line) or (next_line.startswith("|") and next_line.endswith("|")):
                        break
                    para_lines.append(next_line)
                    line_idx += 1

                para_text = " ".join(para_lines).strip()
                current_section.clauses.append(
                    ExtractedClause(
                        path=f"{current_section.path} > Para",
                        text=para_text,
                        clause_type="clause",
                        page_number=page_idx,
                    )
                )

        if current_section.clauses or current_section.tables:
            current_section.page_to = len(pages)
            sections.append(current_section)

        return sections

    def _parse_table_block(self, lines: list[str], page_number: int) -> tuple[ExtractedTable | None, int]:
        """Parses consecutive pipe-delimited table rows."""
        table_lines: list[str] = []
        for l in lines:
            trimmed = l.strip()
            if trimmed.startswith("|") and trimmed.endswith("|"):
                table_lines.append(trimmed)
            else:
                break

        if len(table_lines) < 2:
            return None, 0

        # Extract headers from first row
        headers = [c.strip() for c in table_lines[0].strip("|").split("|")]
        rows: list[list[str]] = []

        start_row = 1
        # Skip markdown separator row if present (e.g. |---|---|)
        if len(table_lines) > 1 and re.match(r"^\|(?:\s*[-:]+[-|\s:]*)\|$", table_lines[1]):
            start_row = 2

        for row_str in table_lines[start_row:]:
            row_cols = [c.strip() for c in row_str.strip("|").split("|")]
            if len(row_cols) == len(headers):
                rows.append(row_cols)

        table = ExtractedTable(
            headers=headers,
            rows=rows,
            page_number=page_number,
        )
        return table, len(table_lines)
