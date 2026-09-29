#!/usr/bin/env python3
"""Check de comportamento no browser: a rolagem da página Legal obedece o usuário.

O bug (v3.5.3) era um `setInterval(400ms) × 12` reatribuindo `scrollTop=0` sem
olhar se já havia alguém rolando: quem abria a Legal recebia uma puxada de volta
ao topo a cada 400ms — uma dente-de-serra de ~180px — que só normalizava quando
o intervalo morria. **Duas rodadas de teste automatizado disseram que não havia
bug**, porque as duas mediram no lugar errado. Este script existe para não
depender de alguém lembrar disso.

As quatro regras que o teste aprendeu (e que estão no AGENTS.md):

1. O observador tem que estar no lugar certo em relação ao que se observa. Aqui
   isso virou "rolar com gesto de verdade": a fix libera o timer ao ver
   `wheel`/`touchstart`/`keydown`/`mousedown`, e **atribuir `scrollTop` por JS
   não dispara nenhum deles** — um robô que seta `scrollTop` mede um usuário que
   não existe e acusa uma puxada que pessoa nenhuma sofre.
2. A medição nunca encerra no primeiro acerto — grava a janela inteira.
3. Julga a FORMA, não o ponto: o defeito era um padrão no tempo, invisível para
   asserção de valor único. Por isso pares `[tempo, scrollTop]`.
4. "Não há bug" exige série temporal, e série vazia não é "nenhuma jogada" —
   é medição que não aconteceu. Por isso o piso de amostras lá embaixo.

Detalhes do app que custaram rodadas e não são óbvios:

- O alvo é o **botão** `⚖️ Termos & Privacidade` do menu, que navega por
  `st.switch_page` — é esse caminho que chama o `_rolar_topo`.
- Existe também um `<a href="/legal">` no rodapé, com texto quase igual. Ele faz
  full page load, caminho em que o `_rolar_topo` **nem roda**, e que em servidor
  frio é redirecionado para `/`. Clicar no elemento errado dá verde falso.
- A rota inicial é `/inicio`, não `/`. E `/?pag=legal` (o deep link externo)
  depende de `st.query_params` sobreviver ao cold-start, o que não se reproduz
  no servidor local — por isso o script usa o botão.

Fora do `pytest` de propósito: precisa de browser de verdade e de um Streamlit
no ar, então é lento e mais propenso a oscilar que um teste unitário — e o
pytest roda a cada push. Este roda sob demanda, antes de release. A trava
estrutural do JS continua nos 2 testes de `test_ui_comum.py`.

Uso (com o app já no ar):
    .venv/bin/streamlit run home.py --server.port 8501 &
    .venv/bin/python scripts/checar_scroll_legal.py
    .venv/bin/python scripts/checar_scroll_legal.py --url http://127.0.0.1:8502

Sai 0 se passar, 1 se falhar (ou se o Playwright não estiver instalado).
"""

from __future__ import annotations

import argparse
import sys
import time

# Browser de teste precisa caber numa janela de notebook: em 800x600 o conteúdo
# da Legal cabe inteiro e o defeito some sozinho, produzindo um falso verde.
VIEWPORT_PADRAO = (1366, 768)

# Variação de scrollTop entre duas amostras que conta como "jogada para o topo".
# O gesto anda 45px por passo, então um reset para 0 aparece como queda de ~180px.
QUEDA_MINIMA_PX = 30

# Piso de amostras: abaixo disso a medição não vale e o resultado é
# INCONCLUSIVO, não passe. Sem este piso, uma série vazia (sonda que não rodou,
# seletor errado, app que não carregou) passaria como "nenhuma jogada".
MINIMO_AMOSTRAS = 20

# Janela em que o próprio mecanismo se arma: o iframe do `components.html`
# monta alguns décimos depois, e o `sobe()` inicial dele pode rodar antes de o
# listener de gesto existir, causando UMA jogada se a página for rolada nesse
# instante. Isso é inerente à correção e imperceptível na prática (ninguém rola
# 300ms depois de clicar), então não reprova — mas é reportado à parte, para não
# esconder. O defeito de verdade era a puxada SUSTENTADA, e ela continua sendo
# pega com folga: das 14 jogadas do bug, só ~1 cai nesta janela.
JANELA_ARMADO_MS = 1000

# Rolar com gesto de verdade. `page.mouse.wheel` emite um WheelEvent nativo, que
# é o que a página escuta para liberar o timer — e que um usuário produz e um
# `element.scrollTop = x` não.
PASSO_PX = 45
INTERVALO_PX_MS = 80

CLICAR_TERMOS_JS = """
() => {
  // Só botões: o <a href="/legal"> do rodapé tem texto quase igual e é o caminho
  // errado (full reload, sem _rolar_topo, e redireciona para / em servidor frio).
  const alvo = [...document.querySelectorAll('button')]
    .find((e) => e.innerText.trim().includes('Termos'));
  if (!alvo) return false;
  alvo.click();
  return true;
}
"""

