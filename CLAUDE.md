# CLAUDE.md — Sistema de fidelidade por cartão na Wallet (base: Clube Backbone)

Este arquivo é lido automaticamente pelo Claude ao abrir o projeto. Ele resume tudo
que foi construído e aprendido no Clube Backbone (cervejaria artesanal), que é a base
deste projeto. Este repositório é a versão adaptada para **um restaurante**, com
banco de dados, GitHub, contas Google e cadastro próprios.

Leia também `ADAPTACAO-RESTAURANTE.md` (o que mudar da base) e `MONTAGEM-DO-ZERO.md`
(contas, chaves e deploy).

**Este repositório é do Cotito** (unidade grab and go do grupo Côt, Shopping Tijuca).
As regras aprovadas pelos sócios estão em **`DECISOES-COTITO.md`** e valem mais que
`ADAPTACAO-RESTAURANTE.md` quando os dois discordarem. Leia esse arquivo primeiro.

---

## 1. Como trabalhar com o dono

- O dono **não é desenvolvedor**. Tem forte sensibilidade de design e intuição comercial.
  Explique em linguagem simples, mostre prós e contras quando houver opções.
- Português do Brasil, tom informal.
- **Mockup antes de código.** Toda mudança de tela: mostrar o desenho, esperar aprovação
  explícita, e só então programar. Aprovado o desenho, vá direto à implementação, sem
  mais perguntas.
- **Um assunto por vez.**
- **Sempre parta da versão atual do arquivo no repositório.** O dono edita arquivos
  direto no editor web do GitHub, então qualquer cópia local pode estar velha.
  Nunca altere a partir de memória ou de cópia antiga.
- Trabalhe em **branch + pull request**; o dono dá o merge na `main`. O merge dispara o
  deploy do servidor (Cloud Build) e das telas (GitHub Pages).
- Valide antes de entregar: JavaScript com `node --check` (extraindo o `<script>`),
  Python com `python3 -m py_compile`.
- Prefira editar trechos (Edit) a substituições em massa com `sed`: já quebrou arquivo.
- O dono pede dados e regras de negócio **uma vez**: registre as decisões aqui ou em docs
  do repositório para não perguntar de novo.

## 2. O que o sistema faz

Programa de fidelidade 100% próprio (sem depender de plataformas de terceiros):

- O cliente se cadastra por um QR/link e recebe um **cartão na Apple Wallet ou Google
  Wallet**. O mesmo QR do cartão serve ao atendente (scanner) e a um amigo (indicação).
- O **atendente/garçom** escaneia o QR do cliente a cada consumo; o cartão atualiza sozinho.
- A cada N consumos (padrão 10) o cliente ganha um prêmio, resgatado escaneando o cartão.
- Painéis: **admin** (dono), **gestor** (por unidade), **garçom/scanner** (celular),
  **colab** (parceiro externo que indica clientes).
- Notificações no cartão (push silencioso via Apple, atualização de objeto no Google).

## 3. Stack e arquitetura

- **Servidor:** Python/Flask no **Google Cloud Run** (`server/main.py`, `storage.py`,
  `pkpass.py`, `gwallet.py`, `apns.py`, `certs.py`). Gunicorn, 1 worker, 8 threads.
- **Banco:** Google Cloud Storage (um bucket). **Um arquivo JSON por registro**; eventos
  em log NDJSON. Sem banco SQL.
- **Telas:** HTML/CSS/JS puro, publicadas no **GitHub Pages**. Falam com o servidor por fetch.
- **Deploy do servidor:** Cloud Build disparado por commit na `main` (`cloudbuild.yaml`
  + `dockerfile` na raiz, que copia `server/`).
- **Cloud Run com instância mínima = 1.** Na base isso foi adotado para evitar perda de
  registros de push da Apple em partida a frio (e a primeira resposta lenta).
- QR codes: imagem de `api.qrserver.com` via `<img>` (evita problema de CORS).
- Tipografia da marca em fonte local (woff/woff2).

### Mapa de arquivos

