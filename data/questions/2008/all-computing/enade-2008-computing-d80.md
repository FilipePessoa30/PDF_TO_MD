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
  sha256: e4dc51222447c27c172c834d9356ac47de31ad37e0549098f8f44bbd4cc72c9d
  alt_text: null
  caption: null
- id: figure-02
  type: image
  path: enade-2008-computing-d80/figure-02.png
  source_page: 34
  extraction_method: raster_crop
  sha256: b5f82546b9d97ecd3a6059056943c2262f4a1f6f3774c25776a0a12e35b1bbde
  alt_text: null
  caption: null
- id: figure-03
  type: diagram
  path: enade-2008-computing-d80/figure-03.png
  source_page: 35
  extraction_method: raster_crop
  sha256: b102cd7a95cc6ee8375e10c95caae405bde6e8d8e872dbfcabb657878ad87a12
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

Durante a análise de um sistema de controle de contas bancárias (SCCB), um analista elaborou o diagrama de classes acima, em que são especificados os objetos de negócio da aplicação, por meio do qual foram distribuídas as responsabilidades e colaborações entre os elementos do modelo. Foi atribuída a outro analista a tarefa de elaborar o diagrama de seqüência do caso de uso chamado DUPLA_CONTA, que apresenta o seguinte comportamento: cria um banco, cria uma agência bancária, cria um cliente e duas contas bancárias associadas ao cliente e agência bancária anteriormente criados, e, por fim, realiza uma transferência de valores entre essas duas contas bancárias. O diagrama de seqüência em UML apresentado abaixo foi elaborado com o intuito de corresponder ao caso de uso em questão.

![Figura da questão](enade-2008-computing-d80/figure-02.png)

No diagrama de seqüência apresentado, há problemas conceituais, relativos à especificação do diagrama de classes e à descrição textual do caso de uso DUPLA-CONTA. Com relação a essa situação, faça o que se pede a seguir.

A Descreva, textualmente, três falhas de tipos distintos presentes no diagrama de seqüência apresentado, relativas ao

![Figura da questão](enade-2008-computing-d80/figure-03.png)

B Descreva, textualmente, três falhas distintas presentes no diagrama de seqüência apresentado, relativas à
