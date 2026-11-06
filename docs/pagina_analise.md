# Documentação: pagina_analise.py

## Propósito
É o componente de "Busca de Cotações" em tempo real e serve como a porta de entrada (Catálogo) para se colocar novos ativos no banco de dados local. 

## Como Funciona
A classe `PaginaAnalise(QWidget)` controla a tela de pesquisa e o Radar de Oportunidades.
- **`setup_ui()`**: Cria uma barra de busca (`QLineEdit`) e uma label escondida para o resultado. Abaixo, renderiza a tabela interativa do **Radar de Oportunidades**.
- **`executar_busca()`**: Pega o texto da barra de pesquisa e aciona o motor de busca na nuvem, usando `self.api.buscar_dados_ativo()`. Destrava o fluxo para que o usuário não sinta travamento na UI (`QApplication.processEvents()`). Se os dados retornarem com sucesso da API, formata o HTML e exibe o resultado na tela, mostrando o botão "Salvar".
- **`salvar_ativo_banco()`**: Ocorre quando o usuário decide salvar a pesquisa. Ele joga as informações na tabela `ativos_catalogo` e a cotação inicial/indicadores na tabela `cache_mercado`. Atualiza automaticamente o radar.
- **`carregar_radar()`**: Lista todos os ativos que já estão no catálogo (salvos no banco). Ele compara o Preço Atual com a coluna `preco_teto`. Se o preço atual for igual ou menor que o teto estabelecido, ele destaca a linha em verde brilhante com a flag "🎯 OPORTUNIDADE".
- **`definir_preco_teto()`**: Um Pop-up ativado diretamente pelas linhas da tabela do Radar, permitindo que o usuário informe o valor máximo que aceita pagar por aquele ativo.

## Interligação
- Diferente de algumas páginas, esta precisa de DUAS instâncias via Injeção de Dependência em seu construtor: O `db` (para salvar os dados) e a `api` (para rodar a busca na web).
- Recebe no construtor um gatilho *Callback* chamado `fn_atualizar_carteira`. Se o usuário salva o ativo no banco, esse callback é acionado para atualizar a tabela da página "Minha Carteira" lá no fundo, avisando que existe um novo ativo pronto para receber registro de compras.
