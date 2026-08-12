---
id: enade-2011-computing-d04
exam_year: 2011
source_occurrences:
- exam_id: enade-2011-unificado
  pdf_sha256: eb3b497f0d0967b1b6d063784c3012e719d1758ba182e4f6d6e6e47151934548
  source_path: 2011/1_prova.pdf
  pages:
  - 19
  question_number: 4
  section: componente-especifico-comum-discursiva
applicable_courses:
- all-computing
section: componente-especifico-comum-discursiva
question_number: 4
question_type: discursive
content_blocks: null
correct_answer: null
official_answer_source: null
answer_validation_status: not_applicable
answer_standard:
  source_path: 2011/3_padrao.pdf
  pdf_sha256: 386353635a8e2fa8081dce177f37918bcaf9426d8ee6881b88aa739bdf0cd412
  pages:
  - 3
  text: 'a) registro nodo com campos: chave do tipo inteiro; esq e dir do tipo apontadores
    para registro nodo. Qualquer notação em português estruturado, de forma imperativa
    ou orientada a objetos deve ser considerada, assim como em uma linguagem de alto
    nível como o Pascal, C e Java. O importante é a presença dos campos sublinhados
    e do uso de apontadores ou autoreferências. b) função CriaABP(v: vetor de inteiros;
    i, j: inteiros) retorna apontador para registro nodo // i,j são os índices inicial
    e final do vetor | Cria novo nodo apontado por p, o qual deve ser uma variável
    local | pos = (i + j) / 2 // determina a posição central do vetor | p‐>chave =
    v[pos] // guarda o elemento v[pos] no novo nodo criado | se i < j entao // ainda
    não se está no nível das folhas | | p‐>esq = CriaABP(v, i, pos‐1 ) // chama recursivamente
    para a sub‐árvore da esquerda | | p‐>dir = CriaABP(v, pos+1, j ) // chama recursivamente
    para a sub‐árvore da direita | senão p‐>esq = p‐>dir = NULL // nível das folhas
    | retorna p


    Chamada principal: raiz = CriaABP(v, 1,n ) onde raiz aponta para o nodo raiz da
    árvore. Qualquer notação em português estruturado, de forma imperativa ou orientada
    a objetos deve ser considerada, assim como em uma linguagem de alto nível como
    o Pascal, C e Java. A função deve ser recursiva e não pode usar comparações para
    encontrar o elemento a ser inserido, nem utilizar operações de inserção que façam
    comparações implicitamente. A condição de parada da recursão (nível das folhas)
    deve estar clara e os parâmetros para chamada recursiva devem estar corretos.
    Os apontadores dos nodos‐folhas devem ser aterrados.'
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
extraction_status: verified
automatic_validation: passed
visual_validation: passed
taxonomy_review_status: pending
---

# Questão 4

Listas ordenadas implementadas com vetores são estruturas de dados adequadas para a busca binária, mas possuem o inconveniente de exigirem custo computacional de ordem linear para a inserção de novos elementos. Se as operações de inserção ou remoção de elementos forem frequentes, uma alternativa é transformar a lista em uma árvore binária de pesquisa balanceada, que permitirá a execução dessas operações com custo logarítmico. Considerando essas informações, escreva um algoritmo recursivo que construa uma árvore binária de pesquisa completa, implementada por estruturas auto-referenciadas ou apontadores, a partir de um vetor ordenado, v, de n inteiros, em que n = 2m - 1, m > 0. O algoritmo deve construir a árvore em tempo linear, sem precisar fazer qualquer comparação entre os elementos do vetor, uma vez que este já está ordenado. Para isso, a) descreva a estrutura de dados utilizada para a implementação da árvore (valor = 2,0 pontos) b) escreva o algoritmo para a construção da árvore. A chamada principal à função recursiva deve passar, como parâmetros, o vetor, índice do primeiro e último elementos, retornando a referência ou apontador para a raiz da árvore criada (valor: 8,0 pontos). Observação: Qualquer notação em português estruturado, de forma imperativa ou orientada a objetos deve ser considerada, assim como em uma linguagem de alto nível, como o Pascal, C e Java.
