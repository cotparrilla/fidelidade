#!/usr/bin/env bash
# Liga o cartão do Google Wallet (Android) no Clube Cotito.
#
# Antes: cadastrar o Cotito como emissor no Google Pay & Wallet Console e
# anotar o Issuer ID (número de ~19 dígitos).
#
# Rode no Cloud Shell, com o projeto do Cotito selecionado:
#   bash <(curl -fsSL https://raw.githubusercontent.com/cotparrilla/fidelidade/main/infra/ligar-google-wallet.sh)
#
# O que faz:
#   1. cria a conta de serviço "wallet" (o "robô" que emite os cartões)
#   2. libera, só neste projeto, a criação de chave (contas Workspace bloqueiam por padrão)
#   3. cria a chave e guarda direto no servidor, sem mostrar na tela nem deixar arquivo
#   4. publica de novo o servidor com o código mais recente
# No fim, mostra o e-mail do robô para autorizar no Wallet Console.

set -euo pipefail

REGIAO="southamerica-east1"
SERVICO="fidelidade"
REPO="https://github.com/cotparrilla/fidelidade"

PROJETO="$(gcloud config get-value project 2>/dev/null)"
[ -n "$PROJETO" ] || { echo "Selecione o projeto do Cotito no topo do console e rode de novo."; exit 1; }
ROBO="wallet@${PROJETO}.iam.gserviceaccount.com"

read -r -p "Issuer ID do Google Wallet (só números): " ISSUER
ISSUER="$(echo "$ISSUER" | tr -cd '0-9')"
[ -n "$ISSUER" ] || { echo "Issuer ID vazio."; exit 1; }

echo "1/4  Criando a conta de serviço..."
gcloud services enable walletobjects.googleapis.com iam.googleapis.com orgpolicy.googleapis.com --quiet
if ! gcloud iam service-accounts describe "$ROBO" >/dev/null 2>&1; then
  gcloud iam service-accounts create wallet --display-name="Google Wallet - Clube Cotito" --quiet
fi

echo "2/4  Liberando a criação de chave só neste projeto..."
PASTA="$(mktemp -d)"; trap 'rm -rf "$PASTA"' EXIT
for regra in iam.disableServiceAccountKeyCreation iam.managed.disableServiceAccountKeyCreation; do
  printf 'name: projects/%s/policies/%s\nspec:\n  rules:\n  - enforce: false\n' "$PROJETO" "$regra" > "$PASTA/p.yaml"
  gcloud org-policies set-policy "$PASTA/p.yaml" >/dev/null 2>&1 || true
done

echo "3/4  Criando a chave e guardando no servidor..."
CHAVE_OK=""
for tentativa in 1 2 3 4 5 6; do
  if gcloud iam service-accounts keys create "$PASTA/chave.json" --iam-account="$ROBO" --quiet >/dev/null 2>&1; then
    CHAVE_OK=1; break
  fi
  echo "     O Google ainda está aplicando a liberação. Nova tentativa em 30 s ($tentativa/6)..."
  sleep 30
done
if [ -z "$CHAVE_OK" ]; then
  echo "Não consegui criar a chave. Mande para o Claude a mensagem do comando abaixo:"
  echo "  gcloud iam service-accounts keys create /tmp/x.json --iam-account=$ROBO"
  exit 1
fi
CHAVE_B64="$(base64 -w0 "$PASTA/chave.json")"
rm -f "$PASTA/chave.json"

echo "4/4  Publicando o servidor com o Google Wallet ligado (3 a 6 minutos)..."
git clone --depth 1 -q "$REPO" "$PASTA/fidelidade"
gcloud run deploy "$SERVICO" --source "$PASTA/fidelidade" --region "$REGIAO" --quiet \
  --update-env-vars "GOOGLE_WALLET_ISSUER_ID=$ISSUER,GOOGLE_WALLET_KEY_B64=$CHAVE_B64" >/dev/null
unset CHAVE_B64

echo
echo "Pronto. Último passo, no Google Pay & Wallet Console:"
echo "  Usuários > Convidar usuário > cole o e-mail abaixo > Desenvolvedor (ou Administrador)"
echo
echo "    $ROBO"
echo
