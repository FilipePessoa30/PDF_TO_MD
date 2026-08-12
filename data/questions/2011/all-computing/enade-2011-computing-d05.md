---
id: enade-2011-computing-d05
exam_year: 2011
source_occurrences:
- exam_id: enade-2011-unificado
  pdf_sha256: eb3b497f0d0967b1b6d063784c3012e719d1758ba182e4f6d6e6e47151934548
  source_path: 2011/1_prova.pdf
  pages:
  - 20
  question_number: 5
  section: componente-especifico-comum-discursiva
applicable_courses:
- all-computing
section: componente-especifico-comum-discursiva
question_number: 5
question_type: discursive
content_blocks: null
correct_answer: null
official_answer_source: null
answer_validation_status: not_applicable
answer_standard:
  source_path: 2011/3_padrao.pdf
  pdf_sha256: 386353635a8e2fa8081dce177f37918bcaf9426d8ee6881b88aa739bdf0cd412
  pages:
  - 4
  - 5
  text: 'Em cada um dos mapeamentos o participante do exame deve indicar claramente
    como calcular o endereço de um determinado bloco da memória principal na memória
    cache. Isso pode ser feito pela divisão do endereço de 32 bits em campos (Palavra,
    Linha, Rótulo e Conjunto) ou por uma breve descrição de como cada campo é usado,
    incluindo seu tamanho. A seguir são apresentadas descrições detalhadas de cada
    esquema, visando facilitar a correção do item. A resposta, portanto, não precisa
    incluir todas as informações de cada esquema, mas deve diferenciá‐los claramente.
    Mapeamento direto: No mapeamento direto cada bloco da memória principal é mapeado
    em uma única posição da cache e seu endereço deve ser dividido da seguinte forma:
    Rótulo Linha Palavra


    Dois bits são usados para identificar a palavra (byte) dentro do bloco (ou linha).
    São necessários 17 bits para determinar em qual das 128K linhas da cache o bloco
    será mapeado. Os 13 bits mais significativos do endereço devem ser comparados
    com o rótulo da cache naquela linha para saber se aquele é o bloco atualmente
    mapeado. Mapeamento totalmente associativo: No mapeamento totalmente associativo
    cada bloco da memória principal pode ser mapeado em qualquer posição da cache
    e seu endereço deve ser dividido da seguinte forma: Rótulo Palavra


    Dois bits são usados para identificar a palavra dentro do bloco. Todos os demais
    bits (30) são usados como rótulo para identificar o bloco na memória cache. Mapeamento
    associativo por conjunto: No mapeamento associativo por conjunto (4 vias) cada
    bloco da memória principal é mapeado em um conjunto com 4 linhas e seu endereço
    deve ser dividido da seguinte forma: Rótulo Conjunto Palavra


    Dois bits são usados para identificar a palavra dentro do bloco. São necessários
    15 bits para determinar em qual dos 32K conjuntos o bloco será mapeado. Os 15
    bits mais significativos do endereço devem ser comparados com os rótulos da cache
    naquele conjunto para saber se o bloco está atualmente mapeado. Vantagens e desvantagens:
    O mapeamento direto é o mais simples de ser implementado e o circuito resultante
    é mais rápido e não requer algoritmo de substituição. Entretanto, em geral, as
    taxas de acertos (cache hit) são menores.


    O mapeamento totalmente associativo é o que tem as maiores taxas de acerto. Entretanto,
    é o mais complexo dos três. Os circuitos resultantes são maiores, mais caros e
    mais lentos. Além disso, requer um algoritmo de substituição. Normalmente esse
    mapeamento é utilizado em memórias cache de pequena capacidade.


    O mapeamento associativo por conjunto é uma solução de compromisso (trade‐off)
    entre as duas opções anteriores. Tem como vantagens ser mais simples que o totalmente
    associativo e, em geral, mais eficiente, em termos de taxas de acerto, do que
    o mapeamento direto.'
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

# Questão 5

As memórias cache são usadas para diminuir o tempo de acesso à memória principal, mantendo cópias de seus dados. Uma função de mapeamento é usada para determinar em que parte da memória cache um dado da memória principal será mapeado. Em certos casos, é necessário usar um algoritmo de substituição para determinar qual parte da cache será substituída. Suponha uma arquitetura hipotética com as seguintes características: • A memória principal possui 4 Gbytes, em que cada byte é diretamente endereçável com um endereço 32 bits. • A memória cache possui 512 Kbytes, organizados em 128 K linhas de 4 bytes. • Os dados são transferidos entre as duas memórias em blocos de 4 bytes. Considerando os mapeamentos direto, totalmente associativo e associativo por conjuntos (em 4 vias), redija um texto que contemple as organizações dessas memórias, demonstrando como são calculados os endereços das palavras, linhas (blocos), rótulos (tags) e conjunto na memória cache em cada um dos três casos. Cite as vantagens e desvantagens de cada função de mapeamento, bem como a necessidade de algoritmos de substituição em cada uma delas. (valor: 10,0 pontos)
