"""Ordered, mixed-content representation for a question's body (PROMPT
Phase 1C section 4/11).

**Motivation (corpus evidence, not a hypothetical need)**: `Question.statement`
is a single flat string, and `Question.assets` is an unordered list - neither
records *where in the reading order* an asset, a table, or a code block
sits relative to the surrounding prose. For 38 of this corpus's 40
questions that loses nothing observable (the statement is one contiguous
paragraph run, figures slot in via the existing inline `![...]` Markdown
reference). It loses real information for two: D3 (paragraph -> formula
list -> paragraph -> ... -> table -> paragraph) and D5 (paragraph -> table
image -> tree-diagram image -> paragraph -> citation, with a full code
listing that must read as its own block, not be flattened into prose). A
future 2011/other-course pass will almost certainly hit the same shape
again - propositional-logic truth tables and pseudocode listings are not
specific to this one booklet.

**Design**: `content_blocks` is an **additive, optional** field on
`Question` (see docs/decisions.md ADR 12). When absent (the default for
every question that does not need it), rendering/parsing behaves exactly
as before Phase 1C - this is why every fixture and all 40 existing
Markdown files needed no migration. When present, it is the authoritative,
ordered representation of the question body; `statement` is still
populated (a flattened plain-text projection, kept for full-text search
and backward compatibility) but is no longer what the Markdown body is
rendered from.

Each block type maps directly onto a segment kind already produced
internally by the extraction pipeline (`assembler.py`'s `StatementSegment`
union: `TextSegment`, `CodeSegment`, `FigureSegment`, plus the new
`TableSegment`) - this schema does not invent a parallel taxonomy, it is
the persisted, public form of what extraction already computes.

Round-trip is by construction, not by re-parsing rendered Markdown:
`content_blocks` lives in the YAML front matter (like `assets` and
`alternatives` already do), so `model -> front matter -> parse -> model`
is exact. The rendered Markdown body (built from the blocks, for human
readability) is a presentation artifact, never re-parsed back into blocks.
"""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field

from enade.models.enums import TableValidationStatus


class ParagraphBlock(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: Literal["paragraph"] = "paragraph"
    text: str = Field(..., min_length=1)


class CodeBlock(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: Literal["code"] = "code"
    text: str = Field(..., min_length=1, description="verbatim, newline-joined; never reformatted")
    language: str | None = None


class TableBlock(BaseModel):
    """A table transcribed cell-by-cell from glyph geometry (never from the
    logical/mathematical meaning of its contents - PROMPT section 5.3: "Não
    use o significado lógico das fórmulas para preencher células").

    ``validation_status`` records whether every cell was confirmed against
    the rendered PDF (see docs/decisions.md ADR 12): a table that has not
    passed that check must never be presented as if it were reliable - see
    ``Question._validate_content_blocks`` in question.py, which requires an
    accompanying visual-fallback asset whenever a `TableBlock` is not
    `verified`.
    """

    model_config = ConfigDict(extra="forbid")

    type: Literal["table"] = "table"
    headers: list[str] = Field(default_factory=list)
    rows: list[list[str]] = Field(..., min_length=1)
    validation_status: TableValidationStatus = TableValidationStatus.NEEDS_REVIEW


class AssetBlock(BaseModel):
    """A pointer, by id, into ``Question.assets`` - never a copy of the
    asset's own fields, so there is exactly one place an asset's
    path/hash/page can drift out of sync.
    """

    model_config = ConfigDict(extra="forbid")

    type: Literal["asset"] = "asset"
    asset_id: str = Field(..., min_length=1)


ContentBlock = Annotated[
    ParagraphBlock | CodeBlock | TableBlock | AssetBlock,
    Field(discriminator="type"),
]
