# Documentação: main.py

## Propósito
O `main.py` é o ponto de entrada (Entry Point) e o contêiner principal do aplicativo Deven Wealth. Ele não contém lógicas complexas de dados ou matemática, focando exclusivamente na orquestração da interface e na inicialização dos serviços.

## Responsabilidades
1. **Inicialização do App**: Instancia o `QApplication` do PyQt6.
2. **Setup do Motor**: Cria as instâncias de `DBManager` e `MarketAPI`.
3. **Criação do Banco e Migrações**: Possui o método `inicializar_banco_dados()`. Ele cria as tabelas padrão e inclui mecanismos de **Migração de Banco**: usa `ALTER TABLE` para injetar a coluna `grupo_regra` em `categorias` e `recorrente` em `transacoes` caso não existam. Além disso, carrega a **Lista Padrão do 50/30/20** de categorias na instalação zerada.
4. **Motor Detetive de Contas Recorrentes (`verificar_contas_recorrentes`)**: Sempre que o aplicativo inicializa, o motor varre o mês anterior em busca de contas recorrentes (`recorrente = 1`) que ainda não foram lançadas no mês corrente. Caso encontre pendências, abre o pop-up de boas-vindas com lista editável e suporte ao **Loop Autolimpante**.
5. **Radar de Dividendos em Segundo Plano (`WorkerRadarDividendos` via `QThread`)**: Ao iniciar, o aplicativo renderiza o painel localmente e dispara uma thread paralela assíncrona. Ela varre a B3 via `MarketAPI` procurando dividendos recentes dos ativos em `carteira_atual`. Se houver proventos não registrados, dispara o pop-up de validação sem travar a interface. Se não houver, encerra silenciosamente.
6. **Layout Base (Chassi)**: Constrói a janela (`QMainWindow`), o menu lateral (Barra de Navegação) contendo um rodapé embutido na parte inferior, e a área central (`QStackedWidget`).
7. **Roteamento de Telas**: Instancia as páginas (`PaginaResumo`, `PaginaCarteira`, etc.), colocando-as dentro do baralho (`QStackedWidget`), e conecta os botões do menu lateral para alternar o índice deste baralho.
8. **Callbacks e Sincronização**: Ao instanciar as páginas, ele passa os conectores para que uma página atualize a outra. Exemplo: passa o `fn_atualizar_resumo=self.pagina_resumo.carregar_dados` para a `PaginaCarteira` e `PaginaRendimentos`, garantindo que o gráfico de dividendos mude assim que um provento for confirmado.
9. **Estilização Global e Identidade Visual**: O método `aplicar_estilos()` insere o QSS (semelhante ao CSS) que define a paleta de cores escura, tipografia global (fonte monoespaçada, estilo terminal) e bordas da interface. A paleta utiliza tons dourados (`#D4AF37`) para destacar a identidade visual, além do fundo quase preto (`#050505`) no menu e rodapé.
10. **Ícones Dinâmicos**: Os ícones do menu lateral utilizam a biblioteca `qtawesome` (estilo outline/linha). Um sistema de estado dinâmico (no método `atualizar_menu()`) colore o ícone e sublinha o botão ativo, deixando os inativos em um tom esmaecido.
## Interligação
- **Depende de**: Todos os outros arquivos (`market_api.py`, `db_manager.py`, e todas as `pagina_*.py`). Ele os importa e os junta.
- **Fornece a**: Nenhum. Ele é o topo da hierarquia, nada o importa.
