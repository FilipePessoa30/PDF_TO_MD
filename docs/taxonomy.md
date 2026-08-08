# Taxonomy

## Model

`Subject -> Topic -> Concept`, where a `Concept` carries its own `aliases`,
`keywords`, and `prerequisites` (ids of other concepts, resolved anywhere
in the same taxonomy document - not restricted to the same topic/subject).
See `src/enade/models/taxonomy.py` for the full contract and its validators
(unique ids, resolvable non-self-referencing prerequisites).

This exists specifically so the platform can distinguish, e.g.:

```
Estruturas de Dados
  -> Árvores                     (topic)
     -> Árvore Binária           (concept)
     -> Árvore de Busca (BST)    (concept, prerequisite: Árvore Binária)
     -> Árvore Balanceada        (concept, prerequisite: Árvore de Busca)
     -> Percursos em Árvore      (concept, prerequisite: Árvore Binária)
```

rather than a flat bag of keywords - a question can reference the specific
concept it actually needs (`arvore-de-busca`), and that concept can point
back at what a student needs to already understand (`arvore-binaria`).

A `Question` references taxonomy nodes purely by id (`subjects`, `topics`,
`concepts`, plus free-text `keywords`) - it does not embed the taxonomy
inline, so a question can be re-tagged by editing the taxonomy or the
question independently, and a question can belong to more than one concept.

## The demo instance

[`data/taxonomy/demo-taxonomy.yaml`](../data/taxonomy/demo-taxonomy.yaml)
is a **small, explicitly-non-definitive** instance used only to validate
the schema end-to-end (two subjects, a handful of concepts, one
cross-subject prerequisite link to prove that resolution isn't
scoped to a single subject). It sets `status: demo` and a `notice` field
that says, verbatim, that it is not the definitive Computing taxonomy.
`enade validate-schema` validates it on every run
(`tests/test_schema_taxonomy.py::test_demo_taxonomy_in_data_dir_is_valid_and_marked_as_demo`
also asserts the disclaimer is present, not just that the file parses).

Building the real taxonomy - informed by the actual ENADE Computing "matriz
de referencia" / syllabus, reviewed by someone who actually teaches this
material - is explicitly **out of scope** for Phase 0. Nothing here should
be read as a claim about curriculum coverage.

## Misconceptions catalog

A sibling, similarly-demo-only file,
[`data/taxonomy/demo-misconceptions.yaml`](../data/taxonomy/demo-misconceptions.yaml),
holds a couple of hand-written `MisconceptionDefinition` entries
(`assumes-tree-is-balanced`, `confuses-tree-traversal-order`) tied to
concepts in the demo taxonomy, to validate that contract too. No question
in the corpus has actually been diagnosed against these in Phase 0 - see
`Question.alternative_diagnostics` in [data-contract.md](data-contract.md)
for how a real diagnosis would eventually attach to a specific wrong
alternative.