| Arquivo | Função |
|---|---|
| `cadastro.html` | Página de cadastro do cliente (vem do QR da mesa ou do QR de um amigo) |
| `perfil.html` | "Meus dados": pontos, benefícios, botão da Wallet, caixa de mensagem ao clube |
| `scanner.html` | Scanner do atendente (câmera nativa BarcodeDetector), aba Atividade |
| `gestor.html` | Painel da unidade: números, atividade, atendentes, aba de reembolso |
| `admin.html` | Painel do dono: sócios, unidades, atendentes, gestores, admins, colabs, push, config, mensagens |
| `colab.html` | Painel do colab (parceiro que indica) |
| `login.html` | Login único: tenta atendente, gestor, admin, colab em sequência |
| `server/main.py` | Todas as rotas |
| `server/storage.py` | Leitura/escrita no bucket |
| `server/pkpass.py` | Gera o cartão Apple (.pkpass) a cada requisição |
| `server/gwallet.py` | Cartão Google Wallet (classe + objeto por cliente) |
| `server/apns.py` | Push para a Apple Wallet |
| `server/certs.py` | Carrega certificados Apple de variáveis de ambiente (base64) |
| `strips/` e `server/strips/` | Artes do cartão (ver armadilha na seção 8) |

### Dados no bucket

`consumidores/<tel>.json` (clientes), `registros/<tel>.json` (dispositivos Apple do push),
`bares/<id>.json` (unidades), `garcons/`, `gestores/`, `admins/`, `colabs/`,
`descontos/` (reembolsos), `config/config.json`, `bloqueados.json`,
`eventos/log.jsonl` (todos os eventos), `mensagens/log.jsonl` (mensagens do cliente).
`storage.listar_X()` usa `_listar_prefixo()` com pool de threads para baixar em paralelo.

### Papéis e logins

Garçom `/login`, gestor `/login-gestor`, admin `/login-admin`, colab `/login-colab`.
Cada registro tem flag `ativo`. **Segurança (feita no Cotito, `server/auth.py`):** senhas
guardadas com hash (as antigas em texto puro migram sozinhas no primeiro login); cada login
devolve um `token` que as telas guardam junto do usuário (`bb_*` no localStorage) e que o
`auth.js` envia em todo pedido. Um `before_request` aplica as regras: rotas públicas
(cadastro, cartão, consumidor, Wallet, QR) liberadas; `/admin/*` só admin (exceto listar
unidades e o gestor criar atendente/colab da própria unidade); `/bar/<id>/*` gestor da
unidade (atendente só `atividade`); scans só em nome de quem está logado. **Rota nova que
não estiver na lista de públicas exige admin**: ao criar rota pública, inclua em `auth.py`.
Telas internas novas precisam do `<script src="auth.js" data-chaves="...">`.

## 4. Regras de negócio

- **Contadores do cliente:** `punches` (ciclo, volta a zero no resgate) e `chopps_totais`
  (vitalício, nunca zera). Não confundir. (No restaurante os nomes de campo podem
  continuar iguais; só o rótulo muda para "pratos".)
- A meta do ciclo é `punches_para_recompensa` (config, padrão 10) e fica **congelada no
  cliente** (`meta`) na hora do cadastro.
- Cartela cheia sem resgatar: novos pontos **não contam** até o resgate.
- Prêmio resgatado **não conta ponto**.
- Marcos de longo prazo (na base: 50 = ação manual, 100 = muda de árvore automática).
  Ver `ADAPTACAO-RESTAURANTE.md` para decidir o que fazer com isso.
- **Padrinho:** quem indica via QR do cartão de um amigo é registrado no cadastro.
- **Boas-vindas:** o primeiro consumo grátis só vale depois de **confirmado na unidade**
  (por isso há "Ficha" = cadastro na web e "Sócio/Ativo" = confirmado no local).
- **Antifraude:** telefone de atendente não pode ser cliente (e vice-versa). Lista fria de
  telefones bloqueados por unidade, com mensagens de recusa vagas de propósito.
  Um telefone pode ser cliente e colab/gestor/admin; só cliente↔atendente é barrado.
- **Colab:** parceiro externo com QR próprio (`/c/<id>`); não consome, não tem cartão.
  Na base há o "modo Prato" (`/scan-prato`, `/resgatar-prato`): colab ganha um prato a
  cada 10 pratos dos indicados dele.
