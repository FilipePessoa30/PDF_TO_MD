"""Geometric (grid-less) table detection (PROMPT Phase 1C section 5.3).

Corpus evidence: D3 (2021 CC bacharelado, page 14) has a 6-formula x 4-row
truth table with no vector-drawn grid lines - each cell is its own,
spatially isolated PyMuPDF text "line" (see docs/decisions.md, "Phase 1C"
ADR 12, for the raw word-bbox evidence this module's thresholds are
calibrated against). Flattened into prose (the pre-Phase-1C behaviour),
that collapses into an unreadable run of bare operators and V/F tokens.

**Method**: cluster ``Line`` bounding boxes first by Y (rows), then by X
within the surviving multi-cell rows (columns) - never by the logical or
mathematical meaning of a formula/cell (PROMPT: "Não use o significado
lógico das fórmulas para preencher células"). A run of lines only becomes
a ``DetectedTable`` when the resulting grid is *stable*: the same column
positions recur across (almost) every row, every row/column pair maps to
at most one cell, and the fraction of unpopulated cells stays small. Any
region that fails these checks is left alone (returned as no table at
all) rather than published as a guess - PROMPT section 6: "O parser deve
recusar ou marcar para revisão uma tabela geometricamente inconsistente."
and "Não complete células ausentes."

This is a content-shape detector, not a per-question rule: it runs over
every question's lines and only ever fires where the geometry itself
looks like a grid (see the thresholds below, all derived from real D3
measurements with a wide safety margin) - a future 2011/other-course
question with the same shape (a grid table with no ruling lines) would be
picked up the same way, with no question-id-specific code anywhere here.
"""

from __future__ import annotations

from dataclasses import dataclass

from enade.extraction.layout import Line

#: Two cells belong to the same visual row if their y0 values are within
#: this many points of each other. D3 evidence: within-row y0 spread is
#: <=1.5pt (symbol-font glyphs sit ~1pt higher than their neighbours);
#: row-to-row spacing is ~25pt - a >10x safety margin either way.
ROW_Y_TOLERANCE = 4.0
#: Two cells belong to the same column if their *center* x ((x0+x1)/2)
#: values are within this many points of each other. Cell content is
#: center-aligned per column in this corpus (a single "V"/"F" glyph and a
#: multi-character formula like "a -> not b" that share a column have very
#: different x0/x1, but the same center - D3 evidence: center-x spread
#: within a column is <1pt across all 6 rows); column-to-column center
#: spacing is >=45pt.
COLUMN_X_TOLERANCE = 6.0
#: A visual row only counts as a candidate table row once it has at least
#: this many distinct cells - guards against an ordinary two-word
#: coincidental alignment (e.g. a running header + page number) being
#: mistaken for a table row.
MIN_CELLS_PER_ROW = 3
#: A run of candidate rows only becomes a table once it has at least this
#: many rows - one or two aligned rows are not enough independent evidence
#: of a real recurring grid.
MIN_TABLE_ROWS = 3
#: A table needs at least this many *stable* (recurring) columns.
MIN_STABLE_COLUMNS = 3
#: A column is "stable" (real) only if populated by at least this
#: fraction of the rows in the run - tolerates one sparse row (e.g. a
#: super-header row numbering only some columns, as in D3) without
#: accepting a column that is mostly coincidental noise.
MIN_COLUMN_ROW_SUPPORT_FRACTION = 0.6
#: Reject the whole candidate table if more than this fraction of
#: (row, stable column) cells end up empty - a real grid should be
#: almost fully populated; a high blank fraction means the "columns"
#: found are not a genuine shared grid (falha conservadora, PROMPT
#: section 6).
MAX_BLANK_CELL_FRACTION = 0.2


@dataclass(frozen=True)
class DetectedTable:
    """One geometrically-reconstructed table, ready to become a ``TableBlock``.

    ``headers`` is the first detected visual row (see module docstring: no
    content-based special-casing - "first row = header" is the same
    convention any table/CSV reader applies). ``rows`` is every row after
    that, in top-to-bottom order. ``consumed_lines`` is every original
    ``Line`` this table was built from, so callers can exclude them from
    normal prose/code assembly (see assembler.py).
    """

    page_number: int
    bbox: tuple[float, float, float, float]
    headers: list[str]
    rows: list[list[str]]
    consumed_lines: frozenset[Line]


