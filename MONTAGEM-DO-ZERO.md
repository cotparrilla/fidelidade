# Montagem do zero — contas, chaves e deploy

O restaurante precisa da **própria infraestrutura**, separada da cervejaria: nada de
dados, bucket ou projeto compartilhado. Este guia lista o que criar e onde cada coisa entra.

Regra de ouro: **chave, senha e certificado nunca vão para o repositório nem para uma
conversa.** Vão só em variáveis de ambiente do Cloud Run (ou Secret Manager).

## Visão geral — o que é de quem

| Item | Conta | Observação |
|---|---|---|
| Apple Developer Program | **Conta nova, no nome do filho (ou da empresa do restaurante)** | Decisão: o projeto pode ser repassado a terceiros, então o cartão não deve ficar preso à conta de outra pessoa (ver 3) |
| Google Cloud (Cloud Run, bucket, Cloud Build) | **Nova, no nome do filho** | Cobrança e dados próprios |
| Google Wallet (Issuer) | **Nova, no nome do filho** | Emissor próprio, nome do restaurante no cartão |
| GitHub | **Novo repositório, no nome do filho** | Pages + gatilho do Cloud Build |

## 1. GitHub

1. Criar o repositório (ex.: `fidelidade`) na conta do filho, a partir de uma cópia limpa
   do código base (sem histórico de dados reais e sem nenhum certificado/chave).
2. Colocar `CLAUDE.md`, `ADAPTACAO-RESTAURANTE.md` e este arquivo na raiz.
3. Ativar o **GitHub Pages** (Settings › Pages › branch `main`, pasta raiz). O endereço
   fica `https://<usuario>.github.io/<repositório>/`.
4. Instalar o app do Claude no repositório (permite o Claude trabalhar em branch e abrir
   pull requests; o filho dá o merge).

## 2. Google Cloud (projeto novo)

1. Criar um **projeto** (ex.: `fidelidade-restaurante`), com cobrança ativada.
2. Ativar as APIs: Cloud Run, Cloud Build, Artifact Registry, Cloud Storage.
3. Criar o **bucket** do Cloud Storage (região `us-central1` ou a mais próxima). Esse
   nome vai em `server/storage.py` (`BUCKET_NAME`). Acesso uniforme, **não público**.
4. Dar à conta de serviço do Cloud Run (a padrão do Compute) permissão de **Storage
   Object Admin** nesse bucket.
5. **Cloud Run:** serviço de nome definido no `cloudbuild.yaml`, região `us-central1`,
   acesso público (as telas chamam a API sem login do Google), **instâncias mínimas = 1**,
   **tempo limite de solicitação = 1200 s** (por causa dos disparos em massa).
6. **Cloud Build:** criar o gatilho ligado ao repositório novo (branch `main`),
   usando o `cloudbuild.yaml` da raiz. Conferir se a conta do Cloud Build pode implantar
   no Cloud Run.
7. Anotar a URL do serviço (`https://....run.app`): vai em todas as telas (constante
   `SERVER`) e na variável `WEB_SERVICE_URL`.

## 3. Apple Wallet (conta de desenvolvedor nova)

Decisão tomada: o restaurante abre a **própria conta Apple Developer**, porque o projeto
poderá ser repassado a terceiros. A Pass Type ID e o certificado ficam presos à conta que
os criou; com conta própria, o ativo acompanha quem for dono do restaurante.

**Abrir a conta (comece por aqui, pode levar dias):**
1. Escolher o tipo: **pessoa física** (rápido, aparece o nome da pessoa como vendedor) ou
   **organização** (exige CNPJ e número D-U-N-S, aparece o nome da empresa, e é a opção
   certa se o projeto puder ser vendido ou repassado). Recomendada: organização.
2. Inscrever-se no Apple Developer Program (anuidade em dólar, paga no cartão).
3. Aguardar a aprovação da Apple. Só depois dela é possível criar Pass Type ID.

**Depois de aprovada:**
1. Em Certificates, Identifiers & Profiles › Identifiers: criar uma **Pass Type ID**
   (ex.: `pass.com.<restaurante>.fidelidade`).
