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

---

## 🚀 Como Lançar uma Nova Versão no Futuro (Passo a Passo)

Siga este roteiro simples sempre que desenvolver novidades ou correções e desejar que o aplicativo notifique os usuários automaticamente:

### 1. Atualizar a Versão no Código
No arquivo [gerenciador/update_checker.py](file:///g:/deven_wealth/gerenciador/update_checker.py#L11), altere a constante para a nova numeração SemVer:
```python
VERSAO_ATUAL = "0.3.0"  # Exemplo de nova versão
```

### 2. Comitar e Enviar para o GitHub
Envie as alterações para a branch principal (`main`):
```bash
git add .
git commit -m "chore: bump version to v0.3.0"
git push origin main
```

### 3. Publicar a Release no Repositório do GitHub
1. Acesse o repositório oficial no navegador: [github.com/LunyErlon/deven_wealth](https://github.com/LunyErlon/deven_wealth)
2. Na lateral direita da página inicial, clique em **Releases** (ou acesse diretamente `/releases`).
3. Clique no botão **"Draft a new release"**.
4. Configure os campos da release:
   - **Choose a tag**: Digite a tag correspondente com `v` (ex: `v0.3.0`) e clique em *Create new tag on publish*.
   - **Target**: Mantenha selecionado `main`.
   - **Release title**: Dê um título claro e atrativo (ex: `Deven Wealth v0.3.0 - Gráficos 50/30/20 & Relatório IRPF`).
   - **Describe this release**: Digite as novidades e melhorias em Markdown (itens com marcadores `- `, novidades, correções). Este texto será exibido dentro do pop-up do programa!
   - *(Opcional)*: Se tiver gerado um executável empacotado (`.exe` ou `.zip`), arraste o arquivo para a área de anexos (*Attach binaries*).
5. Clique no botão verde **"Publish release"**.

---

## 🎯 Resultado no Aplicativo dos Usuários
- Ao abrir o **Deven Wealth**, após 2,5 segundos o motor assíncrono consultará a API de releases.
- O sistema identificará que a versão remota (`0.3.0`) é maior que a versão local (`0.2.0`).
- A pílula com gradiente dourado/pêssego **`🚀 Atualização v0.3.0 Disponível!`** aparecerá suavemente no menu lateral.
- Ao clicar, o usuário verá o Changelog digitado no GitHub e poderá clicar em **"🌐 Baixar Atualização no GitHub"** para baixar o instalador ou novidades diretamente!
