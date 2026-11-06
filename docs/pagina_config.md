# Documentação: pagina_config.py

## Propósito
É o menu global que permite modificar as "Regras" sistêmicas e fornecer uma ferramenta de Reset em caso de banco de dados corrompido ou necessidade de exclusão total por parte do usuário.

## Como Funciona
A classe `PaginaConfig(QWidget)` oferece diversas funções de gerenciamento:
- **`salvar_perfil()`**: Atualiza os dados pessoais do usuário e gerencia a alteração da senha mestra com segurança.
- **`atualizar_token_api()`**: Onde o usuário digita um novo Token da Brapi para fazer a varredura da API. Ele muda esse token ativamente e dinamicamente em tempo de execução mudando a variável `self.api.token_brapi`, de forma que as próximas requisições na Análise de Mercado já sejam autorizadas com a nova chave.
- **`salvar_metas()`**: Atualiza as porcentagens-alvo da regra 50/30/20 (Necessidades, Desejos e Construção de Riqueza) na tabela `configuracoes`. A soma destas metas deve obrigatoriamente totalizar 100%. A aba "Contas Pessoais" consulta esses valores dinamicamente.
- **`exportar_dados_excel()`**: Exporta um relatório contábil completo (planilha Excel `.xlsx`) organizado em três abas (sheets) usando o `pd.ExcelWriter`:
  - **Aba 1 ("Minha Carteira")**: Dados da carteira atual (Ativo, Classe, Setor, Quantidade, Preços e Saldos).
  - **Aba 2 ("Contas Pessoais")**: Histórico de transações financeiras com suas respectivas categorias e grupos.
  - **Aba 3 ("Renda Passiva")**: Histórico de recebimento de dividendos e proventos.
- **`exportar_db_seguro()`** e **`importar_db_seguro()`**: Permitem a criação e restauração de backups completos do banco de dados (arquivos `.dwb`), protegidos por criptografia simétrica (Fernet) derivada da senha mestra do usuário.
- **`zerar_banco_dados()`**: Roda o comando SQL `DELETE FROM [tabela]` em TODAS as 5 tabelas ativas do sistema, mantendo as colunas/estruturas ativas, mas esvaziando todas as linhas. Apenas no final, ele chama o gatilho `fn_reset_db`.
- **UI/UX Aprimorada**: A tela de configurações utiliza um `QScrollArea` para adaptar-se dinamicamente quando as seções expansíveis (Sanfonas) são abertas. Os campos de entrada (nome, token, metas) possuem restrições de largura para não esticarem e validação de tamanho máximo, além de um validador de senha reativo (`validar_regras_senha_ui`) que dá feedback visual em tempo real sobre os requisitos de segurança.

## Interligação
- Recebe a instância do banco (`self.db`) e da API (`self.api`) injetada via construtor.
- Recebe o *Callback* `fn_reset_db` do `main.py`. Assim que o script finaliza o apagar completo do banco, ele aciona essa função que roda diretamente no `main.py` reconstruindo as Categorias-Padrão que o sistema precisa para funcionar ("Alimentação, Moradia, Salário..."), regerando os visuais e jogando o usuário forçosamente para a tela de "Visão Geral" agora vazia.
