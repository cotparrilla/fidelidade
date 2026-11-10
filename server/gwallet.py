# ══════════════════════════════════════════════════════════════
#  CLUBE BACKBONE — GOOGLE WALLET
#
#  Modelo do Google: uma CLASSE (o programa) + um OBJETO por
#  consumidor. O link "Salvar no Google Wallet" e um JWT assinado
#  com a chave da conta de servico. Push = PATCH no objeto.
#
#  Env vars necessarias no Cloud Run:
#    GOOGLE_WALLET_KEY_B64   -> JSON da conta de servico em base64
#    GOOGLE_WALLET_ISSUER_ID -> Issuer ID do Wallet Console
# ══════════════════════════════════════════════════════════════

import os
import json
import base64
import time

from google.oauth2.service_account import Credentials
from google.auth.transport.requests import AuthorizedSession
from google.auth import crypt, jwt as google_jwt

import regras

BASE_URL = "https://walletobjects.googleapis.com/walletobjects/v1"
SCOPE = "https://www.googleapis.com/auth/wallet_object.issuer"

ISSUER_ID = os.environ.get("GOOGLE_WALLET_ISSUER_ID", "")
CLASS_SUFFIX = "clube_cotito"

# endereco publico das telas (GitHub Pages) e do servidor (Cloud Run)
PAGES_URL = os.environ.get("PAGES_URL", "https://cotparrilla.github.io/fidelidade").rstrip("/")
WEB_SERVICE_URL = os.environ.get("WEB_SERVICE_URL", "").rstrip("/")

LOGO_URI = f"{PAGES_URL}/gwallet_logo_cotito.png"

_chave_info = None
_sessao = None


def _chave():
    """Carrega o JSON da conta de servico a partir da env var base64."""
    global _chave_info
    if _chave_info is None:
        b64 = os.environ.get("GOOGLE_WALLET_KEY_B64", "")
        if not b64:
            raise RuntimeError("GOOGLE_WALLET_KEY_B64 nao definida")
        _chave_info = json.loads(base64.b64decode(b64))
    return _chave_info


def _http():
    """Sessao HTTP autenticada com a conta de servico."""
    global _sessao
    if _sessao is None:
        creds = Credentials.from_service_account_info(_chave(), scopes=[SCOPE])
        _sessao = AuthorizedSession(creds)
    return _sessao


def id_classe():
    return f"{ISSUER_ID}.{CLASS_SUFFIX}"


def id_objeto(telefone):
    return f"{ISSUER_ID}.{CLASS_SUFFIX}_{telefone}"


# ──────────────────────────────────────────────────────────────
#  CLASSE (o programa de fidelidade — criada uma vez)
# ──────────────────────────────────────────────────────────────

def _payload_classe():
    return {
        "id": id_classe(),
        "issuerName": "Cotito",
        "programName": "Clube Cotito",
        "programLogo": {
            "sourceUri": {"uri": LOGO_URI},
            "contentDescription": {
                "defaultValue": {"language": "pt-BR", "value": "Clube Cotito"}
            },
        },
        "reviewStatus": "UNDER_REVIEW",
        "hexBackgroundColor": "#1C180E",
        "countryCode": "BR",
    }


def garantir_classe():
    """Cria a classe se nao existir; se existir, ATUALIZA com o payload atual."""
    s = _http()
    r = s.get(f"{BASE_URL}/loyaltyClass/{id_classe()}")
    if r.status_code == 200:
        r2 = s.put(f"{BASE_URL}/loyaltyClass/{id_classe()}", json=_payload_classe())
        if r2.status_code == 200:
            return {"status": "atualizada"}
        return {"status": "erro", "detalhe": r2.text}
    if r.status_code == 404:
        r2 = s.post(f"{BASE_URL}/loyaltyClass", json=_payload_classe())
        if r2.status_code in (200, 201):
            return {"status": "criada"}
        return {"status": "erro", "detalhe": r2.text}
    return {"status": "erro", "detalhe": r.text}


# ──────────────────────────────────────────────────────────────
#  OBJETO (o cartao de cada consumidor)
# ──────────────────────────────────────────────────────────────

HERO_BASE = f"{PAGES_URL}/strips/estilos"

# O Google baixa a imagem UMA vez por URL e guarda a copia dele: trocar o
# PNG no GitHub com o mesmo nome NAO muda o cartao no Android (foi o que
# prendeu a arte da promo de outubro/2026). Toda vez que as strips forem
# trocadas, suba este numero (ou a env var HERO_VERSAO) e chame
# POST /admin/gwallet/reatualizar para reenviar os objetos.
HERO_VERSAO = os.environ.get("HERO_VERSAO", "1")

