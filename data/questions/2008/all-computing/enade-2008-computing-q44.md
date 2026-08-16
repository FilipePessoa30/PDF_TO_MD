---
id: enade-2008-computing-q44
exam_year: 2008
source_occurrences:
- exam_id: enade-2008-b-computacao
  pdf_sha256: 5c8a08f7fdaccaa3b5661f40705e214bffdab634b845bce6288f8eeaa25db264
  source_path: 2008/b1_prova.pdf
  pages:
  - 19
  question_number: 44
  section: engenharia-computacao-objetiva
applicable_courses:
- engenharia-da-computacao
section: engenharia-computacao-objetiva
question_number: 44
question_type: multiple_choice
content_blocks:
- type: asset
  asset_id: figure-01
- type: paragraph
  text: primeira da tabela Produtos (idProduto, descricao, valorUnitario) Estoque
    (idFilial, idProduto, quantidade) A tabela Produtos é populada com aproximadamente
- type: paragraph
  text: apresentadas a seguir. Consulta 1
- type: code
  text: "SELECT\n  SUM(valorUnitario * quantidade)\nFROM\n  Estoque, Produtos\nWHERE\n\
    \  Estoque.idFilial = 132 AND\n  Produtos.idProduto = Estoque.idProduto"
  language: null
- type: paragraph
  text: Consulta 2
- type: code
  text: "SELECT\n  SUM(valorUnitario * quantidade)\nFROM\n  Produtos, Estoque\nWHERE\n\
    \  Estoque.idFilial = 132 AND\n  Produtos.idProduto = Estoque.idProduto"
  language: null
- type: paragraph
  text: A partir dessas informações e considerando que a tabela analise as seguintes
    asserções.
- type: paragraph
  text: que o da Consulta 2 PORQUE
- type: paragraph
  text: 2 terá (10.000)2 registros. Assinale a opção correta a respeito dessas asserções.
correct_answer: null
official_answer_source: 2008/b2_gabarito.pdf
answer_validation_status: annulled
answer_standard: null
assets:
- id: figure-01
  type: image
  path: enade-2008-computing-q44/figure-01.png
  source_page: 19
  extraction_method: raster_crop
  sha256: f08c4e82648202822655a8d06b9ba09742139b0082538cf2cf2990a77a1bb114
  alt_text: null
  caption: null
subjects: []
topics: []
concepts: []
keywords: []
competencies: []
prerequisites: []
difficulty: null
alternative_diagnostics: {}
extraction_method: text_layer
ocr_confidence: null
extraction_status: needs_review
automatic_validation: passed
visual_validation: failed
taxonomy_review_status: pending
---

# Questão 44

![Figura da questão](enade-2008-computing-q44/figure-01.png)

primeira da tabela Produtos (idProduto, descricao, valorUnitario) Estoque (idFilial, idProduto, quantidade) A tabela Produtos é populada com aproximadamente

apresentadas a seguir. Consulta 1

```
SELECT
  SUM(valorUnitario * quantidade)
FROM
  Estoque, Produtos
WHERE
  Estoque.idFilial = 132 AND
  Produtos.idProduto = Estoque.idProduto
```

Consulta 2

```
SELECT
  SUM(valorUnitario * quantidade)
FROM
  Produtos, Estoque
WHERE
  Estoque.idFilial = 132 AND
  Produtos.idProduto = Estoque.idProduto
```

A partir dessas informações e considerando que a tabela analise as seguintes asserções.

que o da Consulta 2 PORQUE

2 terá (10.000)2 registros. Assinale a opção correta a respeito dessas asserções.

## Alternativas

A. As duas asserções são proposições verdadeiras, e a segunda é uma justificativa correta da primeira.
B. As duas asserções são proposições verdadeiras, mas a segunda não é justificativa correta da primeira.
C. A primeira asserção é uma proposição verdadeira, e a segunda, uma proposição falsa.
D. A primeira asserção é uma proposição falsa, e a segunda, uma proposição verdadeira.
E. Tanto a primeira quanto a segunda asserções são proposições falsas.
