---
id: enade-2021-cc-b-d05
exam_year: 2021
source_occurrences:
- exam_id: enade-2021-b
  pdf_sha256: 0254b274cc4adddbb503cf18553ee70c26014cbb0848fe3c5b787c80137b11e8
  source_path: 2021/b1_prova.pdf
  pages:
  - 17
  - 18
  question_number: 5
  section: componente-especifico-discursiva
applicable_courses:
- ciencia-da-computacao-bacharelado
section: componente-especifico-discursiva
question_number: 5
question_type: discursive
correct_answer: null
official_answer_source: null
answer_validation_status: not_applicable
answer_standard:
  source_path: 2021/b3_padrao.pdf
  pdf_sha256: c0348ce0006201f25e9f97502f59ad1b802c6c3e83c232b9c3c8330f6a6e7ded
  pages:
  - 8
  text: 'a) O respondente deve mostrar que após a execução da função buildHeap o arranjo
    ficará da seguinte forma: {34, 21, 8, 13, 2, 1, 3, 5}. b) O respondente deve apresentar
    que no pior caso para a função heapify a complexidade de tempo ficará da seguinte
    forma: O(log n), sendo n o número de elementos do heap.'
assets:
- id: figure-01
  type: diagram
  path: enade-2021-cc-b-d05/figure-01.png
  source_page: 17
  extraction_method: raster_crop
  sha256: d06012c0e6fb71b67c99c93c9e67381cedb35d1b0f55061e1844ed84cd73b8b7
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
automatic_validation: failed
visual_validation: failed
taxonomy_review_status: pending
---

# Questão 5

![Figura da questão](enade-2021-cc-b-d05/figure-01.png)

máximo especifica que um nó filho (no código calculado pelas funções left e right) tem sempre armazenado um valor menor ou igual ao seu pai. CORMEN, T. H.; LEISERSON, C. E.; RIVEST, R. L.; STEIN, C. Introduction to Algorithms. 3. ed. MIT Press and McGraw-Hill. p. 131-161, 2009 (adaptado). Considerando a implementação a seguir, o heapify é uma função auxiliar para reorganizar o arranjo (garantindo a propriedade de heap máximo em uma determinada posição do arranjo) e buildHeap é uma função que usa heapify para reorganizar todas as posições do arranjo (garantindo a propriedade de heap máximo para todos os elementos).

```
}
/a - arranjo, n - número de elementos */
void buildHeap(int *a, int n)
{
   int i;
   for (i = (n-1)/2; i >= 0; i--)
      heapify(a, n, i);
}
```

De acordo com as informações apresentadas, faça o que se pede nos itens a seguir. a) Como ficará o arranjo int a[ ] = {2, 5, 8 ,13, 21, 1, 3, 34} após a execução da função buildHeap(a, 8). (valor: 5,0 pontos) b) Apresente a complexidade de tempo no pior caso para a função heapify, use a notação O ou Q. (valor: 5,0 pontos)
