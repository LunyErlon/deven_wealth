# Documentação: dialog_irpf.py

## Propósito
O `dialog_irpf.py` implementa a classe `DialogRelatorioIRPF(QDialog)`, um módulo de conformidade fiscal e geração de relatórios auxiliares para o preenchimento da Declaração de Ajuste Anual do Imposto de Renda Pessoa Física (DIRPF) junto à Receita Federal do Brasil.

---

## Funcionalidades e Regras Fiscais da Receita Federal

### 1. Seletor de Ano-Calendário (Ano-Base)
- Permite selecionar o ano de referência dos dados (ex: Ano-Base 2025 para a Declaração de 2026).
- Filtra proventos e custos com precisão anual.

---

### 2. Aba 1: 🏛️ Bens e Direitos (Custo Histórico em 31/12)
- **Regra da Receita Federal**:
  - Na ficha *Bens e Direitos*, o investidor é obrigado a declarar o **Custo Total de Aquisição** (Preço Médio ponderado $\times$ Quantidade de cotas) e **nunca** a cotação de mercado em 31/12.
- **Enquadramento Automático por Grupo e Código**:
  - **Ações**: `Grupo 03 - Código 01 (Ações inclusive as listadas em bolsa)`
  - **FIIs**: `Grupo 07 - Código 03 (Fundos de Investimento Imobiliário)`
  - **Criptoativos**: 
    - `Grupo 08 - Código 01 (Bitcoin - BTC)`
    - `Grupo 08 - Código 02 (Outras criptomoedas / Altcoins)`
    - `Grupo 08 - Código 03 (Stablecoins)`
    - `Grupo 08 - Código 99 (Outros criptoativos)`
  - **Renda Fixa**: `Grupo 04 - Código 02 (Títulos Públicos e Privados)`
- **Discriminação Padronizada Pronta para o Programa IRPF**:
  - Gera automaticamente o texto descritivo oficial exigido pelo fisco (ex: *"100 ações ordinárias/preferenciais de ITSA4 (Financeiro), custodiadas em corretora de valores, ao custo total de aquisição de R$ 980,00 (Preço Médio de R$ 9,80)."*).
- **Botão `📋 Copiar`**:
  - Copia o texto da discriminação para a área de transferência do Windows com um único clique.

---

### 3. Aba 2: 💰 Rendimentos Isentos e Não Tributáveis
- Agrupa proventos com isenção de imposto de renda para pessoa física:
  - **Código 09**: Lucros e dividendos recebidos de empresas brasileiras (Ações).
  - **Código 26 (Outros)**: Rendimentos distribuídos por Fundos de Investimento Imobiliário (FIIs).
- Totaliza os valores líquidos recebidos por ativo ao longo de todo o ano-calendário.

---

### 4. Aba 3: 🔒 Rendimentos Sujeitos à Tributação Exclusiva / Definitiva
- **Código 10 (Juros sobre Capital Próprio - JCP)**:
  - Agrupa os proventos do tipo JCP, cujo imposto de renda (15%) é retido na fonte pela instituição pagadora.
  - Informa o valor líquido total a ser lançado na ficha correspondente do programa da Receita Federal.

---

### 5. Exportação do Caderno IRPF em Excel (`.xlsx`)
- Botão **`📑 Exportar Caderno IRPF Completo (.xlsx)`**:
  - Utiliza `pd.ExcelWriter` para gerar uma planilha com 3 abas formatadas:
    1. `Bens e Direitos (Custo)`
    2. `Rendimentos Isentos`
    3. `Tributação Exclusiva (JCP)`
  - Ideal para arquivamento ou envio direto ao contador.

---

## Interligação
- **Chamado por**:
  - `pagina_config.py` (`abrir_relatorio_irpf`)
  - `pagina_carteira.py` (`abrir_irpf`)
  - `pagina_rendimentos.py` (`abrir_irpf`)
- **Tabelas Consultadas**: `carteira_atual`, `ativos_catalogo` e `rendimentos`.

