# -*- coding: utf-8 -*-
"""Testes da leitura de parametros.toml."""

from rag_sus import config


def test_le_os_modelos_reserva_do_juiz_na_ordem(tmp_path):
    texto = (config.PARAMETROS).read_text(encoding="utf-8")
    p = config.carregar_parametros(config.PARAMETROS)
    assert p.reservas_juiz and p.modelo_juiz not in p.reservas_juiz
    # o respondedor não entra na cadeia do Juiz: a cota dele fica só para as respostas
    assert p.modelo_respondedor not in (p.modelo_juiz, *p.reservas_juiz)

    sem_reservas = tmp_path / "parametros.toml"
    sem_reservas.write_text(texto.replace("reservas =", "# reservas ="), encoding="utf-8")
    assert config.carregar_parametros(sem_reservas).reservas_juiz == ()
