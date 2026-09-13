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
extraction_status: needs_review
automatic_validation: passed
visual_validation: failed
taxonomy_review_status: pending
---

# Questão 60

Para transmissões de sinais em banda base, a largura de banda do canal limita a taxa de transmissão máxima. Como resultado do teorema de Nyquist, na ausência de ruído, a taxa de transmissão máxima C de um canal que possui largura de banda W, em hertz, é dada pela equação a seguir. C = 2 × W bauds No entanto, em qualquer transmissão, o ruído térmico está presente nos dispositivos eletrônicos e meios de transmissão. Esse ruído, causado pela agitação dos elétrons nos condutores, é caracterizado pela potência de ruído N. De acordo com a lei de Shannon, na presença de ruído térmico, a taxa de transmissão máxima de um canal que possui largura de banda W, em hertz, e apresenta uma relação sinal-ruído S/N, expressa em decibel (dB), é definida pela equação abaixo. C = W × log2 (1 + ) bps

Tendo como referência inicial as informações acima, considere que seja necessário determinar a taxa de transmissão máxima de um canal de comunicação que possui largura de banda de 3 kHz, relação sinal-ruído de 30,1 dB e adota 16 diferentes níveis de sinalização. Nessa situação, responda aos seguintes questionamentos.

A Na ausência de ruído, de acordo com o teorema de Nyquist, qual a taxa de transmissão máxima do referido canal, em bits por segundo. Apresente os cálculos necessários.

B Na presença de ruído térmico, de acordo com a lei de Shannon, qual a taxa de transmissão máxima do canal, em bits por segundo? Apresente os cálculos necessário e considere que log10 (1.023) = 3,01.

C Na presença de ruído térmico, é possível adotar mais de 16 níveis de sinalização no referido canal? Justifique. (valor: 3,0 pontos)

(valor: 3,0 pontos)

(valor: 4,0 pontos)

Figura para a questão 61 Estágios do ciclo de vida de um serviço de TI Gerenciamento de aplicações Gerente do desenvolvimento de aplicações Negócios Entrega de serviços Gerente de serviços Cliente Usuário

Estratégias, planos e requisitos Soluções de negócios

Definir Planejar Implantar Validar Estabelecer políticas serviços serviços serviços estratégias Desenho e planejamento Implantação Suporte técnico Administração