def _hero_uri(consumidor):
    """Mesma logica da strip do Apple: boas-vindas > premio > quadro do progresso."""
    punches = int(consumidor.get("punches", 0))
    meta = int(consumidor.get("meta", 10))
    pendentes = [r for r in consumidor.get("recompensas", []) if not r.get("resgatada")]
    if any(r.get("tipo") == "boas_vindas" for r in pendentes):
        nome = "strip_estilos_boasvindas"
    elif pendentes or punches >= meta:
        nome = "strip_estilos_premio"
    else:
        nome = f"strip_estilos_{min(punches, meta - 1)}-{meta}"
    return f"{HERO_BASE}/{nome}.png?v={HERO_VERSAO}"


def _payload_objeto(consumidor):
    tel = consumidor["telefone"]
    punches = int(consumidor.get("punches", 0))
    meta = int(consumidor.get("meta", 10))

    pendentes = [r for r in consumidor.get("recompensas", []) if not r.get("resgatada")]
    tem_boas_vindas = any(r.get("tipo") == "boas_vindas" for r in pendentes)
    tem_premio = any(r.get("tipo") != "boas_vindas" for r in pendentes)

    if tem_boas_vindas:
        situacao = "Seu mate da casa está liberado. Mostre este cartão no balcão!"
    elif tem_premio or punches >= meta:
        situacao = "Executivo grátis liberado. Mostre este cartão no balcão!"
    else:
        situacao = f"Faltam {meta - punches} pontos para o executivo por nossa conta."

    aviso = consumidor.get("aviso", "")

    try:
        import storage
        config = storage.carregar_config()
    except Exception:
        config = {}

    # mesmo texto do verso do cartao Apple
    texto_regras = regras.texto_regras(meta)

    return {
        "id": id_objeto(tel),
        "classId": id_classe(),
        "state": "ACTIVE",
        "accountId": tel,
        "accountName": consumidor.get("nome", ""),
        "loyaltyPoints": {
            "label": "Pontos",
            "balance": {"string": f"{punches} de {meta}"},
        },
        "secondaryLoyaltyPoints": {
            "label": "Próxima premiação",
            "balance": {"string": regras.texto_indicacoes(consumidor, config)},
        },
        "heroImage": {
            "sourceUri": {"uri": _hero_uri(consumidor)},
            "contentDescription": {
                "defaultValue": {"language": "pt-BR", "value": "Clube Cotito"}
            },
        },
        "barcode": {
            "type": "QR_CODE",
            "value": f"{WEB_SERVICE_URL}/q/{tel}",
            "alternateText": tel,
        },
        "textModulesData": [
            {"id": "situacao", "header": "Situação", "body": situacao},
            {"id": "aviso", "header": "Último aviso", "body": aviso or "—"},
            {"id": "regras", "header": "Como funciona", "body": texto_regras},
        ],
    }


def atualizar_objeto(consumidor):
    """
    Cria ou atualiza o objeto do consumidor no Google.
    E o equivalente do push da Apple: quem tem o cartao salvo
    ve a mudanca automaticamente.
    """
    s = _http()
    corpo = _payload_objeto(consumidor)
    oid = corpo["id"]
    r = s.get(f"{BASE_URL}/loyaltyObject/{oid}")
    if r.status_code == 200:
        r2 = s.put(f"{BASE_URL}/loyaltyObject/{oid}", json=corpo)
    elif r.status_code == 404:
        r2 = s.post(f"{BASE_URL}/loyaltyObject", json=corpo)
    else:
        return {"status": "erro", "detalhe": r.text}
    if r2.status_code in (200, 201):
        return {"status": "ok"}
    return {"status": "erro", "detalhe": r2.text}


# ──────────────────────────────────────────────────────────────
#  LINK "SALVAR NO GOOGLE WALLET" (JWT assinado)
# ──────────────────────────────────────────────────────────────

def link_salvar(consumidor):
    """
    Gera o link https://pay.google.com/gp/v/save/{jwt}.

    So manda o OBJETO no JWT — a classe (nome do programa, logo, cor)
    ja existe no Google, criada/atualizada uma vez via garantir_classe(),
    e o objeto ja aponta pra ela via "classId". Reenviar a classe
    inteira em CADA link (como estava antes) so deixa o JWT maior à
    toa, e link maior = mais chance de dar problema no meio do caminho
    (cache de navegador, encurtador de URL, esse tipo de coisa).
    """
    chave = _chave()
    claims = {
        "iss": chave["client_email"],
        "aud": "google",
        "typ": "savetowallet",
        "iat": int(time.time()),
        "payload": {
            "loyaltyObjects": [_payload_objeto(consumidor)],
        },
        "origins": ["https://" + PAGES_URL.split("://", 1)[-1].split("/", 1)[0]],
    }
    signer = crypt.RSASigner.from_service_account_info(chave)
    token = google_jwt.encode(signer, claims).decode("utf-8")
    return f"https://pay.google.com/gp/v/save/{token}"
