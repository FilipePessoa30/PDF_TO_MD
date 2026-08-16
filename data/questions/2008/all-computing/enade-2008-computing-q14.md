---
id: enade-2008-computing-q14
exam_year: 2008
source_occurrences:
- exam_id: enade-2008-b-computacao
  pdf_sha256: 5c8a08f7fdaccaa3b5661f40705e214bffdab634b845bce6288f8eeaa25db264
  source_path: 2008/b1_prova.pdf
  pages:
  - 8
  - 9
  question_number: 14
  section: nucleo-comum-objetiva
applicable_courses:
- all-computing
section: nucleo-comum-objetiva
question_number: 14
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
extraction_status: extracted
automatic_validation: passed
visual_validation: not_performed
taxonomy_review_status: pending
---

# Questão 14

Um programador propôs um algoritmo não-recursivo para o percurso em preordem de uma árvore binária com as seguintes características. < Cada nó da árvore binária é representado por um registro com três campos: chave, que armazena seu identificador; esq e dir, ponteiros para os filhos esquerdo e direito, respectivamente. < O algoritmo deve ser invocado inicialmente tomando o ponteiro para o nó raiz da árvore binária como argumento. < O algoritmo utiliza push() e pop() como funções auxiliares de empilhamento e desempilhamento de ponteiros para nós de árvore binária, respectivamente. A seguir, está apresentado o algoritmo proposto, em que 8 representa o ponteiro nulo. Procedimento preordem (ptraiz : PtrNoArvBin) Var ptr : PtrNoArvBin; ptr := ptraiz; Enquanto (ptr … 8) Faça escreva (ptr8.chave); Se (ptr8.dir … 8) Então push(ptr8.dir); Se (ptr8.esq … 8) Então push(ptr8.esq); ptr := pop(); Fim_Enquanto Fim_Procedimento Com base nessas informações e supondo que a raiz de uma árvore binária com n nós seja passada ao procedimento preordem(), julgue os itens seguintes. I O algoritmo visita cada nó da árvore binária exatamente uma vez ao longo do percurso. II O algoritmo só funcionará corretamente se o procedimento pop() for projetado de forma a retornar 8 caso a pilha esteja vazia. III Empilhar e desempilhar ponteiros para nós da árvore são operações que podem ser implementadas com custo constante. IV A complexidade do pior caso para o procedimento preordem() é O(n). Assinale a opção correta.

## Alternativas

A. Apenas um item está certo.
B. Apenas os itens I e IV estão certos.
C. Apenas os itens I, II e III estão certos.
D. Apenas os itens II, III e IV estão certos.
E. Todos os itens estão certos.
