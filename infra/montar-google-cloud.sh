#!/usr/bin/env bash
# Monta o Clube Cotito num projeto novo do Google Cloud.
#
# Rode no Cloud Shell (ícone ">_" no topo do console), com o projeto certo
# selecionado no topo da tela:
#
#   bash <(curl -fsSL https://raw.githubusercontent.com/cotparrilla/fidelidade/main/infra/montar-google-cloud.sh)
#
# O que faz (pode rodar de novo sem estragar nada):
#   1. liga os serviços do Google que o sistema usa
#   2. cria o armazenamento dos dados (bucket privado)
#   3. dá as permissões que o servidor e o deploy precisam
#   4. publica o servidor no Cloud Run (região São Paulo)
#   5. gera a chave das sessões (SECRET_KEY) sem mostrar na tela
#   6. cria o primeiro login de dono (admin)
# No fim, mostra o endereço do servidor para colar no config.js.

set -euo pipefail

REGIAO="southamerica-east1"
SERVICO="fidelidade"
REPO="https://github.com/cotparrilla/fidelidade"
PAGES_URL="https://cotparrilla.github.io/fidelidade"

PROJETO="$(gcloud config get-value project 2>/dev/null)"
if [ -z "$PROJETO" ]; then
  echo "Nenhum projeto selecionado. Escolha o projeto no topo do console e rode de novo."
  exit 1
fi
PN="$(gcloud projects describe "$PROJETO" --format='value(projectNumber)')"
SA="${PN}-compute@developer.gserviceaccount.com"
BUCKET="${PROJETO}-dados"

echo "Projeto: $PROJETO"
echo
echo "1/6  Ligando os serviços (leva 1 a 2 minutos)..."
gcloud services enable run.googleapis.com cloudbuild.googleapis.com \
  artifactregistry.googleapis.com storage.googleapis.com \
  walletobjects.googleapis.com iam.googleapis.com --quiet

echo "2/6  Criando o armazenamento de dados ($BUCKET)..."
if ! gcloud storage buckets describe "gs://$BUCKET" >/dev/null 2>&1; then
  gcloud storage buckets create "gs://$BUCKET" --location="$REGIAO" \
    --uniform-bucket-level-access --public-access-prevention --quiet
fi

echo "3/6  Dando as permissões..."
gcloud storage buckets add-iam-policy-binding "gs://$BUCKET" \
  --member="serviceAccount:$SA" --role=roles/storage.objectAdmin --quiet >/dev/null
for papel in roles/run.admin roles/artifactregistry.writer roles/logging.logWriter \
             roles/storage.admin roles/cloudbuild.builds.builder; do
  gcloud projects add-iam-policy-binding "$PROJETO" --member="serviceAccount:$SA" \
    --role="$papel" --condition=None --quiet >/dev/null
done
gcloud iam service-accounts add-iam-policy-binding "$SA" --member="serviceAccount:$SA" \
  --role=roles/iam.serviceAccountUser --quiet >/dev/null
if ! gcloud artifacts repositories describe cloud-run-source-deploy --location="$REGIAO" >/dev/null 2>&1; then
  gcloud artifacts repositories create cloud-run-source-deploy --repository-format=docker \
    --location="$REGIAO" --quiet
fi

echo "4/6  Publicando o servidor (leva de 3 a 6 minutos)..."
PASTA="$(mktemp -d)"
git clone --depth 1 -q "$REPO" "$PASTA/fidelidade"

# Mantém a SECRET_KEY de uma instalação anterior, para ninguém ser deslogado.
SEGREDO="$(gcloud run services describe "$SERVICO" --region "$REGIAO" --format=json 2>/dev/null \
  | python3 -c 'import json,sys
try:
    env = json.load(sys.stdin)["spec"]["template"]["spec"]["containers"][0].get("env", [])
    print(next((e.get("value","") for e in env if e.get("name") == "SECRET_KEY"), ""))
except Exception:
    print("")' || true)"
if [ -z "$SEGREDO" ]; then
  SEGREDO="$(python3 -c 'import secrets;print(secrets.token_urlsafe(48))')"
fi

gcloud run deploy "$SERVICO" --source "$PASTA/fidelidade" --region "$REGIAO" \
  --allow-unauthenticated --min-instances 1 --timeout 1200 --quiet \
  --update-env-vars "BUCKET_NAME=$BUCKET,SECRET_KEY=$SEGREDO,PAGES_URL=$PAGES_URL,ORG_NAME=Cotito" >/dev/null

URL="$(gcloud run services describe "$SERVICO" --region "$REGIAO" --format='value(status.url)')"
echo "5/6  Gravando o endereço do servidor..."
gcloud run services update "$SERVICO" --region "$REGIAO" \
  --update-env-vars "WEB_SERVICE_URL=$URL" --quiet >/dev/null

echo "6/6  Primeiro login de dono"
if gcloud storage ls "gs://$BUCKET/admins/" >/dev/null 2>&1; then
  echo "     Já existe login de dono. Pulando."
else
  read -r -p "     Código de login (ex.: dono): " ADM_ID
  read -r -p "     Nome: " ADM_NOME
  read -r -s -p "     Senha (não aparece enquanto digita): " ADM_SENHA; echo
  ADM_ID="$ADM_ID" ADM_NOME="$ADM_NOME" ADM_SENHA="$ADM_SENHA" python3 - > "$PASTA/admin.json" <<'PY'
import hashlib, json, os, secrets
senha = os.environ["ADM_SENHA"].encode()
sal = secrets.token_hex(8)
it = 600000
# mesmo formato do werkzeug (check_password_hash)
h = hashlib.pbkdf2_hmac("sha256", senha, sal.encode(), it).hex()
print(json.dumps({"id": os.environ["ADM_ID"].strip(), "nome": os.environ["ADM_NOME"].strip(),
                  "senha": f"pbkdf2:sha256:{it}${sal}${h}", "ativo": True}, ensure_ascii=False))
PY
  ADM_ID_LIMPO="$(echo "$ADM_ID" | tr -d '[:space:]')"
  gcloud storage cp "$PASTA/admin.json" "gs://$BUCKET/admins/${ADM_ID_LIMPO}.json" --quiet >/dev/null
  echo "     Login de dono criado: $ADM_ID_LIMPO"
fi
rm -rf "$PASTA"

echo
echo "Pronto. Endereço do servidor:"
echo
echo "    $URL"
echo
echo "Copie esse endereço e mande para o Claude (ele não é segredo)."
