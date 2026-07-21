#!/usr/bin/env python3
"""
Busca as cotações de fechamento do dia para todos os tickers listados em
tickers.txt usando a API da brapi.dev, e acrescenta uma linha por ativo
no arquivo automation/data/precos_historico.csv.

Uso:
    BRAPI_TOKEN=xxxx python fetch_precos.py

Este script roda diariamente via GitHub Actions (ver
.github/workflows/cotacoes-diarias.yml), que tem acesso livre à internet
(diferente do sandbox usado para desenvolver este projeto).
"""
import csv
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

BASE_DIR = Path(__file__).resolve().parent
TICKERS_FILE = BASE_DIR / "tickers.txt"
DATA_DIR = BASE_DIR / "data"
OUTPUT_FILE = DATA_DIR / "precos_historico.csv"

BRAPI_TOKEN = os.environ.get("BRAPI_TOKEN", "").strip()
BRAPI_URL = "https://brapi.dev/api/v2/stocks/quote"

# Projeto Supabase (financas-jose). A URL não é sensível; a chave sim.
SUPABASE_URL = "https://parrnhobkfvkfolvxnqo.supabase.co"
SUPABASE_SERVICE_KEY = os.environ.get("SUPABASE_SERVICE_KEY", "").strip()

# Quantos tickers pedir por requisição. O plano gratuito não permite lote
# (retorna 400 se symbols tiver mais de 1 ticker), então 1 por chamada.
BATCH_SIZE = 1


def carregar_tickers() -> list[str]:
    tickers = []
    with open(TICKERS_FILE, encoding="utf-8") as f:
        for linha in f:
            linha = linha.strip()
            if not linha or linha.startswith("#"):
                continue
            tickers.append(linha.upper())
    return tickers


def buscar_lote(tickers: list[str]) -> dict:
    """Busca cotação de um lote de tickers. Retorna dict ticker -> preco (ou None se falhar)."""
    params = {"symbols": ",".join(tickers)}
    headers = {}
    if BRAPI_TOKEN:
        headers["Authorization"] = f"Bearer {BRAPI_TOKEN}"

    resultado = {t: None for t in tickers}
    try:
        resp = requests.get(BRAPI_URL, params=params, headers=headers, timeout=20)
        if not resp.ok:
            print(
                f"[AVISO] Falha ao buscar {tickers}: HTTP {resp.status_code} - {resp.text[:300]}",
                file=sys.stderr,
            )
            return resultado
        payload = resp.json()
        for item in payload.get("results", []):
            symbol = item.get("symbol") or item.get("requestedSymbol")
            preco = (item.get("data") or {}).get("regularMarketPrice")
            if symbol:
                resultado[symbol] = preco
    except Exception as exc:  # noqa: BLE001
        print(f"[AVISO] Falha ao buscar {tickers}: {exc}", file=sys.stderr)
    return resultado


def sincronizar_supabase(linhas: list) -> None:
    """Envia as cotações do dia para eqi_financas.precos_diarios no Supabase
    (upsert por ticker+data). Não interrompe o script se falhar — o CSV no
    repositório continua sendo a fonte de verdade mesmo se isso der erro."""
    if not SUPABASE_SERVICE_KEY:
        print(
            "[AVISO] SUPABASE_SERVICE_KEY não configurada — pulando sincronização "
            "com o Supabase (o CSV local ainda foi gravado normalmente).",
            file=sys.stderr,
        )
        return
    if not linhas:
        return

    payload = [
        {
            "ticker": ticker,
            "data": data,
            "preco_fechamento": float(preco),
            "capturado_em": capturado_em,
        }
        for data, ticker, preco, capturado_em in linhas
    ]

    try:
        resp = requests.post(
            f"{SUPABASE_URL}/rest/v1/precos_diarios",
            json=payload,
            headers={
                "apikey": SUPABASE_SERVICE_KEY,
                "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
                "Content-Type": "application/json",
                "Content-Profile": "eqi_financas",
                "Prefer": "resolution=merge-duplicates,return=minimal",
            },
            timeout=30,
        )
        if not resp.ok:
            print(
                f"[AVISO] Falha ao sincronizar com Supabase: HTTP {resp.status_code} - {resp.text[:300]}",
                file=sys.stderr,
            )
        else:
            print(f"OK: {len(payload)} cotações sincronizadas com o Supabase.")
    except Exception as exc:  # noqa: BLE001
        print(f"[AVISO] Falha ao sincronizar com Supabase: {exc}", file=sys.stderr)


def main():
    if not BRAPI_TOKEN:
        print(
            "[ERRO] Variável de ambiente BRAPI_TOKEN não definida. "
            "Configure o secret BRAPI_TOKEN no repositório do GitHub.",
            file=sys.stderr,
        )
        sys.exit(1)

    tickers = carregar_tickers()
    if not tickers:
        print("[ERRO] Nenhum ticker encontrado em tickers.txt", file=sys.stderr)
        sys.exit(1)

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    arquivo_novo = not OUTPUT_FILE.exists()

    hoje = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    capturado_em = datetime.now(timezone.utc).isoformat()

    linhas = []
    falhas = []
    for i in range(0, len(tickers), BATCH_SIZE):
        lote = tickers[i : i + BATCH_SIZE]
        precos = buscar_lote(lote)
        for ticker, preco in precos.items():
            if preco is None:
                falhas.append(ticker)
            else:
                linhas.append([hoje, ticker, preco, capturado_em])
        time.sleep(1)  # gentil com a API, sem necessidade de correr

    with open(OUTPUT_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if arquivo_novo:
            writer.writerow(["data", "ticker", "preco_fechamento", "capturado_em_utc"])
        writer.writerows(linhas)

    print(f"OK: {len(linhas)} cotações gravadas para {hoje}.")
    if falhas:
        print(f"[AVISO] {len(falhas)} tickers sem cotação hoje: {', '.join(falhas)}")

    sincronizar_supabase(linhas)


if __name__ == "__main__":
    main()
