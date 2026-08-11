---
id: enade-2021-cc-b-q20
exam_year: 2021
source_occurrences:
- exam_id: enade-2021-b
  pdf_sha256: 0254b274cc4adddbb503cf18553ee70c26014cbb0848fe3c5b787c80137b11e8
  source_path: 2021/b1_prova.pdf
  pages:
  - 29
  question_number: 20
  section: componente-especifico-objetiva
applicable_courses:
- ciencia-da-computacao-bacharelado
section: componente-especifico-objetiva
question_number: 20
question_type: multiple_choice
content_blocks:
- type: paragraph
  text: Observe o código abaixo escrito na linguagem C.
- type: code
  text: "#include <stdio.h>\n#define TAM 10\nint funcaol(int vetor[], int v){\n  \
    \    int i;\n      for (i = 0; i < TAM; i++){\n            if (vetor[i] == v)\n\
    \                  return i;\n      }\n      return -1;\n}\nint funcao2(int vetor[],\
    \ int v, int i, int f){\n      int m = (i + f) / 2;\n      if (v == vetor[m])\n\
    \            return m;\n      if (i >= f)\n            return -1;\n      if (v\
    \ > vetor[m])\n            return funcao2(vetor, v, m+l, f);\n      else\n   \
    \         return funcao2(vetor, v, i, m-1);\n}\nint main(){\n      int vetor[TAM]\
    \ = {1, 3, 5, 7, 9, 11, 13, 15, 17, 19};\n      printf(“%d - %d”, funcao1(vetor,\
    \ 15), funcao2(vetor, 15, 0, TAM-1));\n      return 0;\n}"
  language: null
- type: paragraph
  text: 'A respeito das funções implementadas, avalie as afirmações a seguir. I. O
    resultado da impressão na linha 24 é: 7 - 7. II. A função funcao1, no pior caso,
    é uma estratégia mais rápida do que a funcao2. III. A função funcao2 implementa
    uma estratégia iterativa na concepção do algoritmo. É correto o que se afirma
    em'
correct_answer: A
official_answer_source: 2021/b2_gabarito.pdf
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

# Questão 20

Observe o código abaixo escrito na linguagem C.

```
#include <stdio.h>
#define TAM 10
int funcaol(int vetor[], int v){
      int i;
      for (i = 0; i < TAM; i++){
            if (vetor[i] == v)
                  return i;
      }
      return -1;
}
int funcao2(int vetor[], int v, int i, int f){
      int m = (i + f) / 2;
      if (v == vetor[m])
            return m;
      if (i >= f)
            return -1;
      if (v > vetor[m])
            return funcao2(vetor, v, m+l, f);
      else
            return funcao2(vetor, v, i, m-1);
}
int main(){
      int vetor[TAM] = {1, 3, 5, 7, 9, 11, 13, 15, 17, 19};
      printf(“%d - %d”, funcao1(vetor, 15), funcao2(vetor, 15, 0, TAM-1));
      return 0;
}
```

A respeito das funções implementadas, avalie as afirmações a seguir. I. O resultado da impressão na linha 24 é: 7 - 7. II. A função funcao1, no pior caso, é uma estratégia mais rápida do que a funcao2. III. A função funcao2 implementa uma estratégia iterativa na concepção do algoritmo. É correto o que se afirma em

## Alternativas

A. I, apenas.
B. III, apenas.
C. I e II, apenas.
D. II e III, apenas.
E. I, II e III.
