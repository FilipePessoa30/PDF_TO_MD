---
id: enade-2021-si-d05
exam_year: 2021
source_occurrences:
- exam_id: enade-2021-s
  pdf_sha256: 13d81a46488d93fb66836e7c704f9de1ba722c3b130ccb4f0aa9d3522c855ba7
  source_path: 2021/s1_prova.pdf
  pages:
  - 16
  question_number: 5
  section: componente-especifico-discursiva
applicable_courses:
- sistemas-de-informacao
section: componente-especifico-discursiva
question_number: 5
question_type: discursive
content_blocks: null
correct_answer: null
official_answer_source: null
answer_validation_status: not_applicable
answer_standard:
  source_path: 2021/s3_padrao.pdf
  pdf_sha256: 4c9ea3b838717c88fec4512c60b10b894c92e982c8aefce630d97075c0f0473f
  pages:
  - 5
  - 6
  text: 'a) O respondente deve indicar quem é a subclasse (gerente) e quem é a superclasse
    (atendente) e que o tipo de relacionamento é generalização. Alternativamente,
    pode indicar herança como o tipo de relacionamento. b) O respondente deve elaborar
    um diagrama conforme o apresentado a seguir. A nomenclatura dos casos de uso pode
    ser diferente desde que preservado seu significado.


    Como primeira alternativa, a representação de atores pode ser realizada usando
    a notação de classes com estereótipos em vez da notação de ícones, conforme o
    diagrama apresentado a seguir.


    Como segunda alternativa, o diagrama a seguir. Essa possibilidade é mais usual
    entre os alunos e desenvolvedores profissionais.'
  assets:
  - id: padrao-01
    type: diagram
    path: enade-2021-si-d05/answer-standard/padrao-01.png
    source_page: 5
    extraction_method: raster_crop
    sha256: a529cd23db927a6c7695f2f1e17fd330e1318edb15bc6421eee865ae02a9b85f
    alt_text: null
    caption: null
  - id: padrao-02
    type: diagram
    path: enade-2021-si-d05/answer-standard/padrao-02.png
    source_page: 6
    extraction_method: raster_crop
    sha256: 79941d8d58bb34c85f98cbfc8854f042f586e115b50c5df80194ba07c461254e
    alt_text: null
    caption: null
  - id: padrao-03
    type: diagram
    path: enade-2021-si-d05/answer-standard/padrao-03.png
    source_page: 6
    extraction_method: raster_crop
    sha256: 82fab33712f55db9e45279661e63d74655d10483f271de431c47e9c1679379dc
    alt_text: null
    caption: null
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
extraction_status: extracted
automatic_validation: passed
visual_validation: not_performed
taxonomy_review_status: pending
---

# Questão 5

Uma loja pretende desenvolver um sistema cujo processo de modelagem utilizará UML (Unified Modeling Language). Essa empresa tem dois tipos de colaboradores, o atendente e o gerente. A principal atividade a ser automatizada pelo sistema é o processamento de vendas, cuja execução é altamente complexa. Dessa forma, a modelagem deve ser realizada de maneira estruturada e organizada, tendo como foco a sua reutilização em diferentes contextos. As vendas são realizadas quase integralmente por atendentes, entretanto, caso haja grande quantidade de clientes, os gerentes também podem processar vendas, por exemplo. O processamento de vendas pode ser realizado considerando duas modalidades de pagamento: a prazo ou à vista, todavia, independentemente da forma de pagamento, há um conjunto comum de ações que sempre são realizadas. As compras a prazo englobam dois modos de pagamento (via cartão de crédito e via boleto) que possuem ações comuns, mas que se diferem nas ações finais. Para algumas formas de processamento de vendas é aplicado um desconto sobre o valor total. O desconto deve ser aplicado sempre que o pagamento for realizado à vista ou quando o pagamento for realizado via boleto com parcelamento em até seis vezes. Entretanto, a loja oferece como forma de pagamento boleto com parcelamento em até doze vezes. No processamento de vendas, após a confirmação do pagamento, é necessário emitir a nota fiscal dos produtos. Apenas em circunstâncias em que algum dos produtos vendidos não possa ser retirado na loja, deve ser possível solicitar a entrega pelo sistema. Considerando a situação apresentada no texto, faça o que se pede nos itens a seguir. a) Indique o tipo de relacionamento que, de acordo com a linguagem UML, permite representar o fato de atendentes e gerentes poderem realizar as mesmas atividades. (valor: 3,0 pontos) b) Elabore um diagrama de caso de uso completo da UML para esse sistema, identificando os atores, os casos de uso e os relacionamentos. (valor: 7,0 pontos)
