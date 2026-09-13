---
id: enade-2008-computing-d40
exam_year: 2008
source_occurrences:
- exam_id: enade-2008-b-computacao
  pdf_sha256: 5c8a08f7fdaccaa3b5661f40705e214bffdab634b845bce6288f8eeaa25db264
  source_path: 2008/b1_prova.pdf
  pages:
  - 17
  question_number: 40
  section: cc-bacharelado-discursiva
applicable_courses:
- ciencia-da-computacao-bacharelado
section: cc-bacharelado-discursiva
question_number: 40
question_type: discursive
content_blocks:
- type: asset
  asset_id: figure-01
- type: paragraph
  text: 'secundários: IndiceIdade, para o atributo idade, e IndiceRenda, para o atributo
    renda. Existe um tipo de serviço nesse banco cujo alvo são tanto os clientes que
    possuem menos de 40 anos de idade quanto aqueles que possuem renda mensal superior
    a 30.000 reais. Para recuperar esses clientes, a seguinte expressão de consulta
    em SQL foi utilizada:'
- type: code
  text: 'SELECT nome, endereco

    FROM Cliente

    WHERE idade < 40 OR renda > 30000;'
  language: null
- type: paragraph
  text: "Com o aumento do número de clientes desse banco, essa consulta passou a apresentar\
    \ problemas de desempenho. Verificou-se, então, que o otimizador de consultas\
    \ não considerava os índices existentes para idade e renda, e a consulta era realizada\
    \ mediante varredura seqüencial na relação Cliente, tornando essa consulta onerosa.\
    \ O plano de execução da consulta, usado pelo otimizador, é apresentado na árvore\
    \ de consulta abaixo, na qual B e F representam as operações de projeção e de\
    \ seleção, respectivamente. B\tnome,endereco"
- type: asset
  asset_id: figure-02
- type: paragraph
  text: utilizar os índices, a solução encontrada foi elaborar a consulta em dois
    blocos separados — um que recupera os clientes com idade inferior a 40 anos, e
    outro que recupera os clientes com renda mensal superior a 30.000 reais — para,
    então, juntar as tuplas das duas relações geradas. Considerando a situação apresentada,
    faça o que se pede a seguir. A Escreva o código de uma consulta em SQL que
- type: paragraph
  text: '(valor: 5,0 pontos)'
- type: paragraph
  text: 'B Desenhe a árvore de consulta para essa solução. (valor: 5,0 pontos)'
correct_answer: null
official_answer_source: null
answer_validation_status: not_applicable
answer_standard:
  source_path: 2008/b3_padrao.pdf
  pdf_sha256: 7021d115731ddcbad3c227da50f6d8c9c2c7f8a5a4b4d7dabce4b3726d0d35ef
  pages:
  - 1
  - 2
  - 3
  text: 'A. O estudante deve seguir a solução apresentada a seguir para receber 100%
    do valor da questão.


    1


    SELECT nome, endereço FROM Cliente WHERE idade < 40 UNION SELECT nome, endereço
    FROM Cliente WHERE renda>30000; B. Devem ser consideradas as seguintes soluções:
    B.1 A solução a seguir é aceitável como resposta, mesmo que o estudante não tenha
    apresentado a utilização do índice, deve receber 100% do valor máximo


    B.2 A solução abaixo é considerada como uma resposta correta e completa, portanto
    o estudante deve receber 100% do valor máximo.


    B.3 A solução abaixo é aceitável como resposta, mesmo que o estudante não tenha
    apresentado a utilização do índice, deve receber 100% do valor máximo.


    2


    B.4 A solução abaixo é considerada como uma resposta correta e completa, portanto
    o estudante deve receber 100% do valor máximo.'
  assets:
  - id: padrao-01
    type: diagram
    path: enade-2008-computing-d40/answer-standard/padrao-01.png
    source_page: 2
    extraction_method: raster_crop
    sha256: c19c512cb567bec505aea4ab87747d7bae2795e132ea4c3cb1290942dec8b699
    alt_text: null
    caption: null
  - id: padrao-02
    type: diagram
    path: enade-2008-computing-d40/answer-standard/padrao-02.png
    source_page: 2
    extraction_method: raster_crop
    sha256: 5016c651ac2ddb8996234891c5ab4efe11f7e8bf9e144b8cc7a2739d797f067a
    alt_text: null
    caption: null
  - id: padrao-03
    type: diagram
    path: enade-2008-computing-d40/answer-standard/padrao-03.png
    source_page: 2
    extraction_method: raster_crop
    sha256: a8aed9f217fdb837f5864a3fedd2bd82298be8562a787013afb89a478685d54d
    alt_text: null
    caption: null
assets:
- id: figure-01
  type: diagram
  path: enade-2008-computing-d40/figure-01.png
  source_page: 17
  extraction_method: raster_crop
  sha256: e7870885d02a001c3e6841c19c5dd03090f796bb9d32bcd6228f5d024492bb2c
  alt_text: null
  caption: null
- id: figure-02
  type: diagram
  path: enade-2008-computing-d40/figure-02.png
  source_page: 17
  extraction_method: raster_crop
  sha256: a6074f3f8fba48fab23fa7ec746eb053a8972e93562c2eee634aa26cc3066827
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

# Questão 40

![Figura da questão](enade-2008-computing-d40/figure-01.png)

secundários: IndiceIdade, para o atributo idade, e IndiceRenda, para o atributo renda. Existe um tipo de serviço nesse banco cujo alvo são tanto os clientes que possuem menos de 40 anos de idade quanto aqueles que possuem renda mensal superior a 30.000 reais. Para recuperar esses clientes, a seguinte expressão de consulta em SQL foi utilizada:

```
SELECT nome, endereco
FROM Cliente
WHERE idade < 40 OR renda > 30000;
```

Com o aumento do número de clientes desse banco, essa consulta passou a apresentar problemas de desempenho. Verificou-se, então, que o otimizador de consultas não considerava os índices existentes para idade e renda, e a consulta era realizada mediante varredura seqüencial na relação Cliente, tornando essa consulta onerosa. O plano de execução da consulta, usado pelo otimizador, é apresentado na árvore de consulta abaixo, na qual B e F representam as operações de projeção e de seleção, respectivamente. B	nome,endereco

![Figura da questão](enade-2008-computing-d40/figure-02.png)

utilizar os índices, a solução encontrada foi elaborar a consulta em dois blocos separados — um que recupera os clientes com idade inferior a 40 anos, e outro que recupera os clientes com renda mensal superior a 30.000 reais — para, então, juntar as tuplas das duas relações geradas. Considerando a situação apresentada, faça o que se pede a seguir. A Escreva o código de uma consulta em SQL que

(valor: 5,0 pontos)

B Desenhe a árvore de consulta para essa solução. (valor: 5,0 pontos)
