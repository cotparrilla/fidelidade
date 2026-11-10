# Seguranca de acesso: senhas com hash e sessao por token.
#
# - Senhas: guardadas com hash (werkzeug). Senhas antigas em texto puro ainda
#   funcionam no login e sao trocadas pelo hash na hora (migracao automatica).
# - Sessao: cada login devolve um "token" assinado com SECRET_KEY. As telas
#   mandam esse token no cabecalho Authorization: Bearer <token>.
# - Regras de acesso por rota: ver regra_de_acesso() abaixo. Rota que nao
#   estiver listada como publica exige admin.

import os
import secrets
import logging

from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from werkzeug.security import generate_password_hash, check_password_hash

import storage

log = logging.getLogger(__name__)

_SECRET = os.environ.get("SECRET_KEY")
if not _SECRET:
    # Sem SECRET_KEY os tokens deixam de valer a cada novo deploy/reinicio
    # (todo mundo precisa entrar de novo). Configure a variavel no Cloud Run.
    _SECRET = secrets.token_urlsafe(48)
    log.warning("SECRET_KEY nao configurada: usando chave temporaria.")

_assinador = URLSafeTimedSerializer(_SECRET, salt="sessao-fidelidade")

VALIDADE_TOKEN = 30 * 24 * 3600   # 30 dias

_CARREGAR = {
    "garcom": storage.carregar_garcom,
    "gestor": storage.carregar_gestor,
    "admin": storage.carregar_admin,
    "colab": storage.carregar_colab,
}


# ── senhas ──────────────────────────────────────────────────

def eh_hash(senha):
    return isinstance(senha, str) and senha.startswith(("scrypt:", "pbkdf2:"))


def preparar_senha(dados):
    """Antes de salvar um cadastro: troca a senha em texto pelo hash."""
    s = dados.get("senha")
    if s and not eh_hash(s):
        dados["senha"] = generate_password_hash(s)
    return dados


def senha_confere(registro, senha, salvar):
    """
    Confere a senha digitada com a guardada. Se a guardada ainda estiver em
    texto puro (cadastro antigo) e bater, ja grava o hash no lugar.
    """
    guardada = (registro or {}).get("senha")
    if not guardada or not senha:
        return False
    if eh_hash(guardada):
        return check_password_hash(guardada, senha)
    if secrets.compare_digest(str(guardada), str(senha)):
        registro["senha"] = generate_password_hash(senha)
        try:
            salvar(registro)
        except Exception as e:
            log.warning("nao consegui migrar a senha para hash: %s", e)
        return True
    return False


def sem_senha(registro):
    r = dict(registro or {})
    r.pop("senha", None)
    return r


# ── tokens ──────────────────────────────────────────────────

def emitir_token(papel, ident):
    return _assinador.dumps({"p": papel, "i": ident})


def sessao_do_pedido(request):
    """
    Le o token do cabecalho e devolve {"papel", "id", "registro"} ou None.
    Confere a cada pedido se o cadastro ainda existe e esta ativo, para que
    desativar um atendente corte o acesso na hora.
    """
    cab = request.headers.get("Authorization", "")
    if not cab.startswith("Bearer "):
        return None
    try:
        dados = _assinador.loads(cab[7:].strip(), max_age=VALIDADE_TOKEN)
    except (BadSignature, SignatureExpired):
        return None
    papel, ident = dados.get("p"), dados.get("i")
    carregar = _CARREGAR.get(papel)
    if not carregar or not ident:
        return None
    registro = carregar(ident)
    if not registro or not registro.get("ativo", True):
        return None
    return {"papel": papel, "id": ident, "registro": registro}


# ── regras de acesso ────────────────────────────────────────

_PUBLICAS_EXATAS = {
    "/", "/login", "/login-gestor", "/login-admin", "/login-colab",
    "/mensagens", "/extrair-padrinho",
}
_PUBLICAS_PREFIXO = (
    "/cadastro/", "/consumidor/", "/cartao/", "/gwallet/", "/v1/", "/q/", "/c/",
)
_SCANS = {"/scan", "/punch", "/resgatar", "/scan-prato", "/resgatar-prato"}


def _gestor_ve_bar(registro, bar_id):
    bars = registro.get("bar_ids", [])
    return "*" in bars or bar_id in bars


def regra_de_acesso(request):
    """
    Devolve None se o pedido pode seguir, ou (dicionario_de_erro, status).
    """
    if request.method == "OPTIONS":
        return None
    path = request.path.rstrip("/") or "/"

    if path in _PUBLICAS_EXATAS or path.startswith(_PUBLICAS_PREFIXO):
        return None

    s = sessao_do_pedido(request)
    if not s:
        return {"erro": "nao_autorizado"}, 401
    papel, reg = s["papel"], s["registro"]
    if papel == "admin":
        return None   # admin acessa tudo

    proibido = ({"erro": "proibido"}, 403)
    partes = path.split("/")   # ["", "bar", "<id>", "atividade"]
    corpo = request.get_json(silent=True) or {}

    # lista de unidades: qualquer pessoa logada
    if path == "/admin/bares" and request.method == "GET":
        return None

    # gestor cria/edita atendentes e colabs das proprias unidades
    if path in ("/admin/garcons", "/admin/colabs") and request.method == "POST":
        if papel == "gestor" and _gestor_ve_bar(reg, corpo.get("bar_id", "")):
            return None
        return proibido

    if path.startswith("/admin/"):
        return proibido

    # paineis da unidade
    if partes[1] == "bar" and len(partes) >= 4:
        bar_id = partes[2]
        if papel == "gestor" and _gestor_ve_bar(reg, bar_id):
            return None
        if papel == "garcom" and reg.get("bar_id") == bar_id and partes[3] == "atividade":
            return None
        return proibido

    # escanear: so em nome de quem esta logado
    if path in _SCANS:
        if papel not in ("garcom", "gestor"):
            return proibido
        if corpo.get("garcom_id") and corpo.get("garcom_id") != s["id"]:
            return proibido
        return None

    if partes[1] == "garcom" and len(partes) >= 4:
        if papel == "gestor" or (papel == "garcom" and partes[2] == s["id"]):
            return None
        return proibido

    if partes[1] == "colab" and len(partes) >= 4:
        colab_id, acao = partes[2], partes[3]
        if papel == "gestor":
            return None
        if papel == "colab" and colab_id == s["id"]:
            return None
        if papel == "garcom" and acao == "pratos":
            return None
        return proibido

    return proibido
