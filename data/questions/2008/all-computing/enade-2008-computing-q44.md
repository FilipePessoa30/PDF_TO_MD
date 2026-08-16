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
- type: paragraph
  text: Considere um banco de dados relacional que contém as seguintes tabelas, em
    que o grifo representa a chave primeira da tabela Produtos (idProduto, descricao,
    valorUnitario) Estoque (idFilial, idProduto, quantidade) A tabela Produtos é populada
    com aproximadamente 10.000 registros, enquanto a tabela Estoque é populada com
    aproximadamente 100.000 registros. Para escrever uma consulta em SQL que determine
    o valor total das mercadorias em estoque de uma filial cujo identificador é igual
    a 132, pode-se usar uma das duas codificações apresentadas a seguir. Consulta
    1
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
  text: A partir dessas informações e considerando que a tabela Estoque possua um
    índice sobre a coluna idFilial, analise as seguintes asserções. O processamento
    da Consulta 1 tem melhor desempenho que o da Consulta 2 PORQUE a quantidade de
    registros processados na consulta 1 é, no pior caso, igual a 10.000, enquanto
    o pior caso na consulta 2 terá (10.000)2 registros. Assinale a opção correta a
    respeito dessas asserções.
correct_answer: null
official_answer_source: 2008/b2_gabarito.pdf
answer_validation_status: annulled
answer_standard: null
assets: []
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
extraction_status: verified
automatic_validation: passed
visual_validation: passed
taxonomy_review_status: pending
---

# Questão 44

Considere um banco de dados relacional que contém as seguintes tabelas, em que o grifo representa a chave primeira da tabela Produtos (idProduto, descricao, valorUnitario) Estoque (idFilial, idProduto, quantidade) A tabela Produtos é populada com aproximadamente 10.000 registros, enquanto a tabela Estoque é populada com aproximadamente 100.000 registros. Para escrever uma consulta em SQL que determine o valor total das mercadorias em estoque de uma filial cujo identificador é igual a 132, pode-se usar uma das duas codificações apresentadas a seguir. Consulta 1

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

A partir dessas informações e considerando que a tabela Estoque possua um índice sobre a coluna idFilial, analise as seguintes asserções. O processamento da Consulta 1 tem melhor desempenho que o da Consulta 2 PORQUE a quantidade de registros processados na consulta 1 é, no pior caso, igual a 10.000, enquanto o pior caso na consulta 2 terá (10.000)2 registros. Assinale a opção correta a respeito dessas asserções.

## Alternativas

A. As duas asserções são proposições verdadeiras, e a segunda é uma justificativa correta da primeira.
B. As duas asserções são proposições verdadeiras, mas a segunda não é justificativa correta da primeira.
C. A primeira asserção é uma proposição verdadeira, e a segunda, uma proposição falsa.
D. A primeira asserção é uma proposição falsa, e a segunda, uma proposição verdadeira.
E. Tanto a primeira quanto a segunda asserções são proposições falsas.
