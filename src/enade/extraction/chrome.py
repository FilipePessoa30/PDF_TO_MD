"""Conservative detection of administrative "chrome" (page furniture).

Per PROMPT section 10: page numbers, running headers/footers, barcodes,
institutional logos, "rascunho" (scratch) rulers and similar booklet
furniture must never end up inside a question's statement/alternatives -
but when a line's status is genuinely ambiguous, this module does **not**
guess; it only recognizes a fixed, evidence-based list of exact patterns
observed in the real 2021 Ciencia da Computacao booklet (see docs/corpus.md
and docs/decisions.md). Anything not matching one of these patterns is left
alone, on the principle that leaving a stray line in the statement is a
recoverable, visible problem (caught by review), while silently dropping a
line that might have been real content is not.
"""

from __future__ import annotations

import re

# Exact (case-insensitive, whitespace-normalized) lines known to be pure
# booklet furniture in the 2021 corpus.
_EXACT_CHROME_LINES: frozenset[str] = frozenset(
    {
        "rascunho",
        "área livre",
        "area livre",
        "ciência da computação",
        "ciencia da computacao",
        "bacharelado",
        "gabarito definitivo",
        "padrão de resposta",
        "padrao de resposta",
        "sinaes",
        "sistema nacional de avaliação da educação superior",
        "sistema nacional de avaliacao da educacao superior",
        "da educação superior",
        "exame nacional de desempenho dos estudantes",
        "ministério da educação",
        "ministerio da educacao",
        "governo federal",
        "inep",
        "leia com atenção as instruções abaixo.",
        "leia com atencao as instrucoes abaixo.",
        "item",
        "gabarito",
    }
)

_CHROME_REGEXES: tuple[re.Pattern[str], ...] = (
    re.compile(r"^\d{1,3}$"),  # a bare page number
    re.compile(r"^\d+(\s+\d+){3,}$"),  # a "rascunho" ruler: "1 2 3 4 5 ... 15"
    re.compile(r"^\*[a-z0-9]+\*$"),  # barcode caption, e.g. "*r02202130*" (already lowercased)
    re.compile(r"(?i)^novembro\s*\|\s*\d{2}$"),  # cover date mark
    re.compile(r"(?i)^enade\s*20\d{2}$"),  # "enade2021" logo text
    re.compile(r"(?i)^qu[ea]st[iï]on[aá]rio\s+de\s+percep[cç][aã]o(\s+da\s+prova)?$"),
)


def normalize_for_chrome_check(text: str) -> str:
    return " ".join(text.strip().lower().split())


def is_chrome_line(text: str) -> bool:
    """True if ``text`` is administrative page furniture, not question content."""
    normalized = normalize_for_chrome_check(text)
    if not normalized:
        return True
    if normalized in _EXACT_CHROME_LINES:
        return True
    return any(pattern.match(normalized) for pattern in _CHROME_REGEXES)
