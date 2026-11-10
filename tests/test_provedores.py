# -*- coding: utf-8 -*-
"""Testes do provedor Gemini com um transporte HTTP falso (sem rede e sem gastar cota)."""

import json

import httpx
import pytest

from rag_sus.provedores import (
    URL_GEMINI,
    CotaDiariaEsgotada,
    ProvedorGemini,
    RecusaDoModelo,
    SaldoEsgotado,
)

ESQUEMA = {"type": "object", "properties": {"x": {"type": "integer"}}, "required": ["x"]}
SISTEMA = [{"type": "text", "text": "sistema"}]


def resposta_ok(texto='{"x": 7}', motivo="STOP"):
    return {
        "candidates": [{"content": {"parts": [{"text": texto}]}, "finishReason": motivo}],
        "usageMetadata": {"promptTokenCount": 1200, "candidatesTokenCount": 30,
                          "thoughtsTokenCount": 50, "cachedContentTokenCount": 1000},
        "modelVersion": "gemini-teste",
        "responseId": "abc",
    }


def erro_429(quota_id, atraso="2s"):
    return {"error": {"code": 429, "status": "RESOURCE_EXHAUSTED", "details": [
        {"@type": "type.googleapis.com/google.rpc.QuotaFailure", "violations": [{"quotaId": quota_id}]},
        {"@type": "type.googleapis.com/google.rpc.RetryInfo", "retryDelay": atraso},
    ]}}


def provedor(respostas, pedidos=None, pausas=None):
    fila = list(respostas)

    def tratar(req: httpx.Request) -> httpx.Response:
        if pedidos is not None:
            pedidos.append(req)
        status, corpo = fila.pop(0)
        return httpx.Response(status, json=corpo)

    cliente = httpx.Client(base_url=URL_GEMINI, transport=httpx.MockTransport(tratar))
    dormir = pausas.append if pausas is not None else (lambda s: None)
    return ProvedorGemini("gemini-teste", "medium", 500, cliente=cliente, dormir=dormir)


def test_monta_pedido_com_esquema_e_le_metadados():
    pedidos = []
    dados, meta = provedor([(200, resposta_ok())], pedidos).gerar_json(SISTEMA, "pergunta", ESQUEMA)

    assert dados == {"x": 7}
    corpo = json.loads(pedidos[0].content)
    assert pedidos[0].url.path.endswith("/models/gemini-teste:generateContent")
    assert corpo["systemInstruction"]["parts"] == [{"text": "sistema"}]
    assert corpo["generationConfig"]["responseJsonSchema"] == ESQUEMA
    assert corpo["generationConfig"]["thinkingConfig"] == {"thinkingLevel": "medium"}
    assert (meta.tokens_entrada, meta.tokens_saida, meta.tokens_cache_leitura) == (1200, 80, 1000)
    assert meta.id_requisicao == "abc" and not meta.usou_fallback and meta.custo_usd == 0.0


def test_cota_por_minuto_espera_o_que_a_api_manda_e_tenta_de_novo():
    pausas = []
    p = provedor([(429, erro_429("GenerateRequestsPerMinutePerProjectPerModel-FreeTier", "41s")),
                  (200, resposta_ok())], pausas=pausas)

    dados, _ = p.gerar_json(SISTEMA, "m", ESQUEMA)

    assert dados == {"x": 7} and pausas == [42.0]


def test_cota_diaria_para_sem_insistir():
    p = provedor([(429, erro_429("GenerateRequestsPerDayPerProjectPerModel-FreeTier"))])
    with pytest.raises(CotaDiariaEsgotada):
        p.gerar_json(SISTEMA, "m", ESQUEMA)


def test_saldo_pre_pago_zerado_para_sem_insistir():
    # Projeto com os créditos do Google AI Pro: o saldo zerado é o teto de gasto.
    p = provedor([(402, {"error": {"code": 402}})])
    with pytest.raises(SaldoEsgotado):
        p.gerar_json(SISTEMA, "m", ESQUEMA)


def test_bloqueio_de_seguranca_vira_recusa():
    p = provedor([(200, resposta_ok(texto="", motivo="SAFETY"))])
    with pytest.raises(RecusaDoModelo):
        p.gerar_json(SISTEMA, "m", ESQUEMA)


def test_ignora_partes_de_pensamento():
    r = resposta_ok()
    r["candidates"][0]["content"]["parts"].insert(0, {"text": "pensando...", "thought": True})
    dados, _ = provedor([(200, r)]).gerar_json(SISTEMA, "m", ESQUEMA)
    assert dados == {"x": 7}


def test_latencia_mede_so_a_requisicao_que_deu_certo_e_nao_as_esperas():
    # A latência entra na comparação entre Condições; as esperas da cota não podem contar.
    agora = [0.0]

    def tratar(req: httpx.Request) -> httpx.Response:
        agora[0] += 3.0  # cada requisição leva 3 s no relógio falso
        if tratar.chamadas == 0:
            tratar.chamadas += 1
            return httpx.Response(429, json=erro_429("GenerateRequestsPerMinutePerProjectPerModel-FreeTier", "41s"))
        return httpx.Response(200, json=resposta_ok())

    tratar.chamadas = 0
    cliente = httpx.Client(base_url=URL_GEMINI, transport=httpx.MockTransport(tratar))

    def dormir(s):
        agora[0] += s

    p = ProvedorGemini("gemini-teste", "medium", 500, cliente=cliente, dormir=dormir, relogio=lambda: agora[0])
    _, meta = p.gerar_json(SISTEMA, "m", ESQUEMA)

    assert meta.latencia_s == pytest.approx(3.0)


