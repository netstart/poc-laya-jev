# Plano: Botão de catálogo completo

## Contexto
Após a busca, o usuário precisa de uma forma rápida de conferir todos os produtos sem marcações de busca. A spec atual não cobre esse comportamento.

## Objetivo
- Criar a especificação do botão toggle de catálogo completo
- Definir comportamento, localização, estilo e critérios de aceitação

## Decisões
1. **Local do botão**: imediatamente após o inspetor, dentro de `.resultados`
2. **Estado inicial**: oculto
3. **Alternância**: clique exibe/oculta o catálogo completo
4. **Conteúdo**: grid com todos os produtos do catálogo, sem badges, sem `source-*`, sem `lv*`
5. **Dados**: reutilizar `catalogo` já carregado no frontend
6. **Estilo**: manter identidade anos 70, discreto
7. **Responsivo**: grid adapta em mobile

## Tarefas
1. **Escrever a spec em `.ai/spec/004-botao-catalogo-completo.md`** com:
   - objetivo
   - comportamento
   - localização
   - conteúdo do catálogo
   - texto do botão
   - critérios de aceitação
2. **Atualizar `public/index.html`**:
   - adicionar container de catálogo completo
   - adicionar botão toggle
3. **Atualizar `public/busca.css`**:
   - estilo do container e botão
   - grid neutro para tiles sem marcação
4. **Atualizar `public/app.js`**:
   - função `renderFullCatalog()`
   - toggle de visibilidade
   - atualização do texto do botão

## Validação
- `node --check public/app.js`
- inspeção manual do HTML/CSS
- backend health check

## Fora de escopo
- persistência do estado
- paginação
- filtros no catálogo completo