- **Reembolso por unidade** (só faz sentido para rede/franquia/parceiros; ver adaptação).

## 5. Cartões da Wallet

**Apple (`pkpass.py`):** tipo storeCard montado a cada requisição. A imagem de faixa
(strip) vem de `server/strips/<temporada>/`, redimensionada para 375×123 em 1x/2x/3x.
O banner de notificação só aparece quando o campo "Último aviso" (backField com
`changeMessage "%@"`) **muda de valor**. Push silencioso: payload `{}`, prioridade 5.
Reenviar texto idêntico não gera novo banner.

**Google (`gwallet.py`):** classe + um objeto por cliente; a imagem principal (hero)
vem de URL pública do GitHub Pages (`strips/<temporada>/` na raiz do repo). Cada
notificação faz PUT no objeto; não há banner.

**Importante:** a arte do iPhone e a do Android ficam em **duas pastas diferentes**
(`server/strips/...` e `strips/...`). Trocar só uma deixa os sistemas diferentes.

**Armadilha de corte (Apple):** a faixa é cortada nas laterais conforme o modelo do
iPhone. Concentre texto e elementos importantes no **centro** da arte.

**iOS 27 (futuro):** novo estilo Poster Generic (arte 358×448 pt) e Featured Actions
(até 2 botões). Ainda não implementado nesta base.

## 6. Variáveis de ambiente (Cloud Run)

`APPLE_TEAM_ID`, `PASS_TYPE_ID`, `ORG_NAME`, `WEB_SERVICE_URL`, `APNS_HOST`,
`APPLE_CERT_B64`, `APPLE_KEY_B64`, `APPLE_WWDR_B64`, `GOOGLE_WALLET_ISSUER_ID`,
`GOOGLE_WALLET_KEY_B64`, `CARDAPIO_URL`, `PERFIL_URL`, `LOJA_URL`, `HERO_VERSAO`,
`SECRET_KEY` (assina os logins; sem ela todos saem a cada deploy).
**Nunca** coloque chaves no repositório nem em conversa. Se uma chave vazar, revogue e
crie outra.

## 7. Fluxos que sempre dão trabalho

- **Disparo em massa (push):** `/admin/push-lote` processa um a um (≈1–2 s por cliente).
  Com centenas de clientes passa do limite de tempo padrão do Cloud Run (300 s).
  Aumente "Tempo limite de solicitação" (Escalonamento › Solicitações) para 1200 s.
- **Troca de arte do cartão (campanhas):** troque nas **duas** pastas, envie o push com
  texto novo, e restaure as artes originais depois (esperar ~30 min). O Google pode manter
  a imagem antiga em cache por um tempo.
- **Falha típica do Cloud Run:** log com `Failed to find attribute 'app' in 'main'` =
  `main.py` quebrado/incompleto no repositório. Confira a sintaxe e o arquivo inteiro.
- **Build verde ≠ deploy novo no ar.** O verde da action do GitHub é o Pages (telas); o
  servidor só muda quando o **Cloud Build** termina e a revisão nova do Cloud Run recebe 100%
  do tráfego. Peça sempre o horário.
- **`storage.listar_eventos()`** deve usar `storage.Client()`, não `_client()` (já causou 500).
- Cartão Apple: backField sem `value` gera aviso no log (corrigir adicionando `value`).

## 8. Lições de produto

- Dono quer **controle do funil e dos dados**: tudo próprio, sem Meta/WhatsApp.
- Cadastro em dois passos (web → confirmação na unidade) reduz fraude de brinde.
- Telefone é a chave do cliente; normalize sempre para só dígitos com DDI 55.
- Textos de tela curtos: no celular, título e blocos que quebram em duas linhas ficam
  feios; o dono é exigente com fonte, cor e alinhamento (veja o estilo das telas
  existentes antes de criar outra).
- **Fonte da marca:** o Clube Backbone usa a fonte comercial GT Sectra Black, licenciada para a cervejaria. Ela **não vem** neste repositório; o restaurante deve usar fonte própria ou licenciar a sua.
- Visual: fundo preto, âmbar como destaque, branco, cinza claro para campos.