class ProvedorFalso:
    def __init__(self, modelo, esgotado=False):
        self.modelo = modelo
        self.esgotado = esgotado
        self.chamadas = 0

    def gerar_json(self, sistema, mensagem, esquema):
        self.chamadas += 1
        if self.esgotado:
            raise CotaDiariaEsgotada(f"cota diária esgotada para {self.modelo}")
        from rag_sus.provedores import Metadados
        return {"x": 1}, Metadados(self.modelo, self.modelo, False)


def test_cadeia_passa_ao_proximo_modelo_quando_a_cota_diaria_acaba_e_nao_volta_ao_esgotado():
    from rag_sus.provedores import ProvedorEmCadeia
    a, b = ProvedorFalso("modelo-a", esgotado=True), ProvedorFalso("modelo-b")
    cadeia = ProvedorEmCadeia([a, b])

    _, meta1 = cadeia.gerar_json(SISTEMA, "m", ESQUEMA)
    _, meta2 = cadeia.gerar_json(SISTEMA, "m", ESQUEMA)

    assert (meta1.modelo_que_respondeu, meta2.modelo_que_respondeu) == ("modelo-b", "modelo-b")
    assert (a.chamadas, b.chamadas) == (1, 2)


def test_cadeia_com_todos_os_modelos_esgotados_para_com_cota_diaria_esgotada():
    from rag_sus.provedores import ProvedorEmCadeia
    cadeia = ProvedorEmCadeia([ProvedorFalso("a", esgotado=True), ProvedorFalso("b", esgotado=True)])
    with pytest.raises(CotaDiariaEsgotada, match="a, b"):
        cadeia.gerar_json(SISTEMA, "m", ESQUEMA)


def test_juiz_do_ambiente_monta_a_cadeia_so_quando_ha_reservas_no_gemini(monkeypatch):
    from rag_sus.provedores import ProvedorEmCadeia, ProvedorOllama, juiz_do_ambiente
    monkeypatch.setenv("GEMINI_API_KEY", "chave-falsa")
    monkeypatch.setenv("PROVEDOR", "gemini")

    cadeia = juiz_do_ambiente(["a", "b"], "medium", 100)
    assert isinstance(cadeia, ProvedorEmCadeia) and [p.modelo for p in cadeia.provedores] == ["a", "b"]
    assert isinstance(juiz_do_ambiente(["a"], "medium", 100), ProvedorGemini)

    monkeypatch.setenv("PROVEDOR", "ollama")
    assert isinstance(juiz_do_ambiente(["a", "b"], "medium", 100), ProvedorOllama)


def provedor_com_tratador(tratar, pausas=None, tentativas=6):
    cliente = httpx.Client(base_url=URL_GEMINI, transport=httpx.MockTransport(tratar))
    dormir = pausas.append if pausas is not None else (lambda s: None)
    return ProvedorGemini("gemini-teste", "medium", 500, cliente=cliente, dormir=dormir, tentativas=tentativas)


def test_tempo_esgotado_e_tentado_de_novo_como_sobrecarga():
    # Plano gratuito: às vezes o modelo não responde nunca; a requisição presa não pode derrubar a Rodada.
    chamadas = []

    def tratar(req):
        chamadas.append(req)
        if len(chamadas) == 1:
            raise httpx.ReadTimeout("sem resposta", request=req)
        return httpx.Response(200, json=resposta_ok())

    pausas = []
    dados, _ = provedor_com_tratador(tratar, pausas).gerar_json(SISTEMA, "m", ESQUEMA)

    assert dados == {"x": 7} and len(chamadas) == 2 and len(pausas) == 1


def test_modelo_que_nunca_responde_vira_modelo_indisponivel():
    from rag_sus.provedores import ModeloIndisponivel

    def tratar(req):
        raise httpx.ReadTimeout("sem resposta", request=req)

    with pytest.raises(ModeloIndisponivel, match="gemini-teste"):
        provedor_com_tratador(tratar, tentativas=3).gerar_json(SISTEMA, "m", ESQUEMA)


def test_sobrecarga_que_nao_passa_vira_modelo_indisponivel():
    from rag_sus.provedores import ModeloIndisponivel

    def tratar(req):
        return httpx.Response(503, json={"error": {"code": 503}})

    with pytest.raises(ModeloIndisponivel):
        provedor_com_tratador(tratar, tentativas=2).gerar_json(SISTEMA, "m", ESQUEMA)


def test_cadeia_passa_ao_proximo_modelo_quando_o_atual_esta_indisponivel():
    from rag_sus.provedores import Metadados, ModeloIndisponivel, ProvedorEmCadeia

    class Preso(ProvedorFalso):
        def gerar_json(self, sistema, mensagem, esquema):
            self.chamadas += 1
            raise ModeloIndisponivel(f"{self.modelo} não respondeu")

    a, b = Preso("modelo-a"), ProvedorFalso("modelo-b")
    _, meta = ProvedorEmCadeia([a, b]).gerar_json(SISTEMA, "m", ESQUEMA)
    assert meta.modelo_que_respondeu == "modelo-b" and isinstance(meta, Metadados)
