---
id: enade-2008-computing-d60
exam_year: 2008
source_occurrences:
- exam_id: enade-2008-b-computacao
  pdf_sha256: 5c8a08f7fdaccaa3b5661f40705e214bffdab634b845bce6288f8eeaa25db264
  source_path: 2008/b1_prova.pdf
  pages:
  - 26
  - 27
  question_number: 60
  section: engenharia-computacao-discursiva
applicable_courses:
- engenharia-da-computacao
section: engenharia-computacao-discursiva
question_number: 60
question_type: discursive
content_blocks: null
correct_answer: null
official_answer_source: null
answer_validation_status: not_applicable
answer_standard:
  source_path: 2008/b3_padrao.pdf
  pdf_sha256: 7021d115731ddcbad3c227da50f6d8c9c2c7f8a5a4b4d7dabce4b3726d0d35ef
  pages:
  - 4
  text: 'A. Considerando que 1 baud = log2 (L) bps, em que L é o número de níveis
    de sinalização, então: C = 2 * W bauds = 2 * W * log2(L) bps Assim, considerando
    a largura de banda (W) de 3 KHz e 16 níveis de sinalização (L), a taxa de transmissão
    máxima é: C = 2 * W * log2(L) = 2 * 3000 * log2(16) = 6000 * 4 = 24.000 bps Logo,
    a taxa de transmissão máxima é de 24.000 bps ou 24 kbps. B. Considerando que a
    relação sinal-ruído (em decibéis) é dada por 10 * log10(S/N), então: 10 * log10(S/N)
    = 30,1 log10(S/N) = 3,01 S/N = 1.023 Assim, considerando a largura de banda (W)
    de 3 KHz e uma relação sinal-ruído (S/N) de 1023, a taxa de transmissão máxima
    é: C = W * log2 (1 + S/N) = 3.000 * log2 (1 + 1.023) = 3.000 * log2 (1.024) =
    3.000 * 10 = 30.000 bps Logo, a taxa de transmissão máxima é de 30.000 bps ou
    30 kbps. C. Existem duas notações aceitáveis como padrão de resposta: textual
    e matemática. Notação Textual Na presença de ruído térmico, é possível adotar
    mais de 16 níveis de sinalização. A justificativa é a seguinte: Em decorrência
    do teorema de Nyquist, a taxa de sinalização de qualquer canal deve ser no máximo
    o dobro da largura de banda passante do meio. Neste caso, a taxa de sinalização
    máxima é de 6.000 bauds. Considerando que, na presença de ruído térmico, a taxa
    de transmissão máxima é 30 kbps, pode-se concluir que o número máximo de níveis
    de sinalização que o canal pode comportar é 32 porque cada símbolo transporta
    5 bits gerando uma taxa de transmissão máxima de 30 kbps. Logo, na presença de
    ruído térmico, é possível adotar mais de 16 níveis de sinalização. Notação Matemática
    Considerando que, na presença de ruído térmico, a taxa de transmissão máxima é
    30 kbps, então é possível calcular o número máximo de níveis de sinalização que
    o canal pode comportar da seguinte forma: 2 * W * log2(L) # 30.000 2 * 3.000 *
    log2(L) # 30.000 log2(L) # 5 L # 32 Logo, na presença de ruído térmico, é possível
    adotar mais de 16 níveis de sinalização.'
  assets: []
assets:
- id: figure-01
  type: diagram
  path: enade-2008-computing-d60/figure-01.png
  source_page: 26
  extraction_method: raster_crop
  sha256: d6dcde209e1c2ae27ca0060e4aeda9be12a23163fe973913d1b2e7274cf9277b
  alt_text: null
  caption: null
- id: figure-02
  type: diagram
  path: enade-2008-computing-d60/figure-02.png
  source_page: 26
  extraction_method: raster_crop
  sha256: ebf9b4c11d15ba0d016f77884d142620011901d63f7687b383fe5691d3c3efd4
  alt_text: null
  caption: null
- id: figure-03
  type: diagram
  path: enade-2008-computing-d60/figure-03.png
  source_page: 26
  extraction_method: raster_crop
  sha256: 510f07289ef6cfdf70b41d384755863daecbbf1b5a032a6c0e7a1e1c0f5c7aaa
  alt_text: null
  caption: null
- id: figure-04
  type: diagram
  path: enade-2008-computing-d60/figure-04.png
  source_page: 26
  extraction_method: raster_crop
  sha256: 4331aa937ac88f5102e609ab13f0e861e535332f2640651001c46a98717ec9e1
  alt_text: null
  caption: null
- id: figure-05
  type: diagram
  path: enade-2008-computing-d60/figure-05.png
  source_page: 27
  extraction_method: raster_crop
  sha256: 5bc9ce34c0c7d192695f008786f33d2a3e6ff9da4fe0f5e0a1acadd164b6d967
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
extraction_status: extracted
automatic_validation: passed
visual_validation: not_performed
taxonomy_review_status: pending
---

# Questão 60

![Figura da questão](enade-2008-computing-d60/figure-03.png)

C = 2 × W bauds

C = W × log2 (1 +

Tendo como referência inicial as informações acima, considere que seja necessário determinar a taxa de transmissão máxima de um canal de comunicação que possui largura de banda de 3 kHz, relação sinal-ruído de 30,1 dB e adota 16 diferentes níveis de sinalização. Nessa situação, responda aos seguintes questionamentos.

A Na ausência de ruído, de acordo com o teorema de Nyquist, qual a taxa de transmissão máxima do referido canal, em

![Figura da questão](enade-2008-computing-d60/figure-01.png)

B Na presença de ruído térmico, de acordo com a lei de Shannon, qual a taxa de transmissão máxima do canal, em bits

![Figura da questão](enade-2008-computing-d60/figure-02.png)

C Na presença de ruído térmico, é possível adotar mais de 16 níveis de sinalização no referido canal? Justifique.

![Figura da questão](enade-2008-computing-d60/figure-04.png)

As questões de 61 a 80, a seguir, são específicas para os estudantes de cursos com perfis profissionais de BACHARELADO EM SISTEMAS DE INFORMAÇÃO. Figura para a questão 61 Estágios do ciclo de vida de um serviço de TI Gerenciamento de aplicações Gerente do desenvolvimento de aplicações Negócios Entrega de serviços Gerente de serviços Cliente Usuário

Estratégias, planos e requisitos Soluções de negócios

Definir Planejar Implantar Validar Estabelecer políticas serviços serviços serviços estratégias Desenho e planejamento Implantação Suporte técnico Administração

![Figura da questão](enade-2008-computing-d60/figure-05.png)
