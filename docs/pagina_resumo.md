# Documentação: pagina_resumo.py

## Propósito
É o componente responsável por renderizar a "Visão Geral", o painel de KPIs (Patrimônio Total e Lucro/Prejuízo) e o Gráfico de Pizza que distribui o patrimônio por classe de ativo.

## Como Funciona
A classe `PaginaResumo` é um `QWidget` que funciona como o painel central do usuário.
- **`setup_ui()`**: Monta a interface. Utiliza os layouts do PyQt6 (`QVBoxLayout`, `QHBoxLayout`) para estruturar os rótulos de KPI (Patrimônio Líquido, Taxa de Poupança e Renda Passiva). Integra nativamente a biblioteca `matplotlib` através do `FigureCanvasQTAgg` para renderizar os gráficos. Também monta os campos da **Máquina do Tempo**.
- **`carregar_dados()`**: Faz as consultas SQL para extrair saldos e o patrimônio investido. Calcula sua média histórica de aportes (usando as transações do tipo "Construção de Riqueza") para alimentar o simulador. Atualiza os gráficos de Despesas (Rosca) e Rendimentos (Barras).
- **`calcular_maquina_tempo()`**: Um simulador preditivo de independência financeira. Ele lê a média de aportes calculada e o patrimônio atual, cruzando com a Taxa Anual e a Meta estipuladas pelo usuário. O motor calcula os juros compostos em um loop mês a mês até que a meta seja batida, retornando exatamente o ano e o mês em que o usuário atingirá o marco.

## Interligação
- Recebe a instância do banco de dados no momento em que é instanciada no `main.py`.
- O seu método `carregar_dados()` é exportado e enviado como *Callback* para as outras páginas (`carteira`, `financas`, `rendimentos`). Assim, se o usuário alterar os dados financeiros em qualquer lugar do app, a tela de Resumo é atualizada instantaneamente.
