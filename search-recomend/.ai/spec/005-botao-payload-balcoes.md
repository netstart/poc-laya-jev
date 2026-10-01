# ESPECIFICAÇÃO DO BOTÃO DE PAYLOAD DOS BALCÕES

## 1. OBJETIVO
Adicionar um botão para exibir/ocultar o payload da busca de cada balcão (Balcão 1 e Balcão 2) em duas colunas, alinhadas com as colunas de resultados acima.

## 2. LOCALIZAÇÃO DO BOTÃO
- O botão deve ficar **abaixo do botão "Ver detalhes da busca"** (que já existe com id `inspectorBtn`)
- O novo botão deve ter o texto: **"Ver payload dos balcões"**
- ID sugerido: `payloadBtn`

## 3. LOCALIZAÇÃO DOS PAYLOADS
- Os payloads devem aparecer em **uma seção de duas colunas** que fica **diretamente abaixo das colunas de resultados** (não centralizada de forma independente)
- A seção de payloads deve estar **dentro do container `.resultados`** para herdar o alinhamento
- Deve estar **posicionada após o `.columns` div** e antes do `.footer`
- Coluna esquerda: payload do Balcão 1 (busca tradicional)
- Coluna direita: payload do Balcão 2 (busca com LAYA)
- Container geral: `payloadDisplay` com classe `payload-display`
- Colunas: `payload-column` com classe `payload-column`
- Containers individuais: `payload-balcao1` e `payload-balcao2` com classe `payload-container`

## 4. ALINHAMENTO COM COLUNAS DE PRODUTOS
- A seção de payloads deve ter **o mesmo `max-width`** das colunas de resultados (1100px)
- Deve ter **o mesmo `padding` lateral** (16px) para alinhar perfeitamente
- Deve usar **o mesmo layout de grid** (1fr 1fr com gap de 24px)
- Deve estar **centralizada** com `margin: 0 auto` (herdado do container pai)
- O resultado é que as colunas de payload ficam **exatamente alinhadas** com as colunas de produtos acima

## 5. COMPORTAMENTO
- **Estado inicial**: payloads ocultos (seção de duas colunas não visível)
- **Ao clicar uma vez**: exibe a seção de duas colunas com:
  - Coluna esquerda: payload do Balcão 1
  - Coluna direita: payload do Balcão 2
- **Ao clicar novamente**: oculta a seção de duas colunas
- O botão deve alternar o texto entre "Ver payload dos balcões" e "Ocultar payload dos balcões"

## 6. ESTRUTURA DOS PAYLOADS

### 6.1 Payload do Balcão 1 (Busca Tradicional)
Deve conter:
- Query original
- IDs encontrados
- Quantidade de resultados
- Tempo de resposta (se disponível)

### 6.2 Payload do Balcão 2 (Busca com LAYA)
Deve conter:
- Query original
- Entendimento (intenção, categoria, orçamento máximo, etc.)
- Scores brutos por item
- Ordem de ranking
- Itens "within" (dentro do orçamento)
- Itens "good" (boas opções - score >= 2)
- Itens "over" (acima do orçamento mas relevantes)
- Métricas: latency_ms, n_chamadas, n_perguntas

## 7. POSICIONAMENTO VISUAL
- Seção de payloads deve usar CSS Grid para layout de duas colunas
- Cada payload deve estar em um container com:
  - Fundo claro
  - Borda
  - Padding adequado
  - Título em letras maiúsculas
  - Conteúdo JSON formatado em bloco de código com scroll horizontal se necessário
  - Altura máxima com scroll vertical quando o conteúdo exceder
- Devem ser inicialmente ocultas (`display: none` para a seção geral)

## 8. RESPONSIVIDADE
- Em telas pequenas, as duas colunas de payload devem empilhar verticalmente
- O alinhamento com as colunas de resultados deve ser mantido em todos os tamanhos de tela

## 9. CRITÉRIOS DE ACEITAÇÃO
- [ ] Botão "Ver payload dos balcões" aparece abaixo de "Ver detalhes da busca"
- [ ] Ao clicar, exibe seção de duas colunas alinhada com as colunas de resultados acima
- [ ] Coluna esquerda mostra payload do Balcão 1
- [ ] Coluna direita mostra payload do Balcão 2
- [ ] As colunas de payload têm a mesma largura e alinhamento das colunas de produtos acima
- [ ] Payloads mostram dados JSON formatados e legíveis
- [ ] Segundo clique oculta a seção de payloads
- [ ] Texto do botão alterna corretamente
- [ ] Em telas pequenas, as colunas empilham verticalmente mantendo o alinhamento
- [ ] Funciona em desktop e mobile
- [ ] Não quebra funcionalidades existentes