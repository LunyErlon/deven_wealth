# Documentação: pagina_rendimentos.py

## Propósito
É o componente responsável pelo gerenciamento de renda passiva (dividendos, rendimentos de FIIs e Juros sobre Capital Próprio - JCP). Permite ao investidor registrar proventos recebidos, visualizar um gráfico do efeito bola de neve ao longo dos meses e gerenciar o histórico de pagamentos com opção de exclusão.

## Como Funciona
Possui a classe principal `PaginaRendimentos(QWidget)` e os componentes do **Radar Automático de Dividendos**:
1. **Radar de Dividendos (Fase 2, 3 e 4)**:
   - **`WorkerRadarDividendos(QThread)`**: Worker em segundo plano que pesquisa proventos recentes sem travar a interface.
   - **`DialogRadarDividendos(QDialog)`**: Pop-up de validação com o conceito de *Atrito Positivo*. Apresenta o ativo, data de pagamento, valor por cota e permite ajustar a **Qtd. Cotas Base** (resolvendo o desafio da *Data-Com*).
   - **Botão Manual (`btn_radar`)**: Permite escanear a B3 sob demanda diretamente no cabeçalho da página.
2. **Formulário de Entrada Manual**:
   - Permite escolher o ativo (filtrado diretamente dos ativos da carteira atual).
   - Data do pagamento (`QDateEdit` com popup de calendário).
   - Tipo de provento (Rendimento, Dividendo, JCP).
   - Quantidade de cotas base e valor líquido total recebido (utilizando os `QDoubleSpinBox` unificados com estilo Catppuccin Macchiato e setas vetoriais).
3. **Lições Didáticas ("Mágica dos Juros Compostos")**:
   - Ao registrar um provento, o método `mostrar_magica_didatica()` calcula e exibe:
     - Valor do provento por cota.
     - *Yield on Cost* (YoC) real sobre o preço médio investido.
     - A barra do "Número Mágico" (quantas cotas são necessárias para que os dividendos comprem uma nova cota automaticamente).
4. **Gráfico do Efeito Bola de Neve**:
   - Gráfico de barras integrado via `matplotlib` (`FigureCanvasQTAgg`), agrupado por mês (`YYYY-MM`), ilustrando o crescimento da renda passiva.
5. **Tabela de Histórico e Exclusão**:
   - Tabela de 6 colunas: `Ativo`, `Data`, `Tipo`, `Cotas Base`, `Valor Recebido`, `Excluir`.
   - Cada linha possui um botão de lixeira em tom coral (`#f38ba8`) estilizado com `qtawesome`.
   - O método `excluir_rendimento(id)` solicita confirmação de segurança e remove o registro do banco de dados, atualizando a tabela e o gráfico instantaneamente.

## Interligação
- Recebe injeção de dependência do `DBManager` e opcionalmente `MarketAPI` e `fn_atualizar_resumo` pelo `main.py`.
- Lê dados de `carteira_atual` para preencher os ativos elegíveis e sugerir quantidades no radar.
- Lê e grava dados na tabela `rendimentos` do SQLite.
- Atualiza o Dashboard Geral (`PaginaResumo`) automaticamente após o registro de proventos.
