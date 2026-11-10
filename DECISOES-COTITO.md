# Decisões do Cotito

Regras de negócio e de marca já aprovadas pelos sócios do Cotito (unidade grab and go
do grupo Côt, Shopping Tijuca, Rio de Janeiro). Este arquivo vale mais que
`ADAPTACAO-RESTAURANTE.md` quando os dois discordarem: aquele foi escrito antes destas
decisões. Não pergunte de novo o que está aqui.

## Operação

- **Uma unidade só.** Nada de escolha de bar, gestor por unidade, reembolso entre bares
  ou lista fria por bar. Pode existir 1 registro em `bares/` por baixo, escondido das telas.
- **Não há garçom nem atendimento de mesa.** Todo contato é no **balcão**, com um
  atendente. No código e nas telas, "garçom" vira "atendente".
- O cliente interage em dois momentos: ao comprar (lê o QR, se cadastra, salva o cartão,
  ganha o mate) e ao voltar (atendente escaneia o cartão a cada pedido com executivo).

## Cadastro

- Perguntas: **nome, telefone e aniversário** (dia e mês). Nada de time, CEP etc.
- Aviso de LGPD no cadastro (texto aprovado no desenho):
  "Aceito que o Cotito guarde meu nome, telefone e aniversário para o clube de pontos.
  Dá pra sair quando quiser."

## Boas-vindas (gancho)

- Ao se cadastrar, o cliente ganha **um mate da casa** (produzido pelo próprio Cotito).
- O mate só é liberado quando o atendente escaneia o cartão no balcão. Esse escaneamento
  é o que confirma o cadastro (ficha → ativo).

## Pontos

- **1 ponto por leitura** quando o pedido tem **pelo menos um executivo**. Dois ou mais
  executivos no mesmo pedido continuam valendo 1 ponto.
- **Bloqueio de 2 horas:** o mesmo cartão não ganha outro ponto antes de 2 h do último.
  O scanner mostra o horário do último ponto e a partir de quando vale o próximo, e o
  painel do dono registra a tentativa.
- **Meta: 10 pontos = 1 executivo grátis.** O prêmio não é um prato específico.
- Prêmio resgatado não conta ponto (regra da base, mantida).
- Remover os marcos de 50 e 100 (árvores) da base.

## Indicação

- Cada cliente mostra o QR do próprio cartão para um amigo; o amigo se cadastra por ele.
- **A indicação só conta quando o indicado retira o mate no balcão** (não no cadastro).
- Contador de indicações **vitalício**, nunca zera.
- **Brindes em degraus fixos e cumulativos, sempre nesta ordem:**
  boné com **15** indicações, camiseta com **45**. Não há escolha de brinde.
  Ex.: com 16, o cartão mostra o boné conquistado e "16/45" rumo à camiseta.
- Os degraus (quantidade e nome do brinde) ficam **editáveis no painel do dono**, para
  ajustar números ou incluir um terceiro brinde sem mexer no código.
- Entrega do brinde: o atendente escaneia o cartão e marca o brinde como entregue.
- O "modo Prato" de colab da base não se aplica; remover para não confundir.

## Cartão na Wallet

- Cartão preto, faixa (strip) com foto, sem campo de pontos no cabeçalho.
- Campos: **Membro** (nome) e **Para a próxima premiação** ("7/15 indicações").
- Artes aprovadas: 12 faixas de 1125 × 369 px em `strips/estilos/` (Google) e
  `server/strips/estilos/` (Apple), com os nomes que o código já espera.
  - `boasvindas`: foto do mate em fundo amarelo, "O mate da casa é por nossa conta."
  - `0-10` a `9-10`: um prato por estágio, contador "N/10 pontos" em branco com contorno
    preto (no `7-10` o contador fica à esquerda, para não cobrir o pote de molho).
  - `premio`: troféu amarelo com o boi em fundo preto, "Parabéns! O executivo é por
    nossa conta."
  - Ordem dos pratos: carne com arroz, empanada, espetinho de polvo, sanduíche, picanha na
    tábua, prato glaceado, linguiça, espeto com molho e farofa, espetinhos de coração,
    choripan. Fotos de reserva para campanhas: salmão, pão de alho, milho.
- As artes do pôster do iOS 27 (`server/strips/estilos/poster/`) eram da base e foram
  retiradas; o código só usa o pôster se as imagens existirem.

## Marca

- Brand book "Cotito" v1.0 (dez/2025). Paleta: branco `#E9E1CC`, preto `#1C180E`,
  amarelo `#FFD13B`, vermelho `#FF6638`, azul `#99B8E5`.
- Fontes da marca: ABC Arizona Mix (principal), ABC Arizona Sans, Xanh Mono (apoio),
  PP Eiko (adorno). Arizona e Eiko são pagas e **ainda não temos os arquivos nem a
  licença para web**. Até lá: **Newsreader** (Google Fonts) no lugar da Arizona Mix,
  aprovada pelos sócios; Xanh Mono é gratuita e pode ser usada de verdade.
- Tom de voz: bem-humorado, objetivo, desejável e próximo; frases curtas.
- Pendentes: logo e ícone do boi em vetor (SVG/PDF).

## Segurança (obrigatório antes de cadastrar clientes de verdade)

- A base guarda senhas em texto puro e as rotas `/admin/*` e `/bar/*` não exigem token.
  Antes de abrir ao público: senhas com hash e token de sessão exigido no servidor.

## Contas

- Tudo em nome do Cotito/grupo, com o e-mail adm@cotparrilla.com.
- GitHub: `cotparrilla/fidelidade`. Apple Developer: inscrição como organização feita.
  Google Cloud e Google Wallet: ainda não criados.