2. Gerar o **certificado** dessa Pass Type ID (pedido via CSR gerado no seu computador),
   baixar o `.cer`, importar no Keychain e exportar o par certificado + chave.
3. Converter para PEM: `cert.pem` (certificado) e `key.pem` (chave privada).
   Baixar também o certificado intermediário **WWDR** da Apple em PEM (`wwdr.pem`).
4. Anotar o **Team ID** da conta nova.
5. Colocar em variáveis do Cloud Run (valores em base64):
   `APPLE_CERT_B64`, `APPLE_KEY_B64`, `APPLE_WWDR_B64`, além de
   `APPLE_TEAM_ID`, `PASS_TYPE_ID`, `ORG_NAME` (nome do restaurante) e `WEB_SERVICE_URL`.
6. O push do cartão usa esse mesmo certificado (`apns.py`), então não há outra chave.

**Chave das sessões (`SECRET_KEY`):** crie no Cloud Run a variável `SECRET_KEY` com um
texto aleatório longo. Gere no Cloud Shell do Google com
`python3 -c "import secrets;print(secrets.token_urlsafe(48))"` e cole direto no Cloud Run,
sem passar pela conversa.
Ela assina o login das telas internas. Sem ela, todo mundo precisa entrar de novo a cada
deploy. Trocar o valor desconecta todos os logins (útil se suspeitar de vazamento).

Cuidados:
- Certificado Apple vence (em geral 1 ano). Anotar a data e renovar antes.
- Se o projeto for repassado, a transferência correta é a da **conta** (a Apple permite
  transferir um app/conta de organização), nunca copiar certificado e chave por e-mail.

## 4. Google Wallet (emissor novo, no nome do filho)

1. Abrir o **Google Pay & Wallet Console** e cadastrar-se como emissor; anotar o
   **Issuer ID**.
2. No Google Cloud do restaurante, criar uma **conta de serviço** e baixar a chave JSON.
   No Console do Wallet, autorizar essa conta de serviço no emissor.
3. Colocar no Cloud Run: `GOOGLE_WALLET_ISSUER_ID` e `GOOGLE_WALLET_KEY_B64`
   (o JSON da chave em base64).
4. Em `gwallet.py`, ajustar `CLASS_SUFFIX`, logo, URL do hero e `origins` para o domínio
   do GitHub Pages do restaurante.
5. Criar a **classe** do cartão (rota `/admin/gwallet/classe`, POST, uma única vez) e usar
   `/admin/gwallet/reatualizar` quando mudar o texto da classe.
6. Enquanto o emissor estiver em modo de teste, só contas de teste adicionadas no Console
   conseguem salvar o cartão. Para o público, é preciso solicitar a publicação.

## 5. Primeiro teste ponta a ponta (com a base sem alterações)

1. Cadastrar no admin: **uma unidade** (a casa), **um garçom**, **um gestor**.
2. Gerar o QR da unidade pelo admin e abrir o link de cadastro no celular.
3. Cadastrar um telefone de teste; baixar o cartão na Wallet (iPhone e Android).
4. No scanner, logar como garçom, escanear o cartão do cliente e conferir:
   boas-vindas, ponto, atualização do cartão e resgate no 10º.
5. Enviar um push de teste pelo admin.
6. Só depois de tudo funcionando: começar a adaptação (`ADAPTACAO-RESTAURANTE.md`).

## 6. Segurança básica

- Trocar a senha de qualquer admin criado para testes.
- Não reutilizar senhas entre unidades/pessoas (as senhas da base são guardadas em texto
  puro; endurecer isso é recomendado antes de abrir ao público).
- Limitar quem tem acesso ao projeto do Google Cloud e ao repositório.
- Guardar uma cópia segura (cofre de senhas) dos certificados Apple e da chave do Google.
- Se alguma chave aparecer numa conversa ou arquivo: revogar e criar outra na hora.

## 7. Custos esperados (ordem de grandeza)

- Apple Developer: anuidade própria do restaurante.
- Google Cloud: com instância mínima = 1, há um custo fixo pequeno mensal; o resto
  (bucket, builds) costuma ficar na faixa gratuita para uma casa só.
- Google Wallet e GitHub Pages: sem custo.