LER_SCROLL_JS = """
() => {
  const e = document.querySelector('[data-testid="stMain"]');
  return e ? e.scrollTop : -1;
}
"""


def _esperar_a_legal(pagina) -> bool:
    """Duas abas = a página Legal renderizou (padrão do st.tabs)."""
    try:
        pagina.wait_for_function(
            "() => document.querySelectorAll('[role=\"tab\"]').length >= 2",
            timeout=30_000,
        )
        return True
    except Exception:
        return False


def _rolar_com_gesto(pagina, segundos: float) -> list[list[int]]:
    """Rola com WheelEvent real e devolve a série [tempo_ms, scrollTop]."""
    # O mouse precisa estar sobre a área de conteúdo para o wheel rolar o
    # container certo (não a barra lateral).
    pagina.mouse.move(VIEWPORT_PADRAO[0] / 2, VIEWPORT_PADRAO[1] / 2)
    inicio = time.monotonic()
    serie: list[list[int]] = []
    while (time.monotonic() - inicio) < segundos:
        pagina.mouse.wheel(0, PASSO_PX)
        t_ms = int((time.monotonic() - inicio) * 1000)
        serie.append([t_ms, pagina.evaluate(LER_SCROLL_JS)])
        pagina.wait_for_timeout(INTERVALO_PX_MS)
    return serie


def _achar_quedas(serie: list[list[int]]) -> list[list[int]]:
    """[tempo, valor_de, valor_para] para cada queda acima do limiar."""
    quedas = []
    anterior = None
    for t, v in serie:
        if anterior is not None and v < anterior[1] - QUEDA_MINIMA_PX:
            quedas.append([t, anterior[1], v])
        anterior = [t, v]
    return quedas


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--url", default="http://127.0.0.1:8501")
    ap.add_argument("--segundos", type=float, default=10.0)
    args = ap.parse_args()

    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("Playwright não está instalado. Instale à parte (fora dos requirements):")
        print("    .venv/bin/pip install playwright && .venv/bin/playwright install chromium")
        return 1

    with sync_playwright() as p:
        navegador = p.chromium.launch(args=["--no-sandbox"])
        try:
            pagina = navegador.new_page(
                viewport={"width": VIEWPORT_PADRAO[0], "height": VIEWPORT_PADRAO[1]}
            )
            pagina.goto(f"{args.url}/inicio", wait_until="domcontentloaded")

            try:
                pagina.wait_for_function(
                    "() => [...document.querySelectorAll('button')]"
                    ".some((e) => e.innerText.includes('Termos'))",
                    timeout=45_000,
                )
            except Exception:
                print("FALHOU: o menu não carregou (app no ar? porta certa?).")
                return 1

            if not pagina.evaluate(CLICAR_TERMOS_JS):
                print("FALHOU: não achei o botão de Termos no menu.")
                return 1

            if not _esperar_a_legal(pagina):
                print("FALHOU: a página Legal não renderizou após o clique.")
                print(f"        path final: {pagina.url}")
                return 1

            serie = _rolar_com_gesto(pagina, args.segundos)
        finally:
            navegador.close()

    quedas = _achar_quedas(serie)
    cedo = [q for q in quedas if q[0] < JANELA_ARMADO_MS]
    tardias = [q for q in quedas if q[0] >= JANELA_ARMADO_MS]
    maximo = max((v for _, v in serie), default=-1)
    print()
    print(
        f"Check da rolagem — viewport {VIEWPORT_PADRAO[0]}x{VIEWPORT_PADRAO[1]}, "
        f"{args.segundos:.0f}s de rolagem com gesto real na Legal"
    )
    print(f"  amostras: {len(serie)}   scroll máximo alcançado: {maximo}px")
    print()
    if len(serie) < MINIMO_AMOSTRAS:
        print(
            f"  INCONCLUSIVO: só {len(serie)} amostras (mínimo {MINIMO_AMOSTRAS}). "
            "A sonda não mediu — isto NÃO é um passe."
        )
        return 1
    if tardias:
        print("  quando    de      para     <- jogada de volta ao topo")
        for t, de, para in tardias[:12]:
            print(f"  {t:6d}ms  {de:5d}  ->  {para:4d}")
        if len(tardias) > 12:
            print(f"  ... e mais {len(tardias) - 12}")
        print()
        n = len(tardias)
        print(f"  FALHOU: {n} {'jogada' if n == 1 else 'jogadas'} para o topo durante a rolagem.")
        return 1

    if cedo:
        for t, de, para in cedo:
            print(
                f"  aviso: 1 toque de {de}px -> {para}px em {t}ms, dentro da "
                f"janela de armamento (< {JANELA_ARMADO_MS} ms) — esperado."
            )
    print("  OK: nenhuma jogada para o topo depois da janela de armamento —")
    print("      a rolagem do usuário não foi interrompida.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
