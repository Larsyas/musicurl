import re
import sys
from pathlib import Path
from urllib.parse import quote

from playwright.sync_api import TimeoutError as PlaywrightTimeout
from playwright.sync_api import sync_playwright

# Caminhos comuns do Brave no Windows
BRAVE_PATHS = [
    r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe",
    r"C:\Program Files (x86)\BraveSoftware\Brave-Browser\Application\brave.exe",
    str(Path.home() / r"AppData\Local\BraveSoftware\Brave-Browser\Application\brave.exe"),
]

SELETOR_TOP_RESULT = '[data-testid="top-result-card"] a[href*="/track/"]'
SELETOR_QUALQUER_FAIXA = 'a[href*="/track/"]'


def achar_brave() -> str:
    for caminho in BRAVE_PATHS:
        if Path(caminho).exists():
            return caminho
    sys.exit("Brave não encontrado. Ajuste BRAVE_PATHS com o caminho do brave.exe.")


def montar_url_busca(termo: str) -> str:
    return "https://open.spotify.com/search/" + quote(termo.strip(), safe="")


def href_para_url_faixa(href: str) -> str | None:
    """Converte '/intl-pt/track/3Ljj...' em 'https://open.spotify.com/track/3Ljj...'."""
    m = re.search(r"/track/([A-Za-z0-9]{22})", href)
    return f"https://open.spotify.com/track/{m.group(1)}" if m else None


def pegar_href_faixa(page) -> str | None:
    """Tenta o card de resultado principal; se não for uma faixa, usa a primeira faixa da página."""
    for seletor in (SELETOR_TOP_RESULT, SELETOR_QUALQUER_FAIXA):
        try:
            link = page.locator(seletor).first
            link.wait_for(state="attached", timeout=10_000)
            return link.get_attribute("href")
        except PlaywrightTimeout:
            continue
    return None


def main() -> None:
    termo = " ".join(sys.argv[1:]).strip() or input("Nome da música (e artista): ").strip()
    if not termo:
        sys.exit("Você precisa digitar algo.")

    url_busca = montar_url_busca(termo)
    print("Acessando:", url_busca)

    with sync_playwright() as pw:
        browser = pw.chromium.launch(
            executable_path=achar_brave(),
            headless=True,
        )
        context = browser.new_context(locale="pt-BR")
        page = context.new_page()

        # --- sua lógica começa aqui ---
        page.goto(url_busca, wait_until="domcontentloaded")

        href = pegar_href_faixa(page)          # ex.: /intl-pt/track/3LjjHWnqa1j4ZFcK6tcCxd
        url_musica = href_para_url_faixa(href) if href else None

        if url_musica:
            print("href bruto :", href)
            print("URL da faixa:", url_musica)
        else:
            print("Não encontrei nenhuma faixa nos resultados.")
        # ------------------------------

        context.close()
        browser.close()


if __name__ == "__main__":
    main()