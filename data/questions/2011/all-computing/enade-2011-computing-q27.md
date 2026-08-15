---
id: enade-2011-computing-q27
exam_year: 2011
source_occurrences:
- exam_id: enade-2011-unificado
  pdf_sha256: eb3b497f0d0967b1b6d063784c3012e719d1758ba182e4f6d6e6e47151934548
  source_path: 2011/1_prova.pdf
  pages:
  - 16
  question_number: 27
  section: componente-especifico-comum-objetiva
applicable_courses:
- all-computing
section: componente-especifico-comum-objetiva
question_number: 27
question_type: multiple_choice
content_blocks: null
correct_answer: E
official_answer_source: 2011/2_gabarito.pdf
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

# Questão 27

Um dos problemas clássicos da computação científica é a multiplicação de matrizes. Assuma que foram declaradas e inicializadas três matrizes quadradas de ponto flutuante, a, b e c, cujos índices variam entre 0 e n - 1. O seguinte trecho de código pode ser usado para multiplicar matrizes de forma sequencial: 1. for [i = 0 to n - 1] { 2. for [j = 0 to n - 1] { 3. c[i, j] = 0.0; 4. for [k = 0 to n - 1] 5. c[i, j] = c[i, j] + a[i, k] * b[k, j]; 6. } 7. } O objetivo é paralelizar esse código para que o tempo de execução seja reduzido em uma máquina com múltiplos processadores e memória compartilhada. Suponha que o comando “co” seja usado para definição de comandos concorrentes, da seguinte forma: “co [i = 0 to n - 1] { x; y; z;}” cria n processos concorrentes, cada um executando sequencialmente uma instância dos comandos x, y, z contidos no bloco. Avalie as seguintes afirmações sobre o problema. I. Esse problema é exemplo do que se chama “embaraçosamente paralelo”, PORQUE pode ser decomposto em um conjunto de várias operações menores que podem ser executadas independentemente. II. O programa produziria resultados corretos e em tempo menor do que o sequencial, trocando-se o “for” na linha 1 por um “co”. III. O programa produziria resultados corretos e em tempo menor do que o sequencial, trocando-se o “for” na linha 2 por um “co”. IV. O programa produziria resultados corretos e em tempo menor do que o sequencial, trocando-se ambos “for”, nas linhas 1 e 2, por “co”. É correto o que se afirma em

## Alternativas

A. I, II e III, apenas.
B. I, II e IV, apenas.
C. I, III e IV, apenas.
D. II, III e IV, apenas.
E. I, II, III, IV.
