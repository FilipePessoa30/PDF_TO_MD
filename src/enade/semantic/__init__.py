"""The semantic layer (PROMPT Fase 5A): taxonomy, question annotation,
pilot selection, and their own gates - built entirely on top of the
already-frozen extraction layer (``enade.extraction``/``enade.models``),
never modifying it.

Layering (never violated by this package): extraction -> taxonomy ->
annotation -> search terms -> recommendation -> frontend. This package
implements only the first two layers; everything after "annotation" is
explicitly out of scope for Fase 5A (see docs/phase-5a-report.md section
32, "NAO FAZER").
"""

from __future__ import annotations
