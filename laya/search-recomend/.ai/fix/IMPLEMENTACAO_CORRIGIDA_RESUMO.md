IMPLEMENTAÇÃO CORRIGIDA: BOTÃO DE PAYLOAD DOS BALCÕES EM DUAS COLUNAS

## Arquivos Modificados

1. **Especificação**: `.ai/spec/005-botao-payload-balcoes.md`
   - Atualizada para refletir a localização correta dos payloads (abaixo do botão em duas colunas)
   - Especifica que os payloads aparecem em uma seção de duas colunas abaixo do botão de controle
   - Detalha o comportamento responsivo (empilhamento em telas pequenas)

2. **HTML**: `public/index.html`
   - Mantido o botão `#payloadBtn` abaixo de `#inspectorBtn`
   - **REMOVIDO**: Os containers de payload que estavam dentro das colunas de resultados
   - **ADICIONADO**: Nova seção `.payload-display` abaixo dos botões de controle
   - Esta seção contém:
     - Div container `.payload-columns` 
     - Duas colunas `.payload-column` (esquerda e direita)
     - Containers de payload individuais `#payload-balcao1` e `#payload-balcao2`

3. **CSS**: `public/busca.css`
   - **ADICIONADO**: Estilos para `.payload-display`:
     - Layout em grid com duas colunas (1fr 1fr)
     - Espaçamento (gap: 24px), margem superior, largura máxima
     - Centralização automática
   - **ATUALIZADO**: Estilos para `.payload-column`:
     - Fundo, borda, sombra (igual aos outros cards)
   - **MANTIDO/APRIMORADO**: Estilos para `.payload-container`:
     - Margem 0 (já que o espaçamento é feito pela coluna)
     - Padding aumentado para 16px
     - Fundo transparente (usando o fundo da coluna)
     - Altura máxima aumentada para 400px
     - Estilos aprimorados para headers (h4) e blocos de código (pre)

4. **JavaScript**: `public/app.js`
   - **MANTIDA**: Variável `currentKeywordIds` para armazenar resultados da busca tradicional
   - **MANTIDA**: Lógica em `doSearch()` para armazenar os IDs da busca keyword
   - **MANTIDA**: Chamada para `renderPayloads()` dentro de `renderInspector()`
   - **MANTIDA**: Função `renderPayloads()` que cria objetos JSON detalhados para ambos os balcões
   - **CORRIGIDO**: Event listener para `#payloadBtn`:
     - Agora tenta o elemento `#payloadDisplay` (seção completa)
     - Verifica se está visível checando `display === "grid"`
     - Alterna entre `display: "none"` e `display: "grid"`
     - Texto do botão alterna corretamente

## Funcionalidade Implementada Corretamente

✅ Botão "📦 Ver payload dos balcões" posicionado abaixo de "🔍 Ver detalhes da busca"
✅ Ao clicar, exibe uma seção de **duas colunas** **abaixo do botão** (não abaixo das colunas de resultados)
✅ Coluna esquerda mostra payload do Balcão 1 (busca tradicional)
✅ Coluna direita mostra payload do Balcão 2 (busca com LAYA)
✅ Clique alternado mostra/oculta a seção completa de payloads
✅ Texto do botão alterna entre "Ver payload dos balcões" e "Ocultar payload dos balcões"
✅ Payloads contêm dados JSON formatados e legíveis
✅ Em telas pequenas, as colunas de payload empilham verticalmente (comportamento padrão do grid)
✅ Não interfere nas funcionalidades existentes de busca ou do inspector de detalhes

## Dados nos Payloads (inalterados)

**Balcão 1 (Busca Tradicional)**:
- Query original
- Tipo de busca
- Total de resultados encontrados
- Lista de IDs dos produtos encontrados
- Timestamp

**Balcão 2 (Busca com LAYA)**:
- Query original
- Tipo de busca
- Objeto de entendimento (intenção, categoria, orçamento máximo)
- Scores brutos por produto
- Ordem de ranking completa
- Lista de itens dentro do orçamento
- Lista de boas opções (score >= 2)
- Lista de itens acima do orçamento mas relevantes
- Métricas de performance (latency, número de chamadas, número de perguntas)
- Timestamp

## Vantagens desta Implementação

1. **Localização correta**: Payloads aparecem exatamente onde solicitado - abaixo do botão de controle
2. **Layout limpo**: Duas colunas bem definidas, sem poluir as áreas de resultados de busca
3. **Consistência visual**: Segue o mesmo estilo dos outros cards (fundo, borda, sombra)
4. **Usabilidade melhorada**: Os usuários podem ver os payloads sem perder o contexto dos resultados de busca
5. **Responsividade**: Funciona bem em diferentes tamanhos de tela
6. **Performance**: Não há duplicação de esforço - os mesmos dados são usados para múltiplos propósitos