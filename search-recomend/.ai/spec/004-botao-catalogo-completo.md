# ESPECIFICAÇÃO DO BOTÃO DE CATÁLOGO COMPLETO

## 1. OBJETIVO
Permitir que o usuário visualize todos os itens do catálogo em qualquer momento, mesmo sem busca ativa, para conferência e comparação futura.

## 2. COMPORTAMENTO
- Ao final da página de resultados, deve existir um botão alternável.
- Por padrão, o catálogo completo está oculto.
- O clique no botão exibe todos os itens do catálogo.
- Um segundo clique oculta novamente o catálogo completo.
- O estado de visibilidade é local na sessão e não persiste entre recarregamentos.

## 3. LOCALIZAÇÃO NA UI
O botão deve aparecer imediatamente após o inspetor e antes do fechamento da seção `.resultados`.

## 4. CONTEÚDO DO CATÁLOGO COMPLETO
- Deve listar todos os produtos do catálogo, sem marcações de busca.
- Cada item deve ser apresentado como tile contendo: id, nombre, precio.
- Não devem ser aplicadas classes de origem (`source-keyword`, `source-laya`, `source-both`).
- Não devem ser exibidos badges de ranking nem níveis `lv0..lv3`.
- A lista deve ser em grid, reutilizando o estilo existente de `.tile`, mas de forma neutra.

## 5. TEXTO DO BOTÃO
- Estado oculto: "Ver catálogo completo"
- Estado visível: "Ocultar catálogo completo"

## 6. CRITÉRIOS DE ACEITAÇÃO
- O botão existe e está visível apenas dentro da seção de resultados.
- O catálogo completo permanece oculto por padrão.
- O clique alterna corretamente entre mostrar e ocultar.
- Os itens exibidos não carregam nenhuma marcação de busca.
- O estilo visual permanece consistente com a identidade anos 70 do projeto.
- Em telas pequenas, o grid do catálogo completo se adapta sem quebrar o layout.
