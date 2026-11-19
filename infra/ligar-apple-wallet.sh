#!/usr/bin/env bash
# Liga o cartão da Apple Wallet (iPhone) no Clube Cotito. Duas etapas:
#
#   1) pedido   — cria a chave privada (fica só no seu Cloud Shell) e o arquivo
#                 de pedido de certificado (CSR) para enviar à Apple.
#   2) instalar — recebe o certificado que a Apple devolve (pass.cer), confere,
#                 e guarda tudo no servidor sem mostrar nada na tela.
#
# Rode no Cloud Shell, com o projeto do Cotito selecionado:
#   bash <(curl -fsSL https://raw.githubusercontent.com/cotparrilla/fidelidade/main/infra/ligar-apple-wallet.sh) pedido
#   bash <(curl -fsSL https://raw.githubusercontent.com/cotparrilla/fidelidade/main/infra/ligar-apple-wallet.sh) instalar

set -euo pipefail

REGIAO="southamerica-east1"
SERVICO="fidelidade"
PASTA="$HOME/cotito-apple"          # fica no seu Cloud Shell (privado)
CHAVE="$PASTA/chave_privada.pem"
CSR="$PASTA/pedido_certificado.certSigningRequest"
WWDR_URL="https://www.apple.com/certificateauthority/AppleWWDRCAG4.cer"

etapa="${1:-}"
mkdir -p "$PASTA"; chmod 700 "$PASTA"

if [ "$etapa" = "pedido" ]; then
  if [ -f "$CHAVE" ]; then
    echo "Já existe uma chave em $CHAVE (de um pedido anterior). Vou reaproveitar."
  else
    openssl genrsa -out "$CHAVE" 2048 2>/dev/null
    chmod 600 "$CHAVE"
  fi
  openssl req -new -key "$CHAVE" -out "$CSR" \
    -subj "/emailAddress=adm@cotparrilla.com/CN=Cotito Wallet/C=BR" 2>/dev/null
  echo
  echo "Pedido criado. Agora baixe o arquivo para o seu computador:"
  echo
  cloudshell download "$CSR" 2>/dev/null || \
    echo "  Menu ⋮ do Cloud Shell > Fazer download > $CSR"
  echo
  echo "Depois envie esse arquivo na Apple (Certificates > + > Pass Type ID Certificate)."
  echo "IMPORTANTE: não apague a pasta $PASTA — a chave privada mora nela."
  exit 0
fi

if [ "$etapa" = "instalar" ]; then
  [ -f "$CHAVE" ] || { echo "Não achei a chave privada. Rode primeiro a etapa 'pedido'."; exit 1; }
  CER="$(ls -t "$HOME"/pass*.cer "$PASTA"/pass*.cer 2>/dev/null | head -1 || true)"
  if [ -z "$CER" ]; then
    echo "Não achei o pass.cer. No Cloud Shell: menu ⋮ > Fazer upload > escolha o pass.cer"
    echo "baixado da Apple. Depois rode esta etapa de novo."
    exit 1
  fi
  echo "Certificado encontrado: $CER"

  openssl x509 -inform DER -in "$CER" -out "$PASTA/cert.pem" 2>/dev/null \
    || cp "$CER" "$PASTA/cert.pem"
  # confere se o certificado é do par da nossa chave
  if [ "$(openssl x509 -noout -modulus -in "$PASTA/cert.pem" | openssl md5)" != \
       "$(openssl rsa -noout -modulus -in "$CHAVE" 2>/dev/null | openssl md5)" ]; then
    echo "Esse certificado não combina com a chave deste Cloud Shell."
    echo "Ele foi gerado a partir de outro pedido. Crie o certificado na Apple de novo"
    echo "usando o arquivo de pedido desta pasta: $CSR"
    exit 1
  fi

  ASSUNTO="$(openssl x509 -noout -subject -nameopt multiline -in "$PASTA/cert.pem")"
  PASS_TYPE_ID="$(echo "$ASSUNTO" | awk -F'= ' '/userId|UID/ {print $2; exit}')"
  TEAM_ID="$(echo "$ASSUNTO" | awk -F'= ' '/organizationalUnitName/ {print $2; exit}')"
  VALIDADE="$(openssl x509 -noout -enddate -in "$PASTA/cert.pem" | cut -d= -f2)"
  [ -n "$PASS_TYPE_ID" ] && [ -n "$TEAM_ID" ] || {
    echo "Não consegui ler o Pass Type ID / Team ID do certificado. Mande esta saída ao Claude:"
    echo "$ASSUNTO" | grep -v -i email; exit 1; }

  curl -fsSL "$WWDR_URL" -o "$PASTA/wwdr.cer"
  openssl x509 -inform DER -in "$PASTA/wwdr.cer" -out "$PASTA/wwdr.pem"

  echo "Pass Type ID: $PASS_TYPE_ID"
  echo "Team ID:      $TEAM_ID"
  echo "Vence em:     $VALIDADE   (anote para renovar antes!)"
  echo
  echo "Guardando no servidor e publicando nova versão (1 a 2 minutos)..."
  gcloud run services update "$SERVICO" --region "$REGIAO" --quiet --update-env-vars \
"APPLE_TEAM_ID=$TEAM_ID,PASS_TYPE_ID=$PASS_TYPE_ID,\
APPLE_CERT_B64=$(base64 -w0 "$PASTA/cert.pem"),\
APPLE_KEY_B64=$(base64 -w0 "$CHAVE"),\
APPLE_WWDR_B64=$(base64 -w0 "$PASTA/wwdr.pem")" >/dev/null

  echo
  echo "Pronto. O cartão do iPhone está ligado."
  echo "Guarde uma cópia da pasta $PASTA no cofre de senhas (ela tem a chave privada)."
  exit 0
fi

echo "Use: ... ligar-apple-wallet.sh pedido   ou   ... ligar-apple-wallet.sh instalar"
exit 1
