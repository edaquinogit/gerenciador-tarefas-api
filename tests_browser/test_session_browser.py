"""Fluxos reais de navegador; rodar separadamente da suíte AppTest.

python -m pip install playwright==1.58.0
python -m playwright install chromium
python -m pytest -q tests_browser
CI usa o Chrome já instalado no runner. Dados e senhas são exclusivos do teste.
"""

import os
import secrets
import shutil
import subprocess
import sys
import time
from pathlib import Path

import pytest
import requests
from playwright.sync_api import expect, sync_playwright
from sqlmodel import Session

from backend.core.security import get_password_hash
from backend.database.connection import build_engine
from backend.models import Usuario

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "test-results"
BASE = "http://127.0.0.1:8501"
API = "http://127.0.0.1:8000"


@pytest.fixture(scope="module")
def live_app(tmp_path_factory):
    directory = tmp_path_factory.mktemp("browser")
    env = {
        **os.environ,
        "SECRET_KEY": secrets.token_urlsafe(48),
        "DATABASE_URL": f"sqlite:///{directory / 'test.db'}",
        "API_URL": API,
        "PUBLIC_API_URL": API,
        "BROWSER_ORIGINS": f'["{BASE}"]',
        "SESSION_COOKIE_SECURE": "false",
        "ACCESS_TOKEN_EXPIRE_MINUTES": "1",
    }
    subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"], cwd=ROOT, env=env, check=True
    )
    engine = build_engine(env["DATABASE_URL"])
    password = secrets.token_urlsafe(18)
    with Session(engine) as session:
        session.add(
            Usuario(username="ensaio", password_hash=get_password_hash(password), perfil="ADMIN")
        )
        session.commit()
    engine.dispose()
    OUTPUT.mkdir(exist_ok=True)
    processes, files = [], []
    try:
        for name, args, health in [
            (
                "api",
                ["uvicorn", "backend.main:create_app", "--factory", "--port", "8000"],
                API + "/health",
            ),
            (
                "streamlit",
                [
                    "streamlit",
                    "run",
                    "frontend/app.py",
                    "--server.port",
                    "8501",
                    "--server.headless",
                    "true",
                ],
                BASE + "/_stcore/health",
            ),
        ]:
            log = (OUTPUT / f"{name}.log").open("w")
            files.append(log)
            process = subprocess.Popen(
                [sys.executable, "-m", *args], cwd=ROOT, env=env, stdout=log, stderr=log
            )
            processes.append(process)
            for _ in range(100):
                if process.poll() is not None:
                    raise RuntimeError(f"{name} não iniciou; confira test-results/{name}.log")
                try:
                    if requests.get(health, timeout=1).ok:
                        break
                except requests.RequestException:
                    pass
                time.sleep(0.2)
            else:
                raise RuntimeError(f"Tempo limite ao iniciar {name}")
        yield password
    finally:
        for process in reversed(processes):
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
        for log in files:
            log.close()


def test_f5_draft_logout_and_small_screen(live_app):
    with sync_playwright() as playwright:
        executable = shutil.which("google-chrome")
        browser = playwright.chromium.launch(executable_path=executable)
        context = browser.new_context(viewport={"width": 1440, "height": 1000})
        page = context.new_page()
        page.set_default_timeout(20000)
        try:
            page.goto(BASE)
            page.get_by_label("Usuário", exact=True).fill("ensaio")
            page.get_by_label("Senha", exact=True).fill(live_app)
            page.get_by_role("button", name="Entrar", exact=True).click()
            expect(
                page.get_by_role("heading", name="Funcionários e setores", exact=True)
            ).to_be_visible()
            for _ in range(50):
                cookies = [c for c in context.cookies() if c["name"] == "gerenciador_sessao"]
                if cookies:
                    break
                time.sleep(0.1)
            assert cookies and cookies[0]["httpOnly"] and cookies[0]["sameSite"] == "Strict"
            page.reload()
            expect(page.get_by_role("button", name="Sair", exact=True)).to_be_visible()
            page.get_by_text("Ordens de produção", exact=True).click()
            page.get_by_text("Nova ordem", exact=True).click()
            page.get_by_label("Produto", exact=True).fill("Toalha de ensaio")
            page.get_by_label("Produto", exact=True).press("Tab")
            page.get_by_label("Especificação (medida, cor ou tecido)", exact=True).fill(
                "Branca 70x140"
            )
            page.get_by_label("Especificação (medida, cor ou tecido)", exact=True).press("Tab")
            # Aguardar salvamento confirmado pelo backend, sem depender de pausa fixa.
            saved = context.request.post(
                API + "/sessoes/restaurar", headers={"Origin": BASE, "X-Session-Request": "1"}
            )
            token = saved.json()["access_token"]
            headers = {"Authorization": f"Bearer {token}"}
            for _ in range(50):
                state = requests.get(API + "/sessoes/estado", headers=headers, timeout=5).json()[
                    "state"
                ]
                if state.get("op_especificacao") == "Branca 70x140":
                    break
                time.sleep(0.1)
            assert state["op_produto"] == "Toalha de ensaio"
            assert state["op_especificacao"] == "Branca 70x140"
            page.reload()
            expect(
                page.get_by_role("heading", name="Ordens de produção", exact=True)
            ).to_be_visible()
            page.get_by_text("Nova ordem", exact=True).click()
            expect(page.get_by_label("Produto", exact=True)).to_have_value("Toalha de ensaio")
            expect(
                page.get_by_label("Especificação (medida, cor ou tecido)", exact=True)
            ).to_have_value("Branca 70x140")
            page.screenshot(path=str(OUTPUT / "desktop.png"), full_page=True)
            page.get_by_role("button", name="Enviar para produção", exact=True).click()
            expect(page.get_by_text("Ordem #1 enviada para produção", exact=False)).to_be_visible()
            page.reload()
            expect(
                page.get_by_role("heading", name="Ordens de produção", exact=True)
            ).to_be_visible()
            assert len(requests.get(API + "/ordens", headers=headers, timeout=5).json()) == 1
            page.set_viewport_size({"width": 390, "height": 844})
            page.screenshot(path=str(OUTPUT / "mobile.png"), full_page=True)
            assert page.locator("body").evaluate("e => e.scrollWidth <= window.innerWidth + 1")
            page.set_viewport_size({"width": 1440, "height": 1000})
            page.get_by_role("button", name="Sair", exact=True).click()
            expect(page.get_by_role("button", name="Entrar", exact=True)).to_be_visible()
            assert requests.get(API + "/usuarios/me", headers=headers, timeout=5).status_code == 401
            page.reload()
            expect(page.get_by_role("button", name="Entrar", exact=True)).to_be_visible()
            expect(page.get_by_role("button", name="Sair", exact=True)).to_have_count(0)
        except Exception:
            page.screenshot(path=str(OUTPUT / "failure.png"), full_page=True)
            (OUTPUT / "page.html").write_text(page.content())
            raise
        finally:
            browser.close()
