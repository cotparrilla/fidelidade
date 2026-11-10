# Regras do Clube Cotito (ver DECISOES-COTITO.md).
#
# - Ponto: 1 por leitura quando o pedido tem executivo; bloqueio de N horas
#   entre pontos do mesmo cartao (config "bloqueio_ponto_horas", padrao 2).
# - Premio: 10 pontos = 1 executivo gratis.
# - Boas-vindas: um mate da casa, liberado no balcao.
# - Indicacao: conta para quem indicou quando o indicado RETIRA O MATE.
#   Contador vitalicio. Brindes em degraus fixos e cumulativos
#   (config "brindes_indicacao", padrao bone com 15 e camiseta com 45).

from datetime import datetime, timezone, timedelta

NOME_CLUBE = "Clube Cotito"

BRINDES_PADRAO = [
    {"qtd": 15, "nome": "Boné"},
    {"qtd": 45, "nome": "Camiseta"},
]
BLOQUEIO_PADRAO_HORAS = 2


def brindes_config(config):
    lista = (config or {}).get("brindes_indicacao") or BRINDES_PADRAO
    limpa = []
    for b in lista:
        try:
            qtd = int(b.get("qtd"))
        except (TypeError, ValueError):
            continue
        nome = (b.get("nome") or "").strip()
        if qtd > 0 and nome:
            limpa.append({"qtd": qtd, "nome": nome})
    return sorted(limpa, key=lambda b: b["qtd"])


def horas_bloqueio(config):
    try:
        return max(0.0, float((config or {}).get("bloqueio_ponto_horas", BLOQUEIO_PADRAO_HORAS)))
    except (TypeError, ValueError):
        return float(BLOQUEIO_PADRAO_HORAS)


def _data(iso):
    if not iso:
        return None
    try:
        d = datetime.fromisoformat(iso)
        return d if d.tzinfo else d.replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def proximo_ponto_em(consumidor, config, agora=None):
    """Quando o cartao pode ganhar o proximo ponto (datetime) ou None se ja pode."""
    ultimo = _data(consumidor.get("ultimo_punch"))
    if not ultimo:
        return None
    libera = ultimo + timedelta(hours=horas_bloqueio(config))
    agora = agora or datetime.now(timezone.utc)
    return libera if libera > agora else None


def indicacoes(consumidor):
    return int(consumidor.get("indicacoes_confirmadas", 0))


def status_brindes(consumidor, config):
    """
    Devolve um resumo da trilha de indicacao:
      total, brindes (com conquistado/entregue), proximo (degrau) e pendentes
      (conquistados e ainda nao entregues, na ordem).
    """
    total = indicacoes(consumidor)
    entregues = {e.get("qtd") for e in consumidor.get("brindes_entregues", [])}
    brindes, pendentes, proximo = [], [], None
    for b in brindes_config(config):
        conquistado = total >= b["qtd"]
        entregue = b["qtd"] in entregues
        item = dict(b, conquistado=conquistado, entregue=entregue)
        brindes.append(item)
        if conquistado and not entregue:
            pendentes.append(item)
        if not conquistado and proximo is None:
            proximo = item
    return {"total": total, "brindes": brindes, "proximo": proximo, "pendentes": pendentes}


def texto_indicacoes(consumidor, config):
    """Ex.: '7/15 indicações' (rumo ao proximo brinde) ou '52 indicações'."""
    st = status_brindes(consumidor, config)
    if st["proximo"]:
        return f"{st['total']}/{st['proximo']['qtd']} indicações"
    return f"{st['total']} indicações"


def texto_regras(meta):
    return (
        f"Mostre este cartão no balcão a cada pedido com executivo e ganhe 1 ponto. "
        f"No {meta}º ponto, o próximo executivo é por nossa conta.\n\n"
        f"Para resgatar, mostre o cartão no balcão: o atendente escaneia e você abre "
        f"uma nova cartela, começando em 0/{meta}.\n\n"
        f"Indique amigos: mostre o QR do seu cartão para a câmera do celular deles. "
        f"Quando o amigo se cadastrar e pegar o mate da casa, a indicação conta para "
        f"você e vale brindes do Cotito."
    )
