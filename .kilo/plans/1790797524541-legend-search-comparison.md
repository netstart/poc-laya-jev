# Plano: Especificação e implementação de legendas para busca comparativa

## Contexto
A `spec/002` define o layout comparativo em duas colunas, mas ainda falta documentar e expor ao usuário o significado das cores, badges e comportamento de cada lado. O objetivo é criar uma `spec/003` complementar e implementar duas legendas visuais no frontend: uma por coluna, explicando exatamente o que aparece ali.

## Objetivo
- Criar `.ai/spec/003-legendas-resultados-busca-comparativa.md`
- Implementar legendas explicativas no frontend, uma para o Balcão 1 e outra para o Balcão 2

## Decisões
1. **Arquivo da spec**: `.ai/spec/003-legendas-resultados-busca-comparativa.md`
2. **Local das legendas**: imediatamente abaixo de cada `.coluna-header`, dentro de `.coluna`
3. **Conteúdo da legenda esquerda**:
   - Itens encontrados apenas pela busca tradicional
   - Itens encontrados por ambos
   - Números/badges indicam ordem de relevância tradicional
4. **Conteúdo da legenda direita**:
   - Itens encontrados apenas pelo LAYA
   - Itens encontrados por ambos
   - Números/badges indicam ranking LAYA
   - Níveis `lv0..lv3` por score
5. **Estilo**: manter identidade anos 70, texto pequeno, sem poluir a UI
6. **Comportamento separado**: cada lado mostra seus próprios itens; itens em comum aparecem em ambos
7. **Responsivo**: legendas empilham com as colunas em mobile

## Tarefas de implementação
1. **Criar `.ai/spec/003-legendas-resultados-busca-comparativa.md`** com:
   - Objetivo
   - Regras de exibição por lado
   - Significado de cores
   - Significado de números/badges
   - Critérios de aceitação da legenda
   - Comportamento de itens em comum/exclusivos
2. **Atualizar `public/index.html`**:
   - Adicionar `.coluna-legend` abaixo de `.coluna-header` em cada coluna
   - Texto explicativo conforme conteúdo da spec
3. **Atualizar `public/busca.css`**:
   - `.coluna-legend` com estilo discreto, fonte pequena, cor muted
   - Garantir que `.columns` empilhe em mobile
4. **Atualizar `public/app.js`** se necessário**:
   - Garantir que os dados de ambos os lados estejam disponíveis para a legenda
   - Nenhuma alteração estrutural deve ser necessária; a lógica de renderização já separa os lados
5. **Validação**:
   - `node --check public/app.js`
   - Inspeção manual do HTML/CSS
   - Backend health check

## Validação
- Sintaxe JS OK
- Backend health OK
- Spec 003 criada e consistente com spec 002
- Frontend reflete a spec 003 sem quebrar layout existente

## Fora de escopo
- Alterar backend
- Mudar paleta de cores existente
- Implementar filtros ou ordenação adicional
