# Adaptação para um restaurante (uma única casa)

Regra de fidelidade definida: **a cada 10 pratos consumidos, o cliente ganha 1 prato**.

Este documento lista o que muda em relação ao Clube Backbone, em ordem de trabalho.
Cada item é uma decisão para o dono aprovar antes de programar (com mockup, se for tela).

## 1. O que já serve como está

- Cadastro por QR/link, cartão na Apple e Google Wallet, scanner do atendente, atualização
  automática do cartão, push, painel admin, mensagens do cliente, lista de bloqueados,
  antifraude, colabs (parceiros que indicam).
- A meta do ciclo é configurável (`punches_para_recompensa` em `/admin/config`):
  **basta colocar 10**. A tela de configuração já existe no admin.

## 2. Trocas de texto e marca (obrigatório)

Procure e troque nestes pontos (todos têm "Backbone", "chopp" ou endereço da base):

| Onde | O que trocar |
|---|---|
| `server/pkpass.py` linhas ~23-30, ~203-211, ~248 | `PASS_TYPE_ID`, `ORG_NAME`, URLs, texto do verso ("a cada chopp... décimo... Chopp Pilsen 300 ml"), `description` |
| `server/gwallet.py` linhas ~26-29, ~70-75, ~105, ~149-150, ~175-180, ~236 | `CLASS_SUFFIX`, logo, nome do emissor e do programa, URL do hero, texto, QR, `origins` |
| `server/main.py` | `PASS_TYPE_ID` padrão, texto de boas-vindas (~linha 138), nome do arquivo `.pkpass`, destinos `cadastro.html` (~1344/1362), nome do sistema na rota `/` |
| `server/storage.py` linha 10 | `BUCKET_NAME` (bucket novo do restaurante) |
| `server/apns.py` linha 18 | `TOPIC` padrão |
| `cloudbuild.yaml` | nome do serviço (`backbone`) e do repositório de imagens, se quiser renomear |
| Todas as telas `.html` | constante `SERVER` (URL do Cloud Run novo), textos "chopp", "Clube Backbone", logo, cores |
| `como_funciona.html`, `escolha.html`, `cadastro.html` | textos de benefícios e imagens |

Dica: ideal é centralizar essas constantes em variáveis de ambiente ou num bloco no topo
de cada arquivo, em vez de repetir. Vale fazer isso logo no começo.

## 3. Vocabulário: "chopp" vira "prato"

O código chama o consumo de "chopp" (`chopps_totais`, evento `resgate`, etc.). Duas opções:

1. **Só trocar o rótulo nas telas** (recomendado): nomes internos continuam, o cliente e o
   atendente só veem "prato". Rápido e seguro.
2. Renomear os campos internos: limpo, mas mexe em muita coisa e quebra dados antigos
   (desnecessário num projeto novo, mas exige cuidado).

Cuidado: na base existe também o conceito de **"prato" para colabs** (modo Prato:
`/scan-prato`, `/resgatar-prato`). No restaurante o "prato" passa a ser o consumo do
próprio cliente. Decidir:

- **Manter ou remover o modo Prato de colab?** Ele só faz sentido se o restaurante quiser
  parceiros (ex.: porteiros de hotel) ganhando prato por indicados. Se não, remova para
  não confundir com o consumo principal.

## 4. Simplificações porque é uma casa só

- **"Bares" vira uma só unidade.** Pode continuar existindo 1 registro em `bares/` (menos
  mudança) e esconder nas telas a escolha/lista de bares e a coluna de bares.
- **Gestor de várias unidades** deixa de ser necessário. O dono usa o admin; o gestor
  pode ser o gerente do salão.
- **Reembolso por unidade** (aba Reembolsos/Reembolso): foi criado porque a cervejaria
  paga o chopp grátis dos bares parceiros. **Não se aplica** a um restaurante com uma
  casa só. Remover a aba, as rotas `/admin/reembolsos`, `/bar/<id>/reembolsos` e
  `storage` de descontos (opcional, não atrapalha se ficar).
- **Antifraude por unidade (lista fria por bar):** simplificar para uma lista única.

## 5. O que fazer com os marcos de 50 e 100

Na base: 50 = visita à fábrica (manual), 100 = muda de árvore (automático a cada 100,
`main.py` ~linha 264-267, aba Árvores do admin, imagens `muda_*.jpg` em `cadastro.html`).
O restaurante provavelmente **não quer isso**. Decidir:

- Remover (aba Árvores, texto e imagens no cadastro, regra `% 100`), ou
- Trocar por um marco próprio (ex.: a cada 50 pratos, uma sobremesa/bebida de cortesia;
  a cada 100, um jantar para dois).

## 6. Estímulo ao cadastro (o "gancho")

Na base: **primeiro chopp grátis** ao confirmar o cadastro no bar (boas-vindas). Para o
restaurante, definir o gancho equivalente. Sugestões a validar com o dono:

- Uma sobremesa ou entrada de cortesia na primeira visita;
- Um desconto na primeira conta;
- Sorteio mensal entre os cadastrados.

Qualquer que seja a escolha, o texto aparece em `cadastro.html` (blocos de benefícios),
na tela de boas-vindas, no cartão (`pkpass.py` e `gwallet.py`) e no evento de boas-vindas
do servidor. Se for só desconto ou sorteio, o fluxo de "chopp grátis confirmado pelo
garçom" pode ser simplificado.

Os blocos de benefícios do cadastro foram desenhados em dois grupos: **âmbar** para
metas de pontos e **cinza** para descontos de parceiros (vestuário, delivery, pousadas na
base). Troque os parceiros por os do restaurante ou remova.

## 7. Arte do cartão

- Na base há **12 artes** de faixa: uma por estágio da cartela de 10 (0/10 a 9/10), uma de
  boas-vindas e uma de prêmio, com o contador X/10 gravado na imagem.
- Para o restaurante: refazer as 12 artes (375×123 px no 1x; entregue em 3x = 1125×369),
  com o contador na própria arte, concentrando os elementos no centro (corte lateral).
- Logo do Wallet: ícone (29/58/87 px), logo do cartão, `gwallet_logo` para o Google.
- Fonte e cores da marca do restaurante (a base usa GT Sectra Black, preto e âmbar). A fonte GT Sectra é comercial e licenciada para a Backbone: **não está neste repositório**; os `@font-face` das telas apontam para ela e precisam ser trocados por uma fonte do restaurante.
- As fotos de árvores (`muda_*.jpg`) também foram retiradas; os textos que as usam vão junto com a decisão da seção 5.

## 8. Itens que não vêm ao caso (podem ser removidos)

- Integração/legado com BotConversa/WhatsApp (modo de compatibilidade em `cadastro.html`).
- Alloy (CRM em avaliação) e todas as estratégias de parceria de marca.
- Dados reais da base: **não copiar** consumidores, eventos, mensagens, bloqueados.

## 9. Ordem sugerida de trabalho

1. Montar contas, bucket e deploy com a base **sem mudar nada** (ver `MONTAGEM-DO-ZERO.md`)
   e testar o fluxo inteiro com um telefone de teste.
2. Trocar marca, textos e arte (seções 2, 3 e 7).
3. Definir o gancho de cadastro e os benefícios (seções 5 e 6).
4. Simplificar para casa única (seção 4).
5. Só depois: novidades (colabs/parceiros, iOS 27, mensagens e campanhas).