def _cluster_rows(lines: list[Line], *, tolerance: float = ROW_Y_TOLERANCE) -> list[list[Line]]:
    ordered = sorted(lines, key=lambda ln: (ln.y0, ln.x0))
    rows: list[list[Line]] = []
    for ln in ordered:
        if rows and (ln.y0 - rows[-1][-1].y0) <= tolerance:
            rows[-1].append(ln)
        else:
            rows.append([ln])
    return rows


def _cluster_columns(
    run: list[list[Line]], *, tolerance: float = COLUMN_X_TOLERANCE
) -> list[list[tuple[float, int, Line]]]:
    entries = sorted(
        (((ln.x0 + ln.x1) / 2, row_index, ln) for row_index, row in enumerate(run) for ln in row),
        key=lambda e: e[0],
    )
    clusters: list[list[tuple[float, int, Line]]] = []
    for center_x, row_index, ln in entries:
        if clusters and (center_x - clusters[-1][-1][0]) <= tolerance:
            clusters[-1].append((center_x, row_index, ln))
        else:
            clusters.append([(center_x, row_index, ln)])
    return clusters


def _build_table_from_run(page_number: int, run: list[list[Line]]) -> DetectedTable | None:
    if len(run) < MIN_TABLE_ROWS:
        return None

    column_clusters = _cluster_columns(run)
    min_support = max(2, round(len(run) * MIN_COLUMN_ROW_SUPPORT_FRACTION))

    stable_columns: list[list[tuple[float, int, Line]]] = []
    for cluster in column_clusters:
        row_indices = [row_index for _, row_index, _ in cluster]
        if len(set(row_indices)) != len(row_indices):
            # Two cells from the same visual row landed in the same column
            # cluster - an ambiguous/misaligned grid. Conservative failure
            # (PROMPT section 5.4: "ausência de célula deslocada").
            return None
        if len(row_indices) >= min_support:
            stable_columns.append(cluster)

    if len(stable_columns) < MIN_STABLE_COLUMNS:
        return None

    stable_columns.sort(key=lambda cluster: sum(x0 for x0, _, _ in cluster) / len(cluster))

    matrix: list[list[str]] = [["" for _ in stable_columns] for _ in run]
    for col_index, cluster in enumerate(stable_columns):
        for _, row_index, ln in cluster:
            matrix[row_index][col_index] = ln.text.strip()

    total_cells = len(matrix) * len(stable_columns)
    blank_cells = sum(1 for row in matrix for cell in row if not cell)
    if total_cells == 0 or (blank_cells / total_cells) > MAX_BLANK_CELL_FRACTION:
        return None

    all_cells = [ln for row in run for ln in row]
    bbox = (
        min(ln.x0 for ln in all_cells),
        min(ln.y0 for ln in all_cells),
        max(ln.x1 for ln in all_cells),
        max(ln.y1 for ln in all_cells),
    )

    return DetectedTable(
        page_number=page_number,
        bbox=bbox,
        headers=matrix[0],
        rows=matrix[1:],
        consumed_lines=frozenset(all_cells),
    )


def detect_tables(lines: list[Line]) -> list[DetectedTable]:
    """Find every grid-shaped run of ``lines``, grouped by page.

    Returns tables in page/top-to-bottom order. A run of consecutive
    (in visual-row order) candidate rows becomes a table only if it
    passes every check in ``_build_table_from_run``; a run that fails
    is simply not reported as a table - its lines remain untouched for
    normal prose/code handling by the caller.
    """
    by_page: dict[int, list[Line]] = {}
    for ln in lines:
        by_page.setdefault(ln.page_number, []).append(ln)

    tables: list[DetectedTable] = []
    for page_number in sorted(by_page):
        row_clusters = _cluster_rows(by_page[page_number])
        i = 0
        while i < len(row_clusters):
            if len(row_clusters[i]) < MIN_CELLS_PER_ROW:
                i += 1
                continue
            j = i
            while j < len(row_clusters) and len(row_clusters[j]) >= MIN_CELLS_PER_ROW:
                j += 1
            table = _build_table_from_run(page_number, row_clusters[i:j])
            if table is not None:
                tables.append(table)
            i = j
    return tables


def _escape_cell(text: str) -> str:
    return text.replace("|", "\\|")


def render_table_markdown(table: DetectedTable) -> str:
    """Render a ``DetectedTable`` as a GFM pipe table."""
    header = [_escape_cell(cell) for cell in table.headers]
    lines = [
        "| " + " | ".join(header) + " |",
        "| " + " | ".join("---" for _ in header) + " |",
    ]
    for row in table.rows:
        lines.append("| " + " | ".join(_escape_cell(cell) for cell in row) + " |")
    return "\n".join(lines)
