# Manual de Segurança e Criptografia do Deven Wealth

Este documento detalha o protocolo de segurança local implementado no Deven Wealth. O objetivo principal do aplicativo é garantir o máximo de privacidade e proteção dos dados do usuário, operando em um modelo _"Offline-First"_ (onde os dados nunca saem da máquina do usuário).

## 1. O Escudo de Dados (Application-Level Encryption)

Como o SQLite tradicional expõe os dados em texto claro e o SQLCipher exige compilação C++ complexa no Windows, o Deven Wealth utiliza um sistema robusto de criptografia em nível de arquivo com a biblioteca moderna `cryptography`.

### A Lógica do Cofre:
1. **Banco Criptografado (`deven_wealth.db.enc`):** O seu banco de dados financeiro só existe no seu computador nesse formato `.enc`. Ele é completamente ilegível para humanos ou para qualquer programa sem a chave exata.
2. **Derivação de Chave (PBKDF2HMAC):** Quando você digita sua Senha-Mestra, o aplicativo não a utiliza crua. Ele a passa por um triturador de algoritmos (SHA256) realizando **480.000 iterações** somado a um "Salt" randômico. Isso cria a Chave Criptográfica. Esse processo impede ataques de "Força Bruta" por cibercriminosos.
3. **Cifragem (Fernet):** O Fernet é o algoritmo simétrico encarregado de pegar a Chave e embaralhar todos os bytes do banco de dados de maneira irreconhecível.

## 2. Ciclo de Vida e Inicialização do Aplicativo

Para evitar vazamentos em memória e proteger os dados contra extração física do disco rígido, o ciclo de vida do software foi adaptado:

*   **Fase 1 - O Launcher (A Porta de Entrada):** O aplicativo sempre inicia em um escudo (O `Launcher`). Ele verifica se o cofre (`.enc`) existe.
*   **Fase 2 - Autenticação Local:** 
    *   **Registro (Primeiro Uso):** Se o banco não existir, a tela exige um nome, a Senha-Mestra forte e o Token da Brapi (validado via API na hora). Finalizado o cadastro, o banco invisível é criado, trancado e criptografado.
    *   **Login (Acesso Diário):** Se já houver um cofre, a tela de login exige a Senha-Mestra.
*   **Fase 3 - Desbloqueio e Uso:** Ao acertar a senha, o módulo `security_manager` usa a chave derivada para quebrar o cadeado, trazendo os dados para um banco `deven_wealth.db` temporário. O Deven Wealth é iniciado.
*   **Fase 4 - Trancando a Porta (`closeEvent`):** Ao clicar no "X" para fechar a interface (janela), o PyQt intercepta o comando. Antes do Python "morrer", o `SecurityManager` criptografa todo o banco modificado para `deven_wealth.db.enc` e imediatamente apaga (deleta) permanentemente o `deven_wealth.db` legível do disco. O cofre está trancado novamente.

## 3. Gestão e Validação do Token Brapi

A proteção da comunicação de preços em tempo real com a B3 (via Brapi) também foi aprimorada:

- **Anti-Spam de Token:** O usuário só consegue concluir o registro se inserir um Token ativo. O programa faz um disparo de _mocking_ (`requests.get`) para as cotações da PETR4. Se o servidor HTTP não responder o código 200 (Sucesso), o sistema bloqueia a criação do cofre.
- **Armazenamento Seguro:** Após o registro, o Token fica armazenado internamente na nova tabela invisível `configuracoes` dentro do SQLite. E como o SQLite é criptografado a cada desligamento, o seu token também está blindado contra interceptações físicas no seu PC.

## 4. O Paradoxo do E-mail Resolvido
Decidimos remover o e-mail do processo de criação de conta. Como um aplicativo desktop necessitaria ter a _nossa_ credencial de remetente SMTP diretamente no código-fonte para conseguir disparar um e-mail ao usuário (uma falha crítica de segurança caso o app fosse descompilado), a arquitetura adotou um formato de "Cold Wallet" (Carteira Fria). Toda a segurança baseia-se única e exclusivamente na sua **Senha-Mestra Local**. Você é o único detentor do acesso.
