---
id: enade-2008-computing-q52
exam_year: 2008
source_occurrences:
- exam_id: enade-2008-b-computacao
  pdf_sha256: 5c8a08f7fdaccaa3b5661f40705e214bffdab634b845bce6288f8eeaa25db264
  source_path: 2008/b1_prova.pdf
  pages:
  - 22
  question_number: 52
  section: engenharia-computacao-objetiva
applicable_courses:
- engenharia-da-computacao
section: engenharia-computacao-objetiva
question_number: 52
question_type: multiple_choice
content_blocks: null
correct_answer: E
official_answer_source: 2008/b2_gabarito.pdf
answer_validation_status: validated
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

# Questão 52

A identificação e o tratamento de erros em programas de computador estão entre as tarefas dos compiladores. Os erros de um programa podem ter variados tipos e precisam ser identificados e tratados em diferentes fases da compilação. Considere uma linguagem de programação que exige que as variáveis manipuladas por seus programas sejam previamente declaradas, não podendo haver duplicidade de identificadores para variáveis em um mesmo escopo. Considere, ainda, que a sintaxe dessa linguagem tenha sido definida por meio de uma gramática livre de contexto e as produções seguintes definam a forma das declarações de variáveis em seus programas. D ÷ TL; | TL; D T ÷ int | real | char L ÷ id | id,L Considere os exemplos de sentenças — I e II — a seguir, com a indicação — entre os delimitadores /* e */ — de diferentes tipos de erros. int: a, b; /* dois pontos após a palavra I int */ int a,b; real a; /* declaração dupla da II variável a */ A partir dessas informações, assinale a opção correta.

## Alternativas

A. A identificação e a comunicação do erro em qualquer uma das sentenças são funções do analisador léxico.
B. O compilador não tem meios para identificar e relatar erros como o da sentença I.
C. A identificação e a comunicação do erro na sentença I são funções da geração de código intermediário.
D. A identificação e a comunicação do erro na sentença II são funções do analisador léxico.
E. A identificação e a comunicação do erro na sentença II são funções da análise semântica.
