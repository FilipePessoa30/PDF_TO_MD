---
id: enade-2008-computing-d80
exam_year: 2008
source_occurrences:
- exam_id: enade-2008-b-computacao
  pdf_sha256: 5c8a08f7fdaccaa3b5661f40705e214bffdab634b845bce6288f8eeaa25db264
  source_path: 2008/b1_prova.pdf
  pages:
  - 34
  - 35
  question_number: 80
  section: sistemas-informacao-discursiva
applicable_courses:
- sistemas-de-informacao
section: sistemas-informacao-discursiva
question_number: 80
question_type: discursive
content_blocks: null
correct_answer: null
official_answer_source: null
answer_validation_status: not_applicable
answer_standard:
  source_path: 2008/b3_padrao.pdf
  pdf_sha256: 7021d115731ddcbad3c227da50f6d8c9c2c7f8a5a4b4d7dabce4b3726d0d35ef
  pages:
  - 5
  - 6
  text: 'Resposta correta: Diagrama correto.


    A. Falhas: a mensagem que constrói o objeto banco não está sintaticamente correta
    ou a mensagem que constrói o objeto cliente não está sintaticamente correta; a
    invocação da mensagem cria conta não deveria ser representada de forma assíncrona;
    as invocações dos métodos criaCliente e do construtor de agência estão sobrepostas
    temporalmente, quando não deveriam sê-las.


    B. Falhas: a criação da agência não deve ser feita diretamente pelo caso de uso
    através da invocação do construtor da classe, pois o construtor é protegido e
    no Banco há o método criarAgência() para apoiar esta operação; uma das contas
    está sendo inadequadamente 5


    criada no escopo da criação do cliente (criarCliente()), quando deveria ser realizada
    pelo método criarConta da classe Agência; os métodos creditar e debitar não deveriam
    ser invocados diretamente pela realização do caso de uso; o diagrama original
    deveria conter mensagem entre Banco e Agência (GetConta)


    6'
  assets:
  - id: padrao-01
    type: diagram
    path: enade-2008-computing-d80/answer-standard/padrao-01.png
    source_page: 5
    extraction_method: raster_crop
    sha256: f8b14ab4a873806b799ded1f5c4e681df63ace4262d4f7e25bdb595657814d3a
    alt_text: null
    caption: null
  - id: padrao-02
    type: diagram
    path: enade-2008-computing-d80/answer-standard/padrao-02.png
    source_page: 6
    extraction_method: raster_crop
    sha256: ce084189c96bbf415a5c34790c96630047809a7a73d470d5da4b01a98921b829
    alt_text: null
    caption: null
  - id: padrao-03
    type: diagram
    path: enade-2008-computing-d80/answer-standard/padrao-03.png
    source_page: 6
    extraction_method: raster_crop
    sha256: a1b3268e2a7755a8385728279c4e2fec9ed08e149b407e48a757ad26401859b1
    alt_text: null
    caption: null
assets:
- id: figure-01
  type: image
  path: enade-2008-computing-d80/figure-01.png
  source_page: 34
  extraction_method: raster_crop
  sha256: fe93d0fa30aa13c1c0a23fa89791b705dbcaa88c12c0618cc366047a53f6cab3
  alt_text: null
  caption: null
- id: figure-02
  type: diagram
  path: enade-2008-computing-d80/figure-02.png
  source_page: 35
  extraction_method: raster_crop
  sha256: c444faf3a925b2bef45f7aba07222da6352d18ac81588dda0ee12350768b1b44
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
extraction_status: verified
automatic_validation: passed
visual_validation: passed
taxonomy_review_status: pending
---

# Questão 80

![Figura da questão](enade-2008-computing-d80/figure-01.png)

No diagrama de seqüência apresentado, há problemas conceituais, relativos à especificação do diagrama de classes e à descrição textual do caso de uso DUPLA-CONTA. Com relação a essa situação, faça o que se pede a seguir.

A Descreva, textualmente, três falhas de tipos distintos presentes no diagrama de seqüência apresentado, relativas ao

![Figura da questão](enade-2008-computing-d80/figure-02.png)

B Descreva, textualmente, três falhas distintas presentes no diagrama de seqüência apresentado, relativas à
