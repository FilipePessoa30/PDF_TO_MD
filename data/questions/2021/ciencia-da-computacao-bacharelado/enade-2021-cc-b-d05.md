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
content_blocks:
- type: paragraph
  text: Um heap binário é um arranjo que pode ser visualizado como uma árvore binária,
    sendo que cada nó da árvore corresponde a um elemento do arranjo, como pode ser
    observado na figura a seguir.
- type: asset
  asset_id: figure-01
- type: paragraph
  text: 'Percebe-se que existem dois tipos de heaps: heaps máximo e heaps mínimo.
    O heap máximo é uma estrutura de dados que possibilita a consulta ou extração
    de forma eficiente do maior elemento de uma coleção. A propriedade de heap máximo
    especifica que um nó filho (no código calculado pelas funções left e right) tem
    sempre armazenado um valor menor ou igual ao seu pai. CORMEN, T. H.; LEISERSON,
    C. E.; RIVEST, R. L.; STEIN, C. Introduction to Algorithms. 3. ed. MIT Press and
    McGraw-Hill. p. 131-161, 2009 (adaptado). Considerando a implementação a seguir,
    o heapify é uma função auxiliar para reorganizar o arranjo (garantindo a propriedade
    de heap máximo em uma determinada posição do arranjo) e buildHeap é uma função
    que usa heapify para reorganizar todas as posições do arranjo (garantindo a propriedade
    de heap máximo para todos os elementos).'
- type: code
  text: "int left(int i) { return (2 * i + 1); }\nint right(int i) { return (2 * i\
    \ + 2); }\n/* a - arranjo, n - número de elementos,\ni - posição do elemento que\
    \ deve ser\ncolocado em propriedade de heap */\nvoid heapify (int *a, int n, int\
    \ i)\n{\n   int e, d, max, aux;\n\n   e = left(i);\n   d = right(i);\n   if (e\
    \ < n && a[e] > a[i])\n      max = e;\n   else\n      max = i;\n   if (d < n &&\
    \ a[d] > a[max])\n      max = d;\n   if (max != i)\n   {\n      aux = a[i];\n\
    \      a[i] = a[max];\n      a[max] = aux;\n      heapify(a, n, max);\n   }\n\
    }\n/a - arranjo, n - número de elementos */\nvoid buildHeap(int *a, int n)\n{\n\
    \   int i;\n   for (i = (n-1)/2; i >= 0; i--)\n      heapify(a, n, i);\n}"
  language: null
- type: paragraph
  text: 'De acordo com as informações apresentadas, faça o que se pede nos itens a
    seguir. a) Como ficará o arranjo int a[ ] = {2, 5, 8 ,13, 21, 1, 3, 34} após a
    execução da função buildHeap(a, 8). (valor: 5,0 pontos) b) Apresente a complexidade
    de tempo no pior caso para a função heapify, use a notação O ou Q. (valor: 5,0
    pontos)'
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
  assets: []
assets:
- id: figure-01
  type: diagram
  path: enade-2021-cc-b-d05/figure-01.png
  source_page: 17
  extraction_method: raster_crop
  sha256: b5e2f7cc359d586daf48ec0ddaac914a7bf5343c4f7919fa0acc38d69b4789c9
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

# Questão 5

Um heap binário é um arranjo que pode ser visualizado como uma árvore binária, sendo que cada nó da árvore corresponde a um elemento do arranjo, como pode ser observado na figura a seguir.

![Figura da questão](enade-2021-cc-b-d05/figure-01.png)

Percebe-se que existem dois tipos de heaps: heaps máximo e heaps mínimo. O heap máximo é uma estrutura de dados que possibilita a consulta ou extração de forma eficiente do maior elemento de uma coleção. A propriedade de heap máximo especifica que um nó filho (no código calculado pelas funções left e right) tem sempre armazenado um valor menor ou igual ao seu pai. CORMEN, T. H.; LEISERSON, C. E.; RIVEST, R. L.; STEIN, C. Introduction to Algorithms. 3. ed. MIT Press and McGraw-Hill. p. 131-161, 2009 (adaptado). Considerando a implementação a seguir, o heapify é uma função auxiliar para reorganizar o arranjo (garantindo a propriedade de heap máximo em uma determinada posição do arranjo) e buildHeap é uma função que usa heapify para reorganizar todas as posições do arranjo (garantindo a propriedade de heap máximo para todos os elementos).

```
int left(int i) { return (2 * i + 1); }
int right(int i) { return (2 * i + 2); }
/* a - arranjo, n - número de elementos,
i - posição do elemento que deve ser
colocado em propriedade de heap */
void heapify (int *a, int n, int i)
{
   int e, d, max, aux;

   e = left(i);
   d = right(i);
   if (e < n && a[e] > a[i])
      max = e;
   else
      max = i;
   if (d < n && a[d] > a[max])
      max = d;
   if (max != i)
   {
      aux = a[i];
      a[i] = a[max];
      a[max] = aux;
      heapify(a, n, max);
   }
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
