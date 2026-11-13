# Documentação: update_checker.py

## Propósito
O `update_checker.py` implementa o mecanismo de notificação e verificação de atualizações (Auto-Update Checker) do Deven Wealth, integrando-se nativamente à API de Releases do GitHub com design offline-first, seguro e não intrusivo (UI/UX Opção A).

---

## Componentes

### 1. `WorkerVerificadorUpdates(QThread)`
Worker assíncrono que opera em thread dedicada em segundo plano para não travar a interface gráfica do usuário.
- **Constantes de Configuração**:
  - `VERSAO_ATUAL`: Versão SemVer atual do aplicativo (ex: `"0.2.0"`).
  - `REPO_GITHUB`: Repositório oficial do projeto (`LunyErlon/deven_wealth`).
  - `URL_RELEASES_API`: Endpoint REST oficial (`https://api.github.com/repos/LunyErlon/deven_wealth/releases/latest`).
- **Comportamento e Resiliência (Offline-First)**:
  - Timeout estrito de 3.0 segundos para requisições HTTP.
  - Compara a tag remota (`tag_name`) com a versão local utilizando `packaging.version.parse` para análise semântica robusta.
  - Se a versão remota for superior à local, emite o sinal `nova_versao_detectada(dict)` contendo a versão, título, notas de versão (Changelog) e URL de download.
  - Caso o aplicativo esteja offline, não haja internet ou o GitHub retorne status diferente de 200 (ex: 404 para repositórios sem releases ainda), o worker emite `verificacao_finalizada(False, mensagem)` e finaliza silenciosamente sem emitir erros ou travar o sistema.

---

### 2. `DialogAtualizacao(QDialog)`
Modal interativo moderno estilizado no tema Catppuccin Mocha (`#1e1e2e`, `#313244`, `#cdd6f4`) que exibe os detalhes da atualização:
- **Cabeçalho Comparativo**: Destaque visual contrastando a versão atual instalada (`v0.2.0`) com a nova versão disponível (`vX.Y.Z`).
- **Visualizador de Changelog (`QTextBrowser`)**: Renderiza a descrição formatada da release e o que mudou na nova versão.
- **Garantia de Segurança Local**: Mensagem explicativa reforçando que a atualização não apaga os dados locais, o cofre nem o banco de dados criptografado.
- **Botões de Ação**:
  - `"🌐 Baixar Atualização no GitHub"`: Abre a URL da release oficial diretamente no navegador padrão via `QDesktopServices.openUrl()`.
  - `"Lembrar Mais Tarde"`: Fecha o diálogo sem forçar o usuário a interromper suas atividades financeiras.

---

## Integração no Deven Wealth

### No Menu Lateral (`main.py`)
- Agendado suavemente via `QTimer.singleShot(2500, self.iniciar_verificacao_updates)` na abertura do app.
- Se uma nova versão for detectada, a pílula sutil `self.btn_update` (`"🚀 Atualização vX.Y.Z Disponível!"`) surge acima do rodapé da barra lateral com estilo gradiente suave (`#fab387` a `#f9e2af`).
- O clique na pílula abre o `DialogAtualizacao`.

### Nas Configurações (`pagina_config.py`)
- O botão `"🚀 Verificar Atualizações do Deven Wealth"` na seção de Backup e Sistema permite ao usuário forçar uma verificação manual a qualquer momento, recebendo feedback visual imediato.
