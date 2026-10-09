# ESPECIFICAÇÃO DO BOTÃO DE CATÁLOGO COMPLETO

## 1. OBJETIVO
Permitir que o usuário visualize todos os itens do catálogo em qualquer momento, mesmo sem busca ativa, para conferência e comparação futura.



## 4. CONTEÚDO DO CATÁLOGO COMPLETO
- Deve listar todos os produtos do catálogo, sem marcações de busca.
- Cada item deve ser apresentado como tile contendo: id, nombre, precio.
- Não devem ser aplicadas classes de origem (`source-keyword`, `source-laya`, `source-both`).
- Não devem ser exibidos badges de ranking nem níveis `lv0..lv3`.
- A lista deve ser em grid, reutilizando o estilo existente de `.tile`, mas de forma neutra.


## 6. COMPORTAMENTO DO CATÁLOGO POR CATEGORIA (FIXO À ESQUERDA)
- O catálogo completo deve permanecer fixo no lado esquerdo da tela.
- Os produtos devem ser agrupados e exibidos de acordo com a categoria.
- O catálogo **não deve exibir nenhuma marcação de busca** (sem bordas verdes, sem transparência, sem badges).
- A visualização lateral por categoria deve ser mantida mesmo durante a busca.

## 7. CRITÉRIOS DE ACEITAÇÃO

- Em telas pequenas, o grid do catálogo completo se adapta sem quebrar o layout.
- O catálogo lateral fixo à esquerda respeita agrupamento por categoria.
- O catálogo mantém aparência neutra em todo momento, independentemente de buscas realizadas.
