# Comece aqui — como usar o pacote do sistema de fidelidade

Este texto é para você, que vai montar o programa de fidelidade do seu restaurante.
Você não precisa saber programar: quem programa é o Claude, e este pacote faz com que ele
já entenda tudo que foi construído. Você decide, aprova e dá o "ok" final.

**O que é o sistema:** um cartão de fidelidade que mora na carteira do celular do cliente
(Apple Wallet e Google Wallet). O garçom escaneia o cartão a cada prato consumido. A cada 10
pratos, o cliente ganha 1 prato. Existem painéis para o dono, o gerente e o garçom.

**O que você recebeu:** um arquivo ZIP (`fidelidade-restaurante-base.zip`) com o código
pronto e 3 documentos de instrução. O código vem da cervejaria da família e precisa ser
adaptado para o restaurante.

---

## Parte 1 — Contas (comece já, algumas demoram)

Você precisa de quatro contas, todas no **seu nome** (ou da empresa do restaurante).
Nada é compartilhado com a cervejaria.

| Conta | Para quê | Quanto demora |
|---|---|---|
| **Apple Developer Program** | Cartão no iPhone | Pode levar vários dias para aprovar. Anuidade em dólar. Para empresa, precisa de CNPJ e número D-U-N-S |
| **Google Cloud** | Onde o sistema roda e guarda os dados | Minutos. Pede cartão para cobrança |
| **Google Wallet (emissor)** | Cartão no Android | Minutos para cadastrar; a publicação para o público pode levar alguns dias |
| **GitHub** | Onde fica o código e as telas | Minutos. Gratuito |

**Comece pela Apple**, porque é a que demora. Enquanto espera, siga com o resto.

## Parte 2 — Colocar o código no GitHub

1. Entre no GitHub e crie um **repositório novo**. Sugestão de nome: `fidelidade`.
   Deixe **público** (o GitHub gratuito exige isso para publicar as telas). Não marque
   nenhuma opção de "adicionar arquivos" (README, .gitignore).
2. No computador, **descompacte o ZIP**. Vai aparecer uma pasta `fidelidade`.
3. No repositório novo, clique em **Add file › Upload files** e arraste **todo o conteúdo**
   da pasta (os arquivos e pastas de dentro, não a pasta `fidelidade` em si).
   Confira que `CLAUDE.md` ficou na primeira tela, junto de `admin.html`.
   Se o GitHub reclamar do número de arquivos, envie em dois ou três lotes.
4. Clique em **Commit changes**.
5. Ative a publicação das telas: **Settings › Pages**, em *Branch* escolha `main` e a pasta
   `/ (root)`, e salve. Em alguns minutos o GitHub mostra o endereço
   (`https://seu-usuario.github.io/fidelidade/`).

## Parte 3 — Conectar o Claude ao repositório

1. Abra o Claude (o aplicativo ou o claude.ai) e crie um **projeto novo** para o restaurante.
2. Conecte o GitHub ao Claude e **instale o app do Claude no repositório** `fidelidade`
   (o GitHub pede a autorização na tela).
3. Diga ao Claude, com estas palavras ou parecidas:

   > Este é o repositório do programa de fidelidade do meu restaurante. Leia o `CLAUDE.md`
   > e os outros dois documentos na raiz. Sou do ramo de restaurantes e não programo.
   > Vamos montar tudo do zero seguindo o `MONTAGEM-DO-ZERO.md`, um passo de cada vez.

   Ele já sabe como trabalhar com você: explica em linguagem simples, mostra o desenho
   antes de mexer em qualquer tela e pede sua aprovação.

## Parte 4 — A ordem certa de trabalho

Siga esta ordem. **Não pule** para a personalização antes de o teste da etapa 1 funcionar.

1. **Montar e testar sem mudar nada** (`MONTAGEM-DO-ZERO.md`): criar o projeto no Google Cloud,
   o armazenamento, o serviço, os certificados e fazer um cadastro de teste com o seu próprio
   telefone até o cartão aparecer na carteira e atualizar. O Claude acompanha cada passo;
   você faz o que exige o seu login (criar contas, aceitar termos, colar chaves).
2. **Trocar a marca** (`ADAPTACAO-RESTAURANTE.md`, seções 2, 3 e 7): nome, logo, cores,
   textos e a arte do cartão. Para a arte, peça ao Claude as medidas e o que cada imagem
   precisa ter.
3. **Decidir o gancho de cadastro e os benefícios** (seções 5 e 6): o que o cliente ganha ao
   se cadastrar, e se haverá marcos (por exemplo, um prêmio especial aos 50 ou 100 pratos).
4. **Simplificar para um restaurante só** (seção 4): o sistema nasceu para vários bares; o
   Claude esconde o que você não usa.
5. **Colocar para valer:** cadastrar os garçons, imprimir o QR do cadastro para as mesas e
   treinar a equipe. Comece com poucas mesas e um garçom, antes de abrir para todo o salão.

## Parte 5 — O dia a dia com o Claude

- **Peça uma coisa de cada vez.** Quando for uma tela, ele mostra o desenho primeiro. Só
  diga "pode fazer" depois de aprovar.
- **O Claude trabalha numa cópia do código e abre um "pull request"** (uma proposta de
  mudança). Nada vai para o ar até você aprovar e clicar em **Merge** no GitHub.
- **Depois do Merge**, espere uns 3 a 5 minutos: o sistema se atualiza sozinho. Se algo parar,
  avise o Claude com a mensagem exata e uma foto da tela.
- **Se o Claude perguntar de onde veio uma configuração, não improvise.** Ele deve sempre
  partir do arquivo atual do repositório.

## Parte 6 — Cuidados que valem ouro

- **Nunca cole uma senha, chave ou certificado numa conversa.** Se escapar, avise o Claude
  na hora: a chave será trocada. As chaves ficam só nas configurações do Google Cloud.
- **Faça backup das chaves da Apple e do Google** num cofre de senhas.
- **Anote a data de vencimento do certificado da Apple** (em geral um ano) e renove antes.
- **Só use o cadastro de clientes de verdade depois de testar bastante** com seu próprio
  telefone e o de alguém da equipe, em iPhone e Android.
- O sistema guarda **dados pessoais de clientes** (nome e telefone). Avise no cadastro que
  isso acontece e para quê (LGPD). O Claude pode ajudar a redigir o texto.

## Parte 7 — Se algo der errado

| Sintoma | Primeiro passo |
|---|---|
| Tela mostra "Sem conexão" ou "Service Unavailable" | Avise o Claude. Ele vai pedir o registro (log) do Cloud Run |
| Mudei algo e não apareceu | Espere o Merge terminar (3 a 5 min) e recarregue a página com Ctrl+Shift+R |
| Cartão não chega na carteira | Diga o modelo do celular (iPhone ou Android) e mande uma foto da tela |
| Dúvida geral | Pergunte ao Claude: ele leu os 3 documentos e conhece o sistema inteiro |

Boa montagem!
