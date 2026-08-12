---
id: enade-2021-si-q33
exam_year: 2021
source_occurrences:
- exam_id: enade-2021-s
  pdf_sha256: 13d81a46488d93fb66836e7c704f9de1ba722c3b130ccb4f0aa9d3522c855ba7
  source_path: 2021/s1_prova.pdf
  pages:
  - 36
  - 37
  question_number: 33
  section: componente-especifico-objetiva
applicable_courses:
- sistemas-de-informacao
section: componente-especifico-objetiva
question_number: 33
question_type: multiple_choice
content_blocks:
- type: paragraph
  text: 'Uma abordagem calcula a posição da chave na tabela com base no valor da chave.
    Este valor é a única indicação da posição. Quando a chave é conhecida, a posição
    na tabela pode ser acessada diretamente, sem fazer qualquer outro teste preliminar,
    conforme exigido na busca binária ou durante a pesquisa em uma árvore. Precisamos
    encontrar uma função h que possa transformar uma chave particular K — seja ela
    uma cadeia de caracteres, um número, um registro etc. — em um índice na tabela
    usada para armazenar itens do mesmo tipo que K. A função h é chamada função de
    escrutínio (hash) e não retorna valores únicos. Por exemplo, h(“abc”) = h(“acb”).
    Este problema é chamado colisão. DROZDEK, A. Estrutura de Dados e Algoritmos em
    C++. São Paulo: Cengage do Brasil, p.473, 2016 (adaptado). Uma tabela na qual
    os dados são inseridos em entradas determinadas por uma função h, conforme descrito
    no texto, é chamada de tabela de dispersão ou tabela de espalhamento. A tabela
    de dispersão é representada por meio do vetor tabelaH de T posições, no qual cada
    posição é uma estrutura ItemDado e o procedimento de inserção em tabelaH está
    definido a seguir.'
- type: code
  text: "ItemDado:\n  Chave: inteiro\n  Dado: inteiro\n\n  Prox: ItemDado\nprocedimento\
    \ insere(chave, dado: inteiro)\ninício\n\n  item, temp: ItemDado\n  índice: inteiro\n\
    \n  índice <- h(chave)\n  se tabelaH[índice].chave = -1 então\n\n     tabelaH[índice].chave\
    \ <- chave\n     tabelaH[índice].dado <- dado\n     tabelaH[índice].prox <- NULO\n\
    \  senão\n\n      item.chave <- chave\n      item.dado <- dado\n      item.prox\
    \ <- NULO\n     se tabelaH[índice].prox = NULO então\n       tabelaH[índice].prox\
    \ <- item\n     senão\n\n        temp <- tabelaH[índice].prox\n        enquanto\
    \ temp.prox ≠ NULO faça\n         temp <- temp.prox\n        fimenquanto\n\n \
    \       temp.prox <- item\n      fimse\n  fimse\nfimprocedimento"
  language: null
- type: paragraph
  text: 'O valor -1 no campo chave de uma entrada na tabela significa que aquela entrada
    está livre; o campo Prox com o valor NULO significa que ele não aponta para nenhum
    item de dado. A função h(chave) simplesmente retorna o valor do resto da divisão
    inteira de chave por T. Considerando as informações apresentadas e supondo que
    T = 9, assinale a opção que corresponde ao estado de tabelaH após a seguinte sequência
    de chamadas: insere(13, 6); insere(46, 7); insere(20, 22); insere(28, 25); insere(19,
    26); insere(17, 9).'
- type: asset
  asset_id: figure-01
correct_answer: null
official_answer_source: 2021/s2_gabarito.pdf
answer_validation_status: annulled
answer_standard: null
assets:
- id: figure-01
  type: diagram
  path: enade-2021-si-q33/figure-01.png
  source_page: 37
  extraction_method: raster_crop
  sha256: de0870482647bed3d1a3613d0197bb7ee63557888d6b37f94593be91294caec5
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

# Questão 33

Uma abordagem calcula a posição da chave na tabela com base no valor da chave. Este valor é a única indicação da posição. Quando a chave é conhecida, a posição na tabela pode ser acessada diretamente, sem fazer qualquer outro teste preliminar, conforme exigido na busca binária ou durante a pesquisa em uma árvore. Precisamos encontrar uma função h que possa transformar uma chave particular K — seja ela uma cadeia de caracteres, um número, um registro etc. — em um índice na tabela usada para armazenar itens do mesmo tipo que K. A função h é chamada função de escrutínio (hash) e não retorna valores únicos. Por exemplo, h(“abc”) = h(“acb”). Este problema é chamado colisão. DROZDEK, A. Estrutura de Dados e Algoritmos em C++. São Paulo: Cengage do Brasil, p.473, 2016 (adaptado). Uma tabela na qual os dados são inseridos em entradas determinadas por uma função h, conforme descrito no texto, é chamada de tabela de dispersão ou tabela de espalhamento. A tabela de dispersão é representada por meio do vetor tabelaH de T posições, no qual cada posição é uma estrutura ItemDado e o procedimento de inserção em tabelaH está definido a seguir.

```
ItemDado:
  Chave: inteiro
  Dado: inteiro

  Prox: ItemDado
procedimento insere(chave, dado: inteiro)
início

  item, temp: ItemDado
  índice: inteiro

  índice <- h(chave)
  se tabelaH[índice].chave = -1 então

     tabelaH[índice].chave <- chave
     tabelaH[índice].dado <- dado
     tabelaH[índice].prox <- NULO
  senão

      item.chave <- chave
      item.dado <- dado
      item.prox <- NULO
     se tabelaH[índice].prox = NULO então
       tabelaH[índice].prox <- item
     senão

        temp <- tabelaH[índice].prox
        enquanto temp.prox ≠ NULO faça
         temp <- temp.prox
        fimenquanto

        temp.prox <- item
      fimse
  fimse
fimprocedimento
```

O valor -1 no campo chave de uma entrada na tabela significa que aquela entrada está livre; o campo Prox com o valor NULO significa que ele não aponta para nenhum item de dado. A função h(chave) simplesmente retorna o valor do resto da divisão inteira de chave por T. Considerando as informações apresentadas e supondo que T = 9, assinale a opção que corresponde ao estado de tabelaH após a seguinte sequência de chamadas: insere(13, 6); insere(46, 7); insere(20, 22); insere(28, 25); insere(19, 26); insere(17, 9).

![Figura da questão](enade-2021-si-q33/figure-01.png)

## Alternativas

A. 4 NULO -1 - NULO -1 - NULO -1 - NULO -1 - NULO NULO -1 - NULO NULO -1 - NULO
B. 4 -1 - NULO -1 - NULO NULO -1 - NULO -1 - NULO -1 - NULO -1 - NULO
C. 4 NULO NULO -1 - NULO NULO -1 - NULO NULO NULO NULO
D. 4 NULO NULO -1 - NULO -1 - NULO NULO -1 NULO NULO -1
E. 4 NULO -1 -1 -1 NULO
