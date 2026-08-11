---
id: fixture-invalid-unverified-table
exam_year: 2021
source_occurrences:
  - exam_id: enade-2021-b
    pdf_sha256: deadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeef
    source_path: 2021/b1_prova.pdf
    pages: [14]
    question_number: 99
    section: componente-especifico
applicable_courses:
  - ciencia-da-computacao-bacharelado
section: componente-especifico
question_number: 99
question_type: discursive
content_blocks:
  - type: paragraph
    text: "Considere a tabela a seguir."
  - type: table
    headers: ["p", "q"]
    rows:
      - ["V", "F"]
    validation_status: needs_review
---

# Questão 99

Fixture invalida: a tabela nao foi validada celula a celula
(`validation_status: needs_review`) e o bloco de conteudo nao inclui
nenhum `AssetBlock` de fallback visual - isso deve ser rejeitado
(ver PROMPT Fase 1C secao 5.2 e docs/decisions.md ADR 12).
