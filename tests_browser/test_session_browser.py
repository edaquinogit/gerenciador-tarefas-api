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
            page.get_by_role("button", name="Enviar para produção", exact=True).click()
            expect(page.get_by_text("Ordem #1 enviada para produção", exact=False)).to_be_visible()
            page.reload()
            expect(
                page.get_by_role("heading", name="Ordens de produção", exact=True)
            ).to_be_visible()
            expect(page.get_by_role("radio", name="Ordens de produção", exact=True)).to_be_checked()
            assert len(requests.get(API + "/ordens", headers=headers, timeout=5).json()) == 1
            expect(
                page.get_by_role("button", name="#1 — Toalha de ensaio", exact=True)
            ).to_be_visible()
            page.screenshot(path=str(OUTPUT / "desktop.png"), full_page=True, animations="disabled")
            mobile_context = browser.new_context(
                viewport={"width": 390, "height": 844}, is_mobile=True, has_touch=True
            )
            mobile_context.add_cookies(context.cookies())
            mobile = mobile_context.new_page()
            mobile.goto(BASE)
            expect(
                mobile.get_by_role("heading", name="Ordens de produção", exact=True)
            ).to_be_visible(timeout=20000)
            expect(
                mobile.get_by_role("button", name="#1 — Toalha de ensaio", exact=True)
            ).to_be_visible()
            mobile.screenshot(
                path=str(OUTPUT / "mobile.png"), full_page=True, animations="disabled"
            )
            assert mobile.locator("body").evaluate("e => e.scrollWidth <= window.innerWidth + 1")
            pills = mobile.locator('[class*="st-key-filtros_"] [role="radiogroup"]')
            assert pills.evaluate("e => e.scrollWidth > e.clientWidth")
            mobile.get_by_role("button", name="#1 — Toalha de ensaio", exact=True).click()
            expect(
                mobile.get_by_role("dialog").get_by_text("Branca 70x140", exact=True)
            ).to_be_visible()
            mobile.screenshot(path=str(OUTPUT / "mobile-dialog.png"), full_page=True)
            mobile.get_by_role("dialog").get_by_role(
                "button", name="Fechar detalhes", exact=True
            ).click()
            expect(mobile.get_by_role("dialog")).to_have_count(0)
            mobile_context.close()
            # JWT de 1 minuto: navegador deve renovar sem estender a sessão máxima.
            for _ in range(75):
                if (
                    requests.get(API + "/usuarios/me", headers=headers, timeout=5).status_code
                    == 401
                ):
                    break
                time.sleep(1)
            else:
                pytest.fail("Token curto não expirou no período esperado")
            page.get_by_role("button", name="Painel de produção", exact=True).click()
            expect(
                page.get_by_role("heading", name="Painel de produção", exact=True)
            ).to_be_visible()
            renewed = context.request.post(
                API + "/sessoes/restaurar", headers={"Origin": BASE, "X-Session-Request": "1"}
            ).json()
            assert renewed["expires_at"] == saved.json()["expires_at"]
            headers = {"Authorization": f"Bearer {renewed['access_token']}"}
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


def test_ready_notice_privacy_and_password_approval(live_app):
    """Duas caixas independentes; entrega por polling e liberação sem F5."""
    from datetime import datetime, timedelta, timezone
    from uuid import uuid4

    password = secrets.token_urlsafe(18)

    def api(username, secret, method, path, **kwargs):
        login = requests.post(
            API + "/token", data={"username": username, "password": secret}, timeout=10
        )
        login.raise_for_status()
        response = requests.request(
            method,
            API + path,
            headers={"Authorization": "Bearer " + login.json()["access_token"]},
            timeout=10,
            **kwargs,
        )
        response.raise_for_status()
        return response.json()

    for name, sector in [
        ("pedido_a", "SOLICITACAO"),
        ("pedido_b", "SOLICITACAO"),
        ("corte", "PRODUCAO"),
        ("coleta", "COLETA_EMBALAGEM"),
    ]:
        api(
            "ensaio",
            live_app,
            "POST",
            "/admin/funcionarios",
            json={
                "username": name,
                "telefone": "79999990001",
                "password": password,
                "setor": sector,
            },
        )
    order = api(
        "pedido_a",
        password,
        "POST",
        "/ordens",
        json={
            "request_id": str(uuid4()),
            "produto": "Capa urgente",
            "especificacao": "Azul 3 lugares",
            "quantidade": 20,
            "unidade": "pecas",
            "prioridade": "URGENTE",
            "prazo": (datetime.now(timezone.utc) + timedelta(days=1)).isoformat(),
            "observacao": "Lote de teste",
        },
    )
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(executable_path=shutil.which("google-chrome"))
        context = browser.new_context(viewport={"width": 1440, "height": 1000})
        admin_context = browser.new_context(viewport={"width": 1440, "height": 1000})
        page, admin = context.new_page(), admin_context.new_page()
        page.set_default_timeout(20000)
        admin.set_default_timeout(20000)

        def enter(page, name, secret):
            page.goto(BASE)
            page.get_by_label("Usuário", exact=True).fill(name)
            page.get_by_label("Senha", exact=True).fill(secret)
            page.get_by_role("button", name="Entrar", exact=True).click()
            expect(page.get_by_role("button", name="Sair", exact=True)).to_be_visible()

        try:
            enter(page, "pedido_a", password)
            expect(page.get_by_text("Minhas tarefas", exact=True)).to_have_count(0)
            expect(page.get_by_text("Avisos não lidos: 0", exact=True)).to_be_visible()
            for status in ("CORTANDO", "COSTURANDO", "PRONTO"):
                order = api(
                    "corte",
                    password,
                    "PATCH",
                    f"/ordens/{order['id']}/etapa",
                    json={"request_id": str(uuid4()), "versao": order["versao"], "status": status},
                )
            expect(page.get_by_text("Avisos não lidos: 1", exact=True)).to_be_visible(timeout=20000)
            expect(
                page.get_by_text("Disponível para coleta e embalagem.", exact=True)
            ).to_be_visible()
            page.get_by_role("button", name="Abrir ordem", exact=True).click()
            dialog = page.get_by_role("dialog")
            expect(dialog.get_by_text("Azul 3 lugares", exact=True)).to_be_visible()
            expect(dialog.get_by_role("button", name="Marcar lote pronto")).to_have_count(0)
            page.screenshot(
                path=str(OUTPUT / "ready-dialog.png"), full_page=True, animations="disabled"
            )
            dialog.get_by_role("button", name="Fechar detalhes", exact=True).click()
            expect(page.get_by_role("dialog")).to_have_count(0)
            for username in ("pedido_b", "corte", "coleta"):
                assert api(username, password, "GET", "/notificacoes")["total"] == 0
            page.get_by_text("Minha conta", exact=True).click()
            expect(page.get_by_label("Nova senha", exact=True)).to_have_count(0)
            page.get_by_role("button", name="Solicitar alteração de senha", exact=True).click()
            expect(
                page.get_by_text(
                    "Solicitação enviada. Aguardando autorização do administrador.", exact=True
                )
            ).to_be_visible()
            enter(admin, "ensaio", live_app)
            admin.get_by_role("radio", name="Funcionários e setores", exact=True).check()
            admin.get_by_role("button", name="Permitir troca", exact=True).click()
            expect(page.get_by_label("Nova senha", exact=True)).to_be_visible(timeout=20000)
            new_password = secrets.token_urlsafe(18)
            page.get_by_label("Senha atual", exact=True).fill(password)
            page.get_by_label("Nova senha", exact=True).fill(new_password)
            page.get_by_label("Confirme a nova senha", exact=True).fill(new_password)
            page.get_by_role("button", name="Alterar minha senha", exact=True).click()
            expect(page.get_by_role("button", name="Entrar", exact=True)).to_be_visible()
            enter(page, "pedido_a", new_password)
            page.get_by_text("Minha conta", exact=True).click()
            expect(page.get_by_label("Nova senha", exact=True)).to_have_count(0)
            assert (
                api("pedido_a", new_password, "GET", "/usuarios/me/autorizacao-senha")["status"]
                == "UTILIZADA"
            )
        except Exception:
            page.screenshot(path=str(OUTPUT / "rules-failure.png"), full_page=True)
            admin.screenshot(path=str(OUTPUT / "rules-admin-failure.png"), full_page=True)
            raise
        finally:
            browser.close()


def test_sector_pilot_automatic_queue_and_draft(live_app):
    """Solicitar, produzir e coletar pela UI em sessões independentes, sem F5."""
    password = secrets.token_urlsafe(18)
    login = requests.post(
        API + "/token", data={"username": "ensaio", "password": live_app}, timeout=10
    )
    login.raise_for_status()
    headers = {"Authorization": "Bearer " + login.json()["access_token"]}
    for name, sector in [
        ("piloto_pedido", "SOLICITACAO"),
        ("piloto_corte", "PRODUCAO"),
        ("piloto_coleta", "COLETA_EMBALAGEM"),
    ]:
        response = requests.post(
            API + "/admin/funcionarios",
            headers=headers,
            timeout=10,
            json={
                "username": name,
                "telefone": "79999990001",
                "password": password,
                "setor": sector,
            },
        )
        response.raise_for_status()
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(executable_path=shutil.which("google-chrome"))
        pages = {}
        try:
            for role, username, secret in [
                ("pedido", "piloto_pedido", password),
                ("corte", "piloto_corte", password),
                ("coleta", "piloto_coleta", password),
                ("admin", "ensaio", live_app),
            ]:
                page = browser.new_context(viewport={"width": 1440, "height": 1000}).new_page()
                page.set_default_timeout(20000)
                pages[role] = page
                page.goto(BASE)
                page.get_by_label("Usuário", exact=True).fill(username)
                page.get_by_label("Senha", exact=True).fill(secret)
                page.get_by_role("button", name="Entrar", exact=True).click()
                expect(page.get_by_role("button", name="Sair", exact=True)).to_be_visible()
            pedido, corte, coleta, admin = [
                pages[r] for r in ("pedido", "corte", "coleta", "admin")
            ]
            admin.get_by_role("button", name="Painel de produção", exact=True).click()
            # Filtro escolhido deve sobreviver a atualizações recebidas de outro setor.
            corte.locator('[class*="st-key-filtros_"]').get_by_text("Pendente", exact=True).click()
            pedido.get_by_text("Nova ordem", exact=True).click()
            pedido.get_by_label("Produto", exact=True).fill("TESTE piloto entre setores")
            pedido.get_by_label("Produto", exact=True).press("Tab")
            pedido.get_by_label("Especificação (medida, cor ou tecido)", exact=True).fill(
                "Azul 50x70"
            )
            pedido.get_by_label("Especificação (medida, cor ou tecido)", exact=True).press("Tab")
            pedido.get_by_role("button", name="Enviar para produção", exact=True).click()
            card = corte.get_by_role("button", name="TESTE piloto entre setores", exact=False)
            expect(card).to_be_visible(timeout=20000)
            expect(corte.get_by_role("radio", name="Pendente", exact=True)).to_be_checked()
            expect(
                admin.get_by_role("button", name="TESTE piloto entre setores", exact=False)
            ).to_be_visible(timeout=20000)
            # Texto ainda em edição não deve ser perdido pelo polling da fila.
            if not pedido.get_by_label("Produto", exact=True).is_visible():
                pedido.get_by_text("Nova ordem", exact=True).click()
            draft = pedido.get_by_label("Produto", exact=True)
            draft.fill("Rascunho mantido durante produção")
            before = pedido.get_by_text("Última consulta:", exact=False).inner_text()
            card.click()
            dialog = corte.get_by_role("dialog")
            expect(dialog.get_by_text("Azul 50x70", exact=True)).to_be_visible()
            # Aguarda um ciclo observável sem mudar foco, tela ou formulário.
            expect(pedido.get_by_text("Última consulta:", exact=False)).not_to_have_text(
                before, timeout=20000
            )
            expect(draft).to_have_value("Rascunho mantido durante produção")
            expect(dialog).to_be_visible()
            for action in ("Iniciar corte", "Iniciar costura", "Marcar lote pronto"):
                dialog.get_by_role("button", name=action, exact=True).click()
            expect(
                dialog.get_by_text(
                    "Produto disponível para coleta e embalagem — lote completo.", exact=True
                )
            ).to_be_visible()
            expect(pedido.get_by_text("Avisos não lidos: 1", exact=True)).to_be_visible(
                timeout=20000
            )
            expect(
                coleta.get_by_role("button", name="TESTE piloto entre setores", exact=False)
            ).to_be_visible(timeout=20000)
            expect(coleta.get_by_text("Avisos não lidos: 0", exact=True)).to_be_visible()
            coleta.get_by_role("button", name="TESTE piloto entre setores", exact=False).click()
            retirada = coleta.get_by_role("dialog")
            retirada.get_by_text("Confirmo a retirada de todo o lote", exact=True).click()
            retirada.get_by_role("button", name="Confirmar coleta", exact=True).click()
            expect(retirada.get_by_text("Coletada por piloto_coleta", exact=False)).to_be_visible()
            expect(
                pedido.get_by_text(
                    "Lote já coletado. Este aviso permanece no histórico.", exact=True
                )
            ).to_be_visible(timeout=20000)
            expect(draft).to_have_value("Rascunho mantido durante produção")
            # Evidência fica no artefato browser-evidence da execução.
            pedido.screenshot(
                path=str(OUTPUT / "pilot-requester.png"), full_page=True, animations="disabled"
            )
            coleta.screenshot(
                path=str(OUTPUT / "pilot-collected.png"), full_page=True, animations="disabled"
            )
        except Exception:
            for role, page in pages.items():
                page.screenshot(
                    path=str(OUTPUT / f"pilot-failure-{role}.png"),
                    full_page=True,
                    animations="disabled",
                )
            raise
        finally:
            browser.close()


@pytest.mark.parametrize("engine_name", ["chromium", "webkit"])
def test_mobile_cookie_recovery_and_layout(live_app, engine_name):
    """Cookie inválido, falha temporária, F5 e detalhes em telas pequenas."""
    with sync_playwright() as playwright:
        engine = getattr(playwright, engine_name)
        options = (
            {"executable_path": shutil.which("google-chrome")} if engine_name == "chromium" else {}
        )
        browser = engine.launch(**options)
        context = browser.new_context(
            viewport={"width": 390, "height": 844}, is_mobile=True, has_touch=True
        )
        context.add_cookies(
            [
                {
                    "name": "gerenciador_sessao",
                    "value": "invalido",
                    "domain": "127.0.0.1",
                    "path": "/sessoes",
                    "httpOnly": True,
                    "sameSite": "Strict",
                },
                {"name": "preferencia_teste", "value": "preservar", "url": BASE},
            ]
        )
        # A primeira consulta falha; a próxima deve recuperar sozinha em 15 segundos.
        context.route(
            "**/sessoes/restaurar",
            lambda route: route.fulfill(
                status=503,
                content_type="application/json",
                headers={
                    "Access-Control-Allow-Origin": BASE,
                    "Access-Control-Allow-Credentials": "true",
                },
                body='{"detail":"API temporariamente indisponível"}',
            ),
            times=1,
        )
        page = context.new_page()
        page.set_default_timeout(25000)
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        try:
            page.goto(BASE)
            warning = page.get_by_text(
                "Não foi possível recuperar a sessão no navegador.", exact=False
            )
            expect(warning).to_be_visible(timeout=25000)
            expect(warning).to_have_count(0, timeout=30000)
            expect(page.get_by_role("button", name="Entrar", exact=True)).to_be_visible()
            cookies = {c["name"]: c["value"] for c in context.cookies()}
            assert "gerenciador_sessao" not in cookies
            assert cookies["preferencia_teste"] == "preservar"
            page.get_by_label("Usuário", exact=True).fill("ensaio")
            page.get_by_label("Senha", exact=True).fill(live_app)
            page.get_by_role("button", name="Entrar", exact=True).click()
            expect(
                page.get_by_role("button", name="Painel de produção", exact=True)
            ).to_be_visible()
            # Aguarda a vinculação antes de recarregar a página.
            for _ in range(100):
                if any(c["name"] == "gerenciador_sessao" for c in context.cookies()):
                    break
                page.wait_for_timeout(100)
            else:
                pytest.fail("Cookie não foi vinculado")
            page.reload()
            page.get_by_role("button", name="Painel de produção", exact=True).click()
            card = page.get_by_role("button", name="#1 — Toalha de ensaio", exact=True)
            expect(card).to_be_visible()
            for width in (360, 390, 768, 1440):
                page.set_viewport_size({"width": width, "height": 900})
                expect(card).to_be_visible()
                assert page.locator("body").evaluate("e => e.scrollWidth <= window.innerWidth + 1")
                card.click()
                dialog = page.get_by_role("dialog")
                expect(dialog.get_by_text("Branca 70x140", exact=True)).to_be_visible()
                box = dialog.bounding_box()
                assert box and box["x"] >= 0 and box["x"] + box["width"] <= width + 1
                assert dialog.evaluate("e => e.scrollWidth <= e.clientWidth + 1")
                if width == 390:
                    page.screenshot(
                        path=str(OUTPUT / f"audit-{engine_name}-mobile.png"), animations="disabled"
                    )
                dialog.get_by_role("button", name="Fechar detalhes", exact=True).click()
                expect(dialog).to_have_count(0)
            page.set_viewport_size({"width": 390, "height": 844})
            toggle = page.get_by_test_id("stExpandSidebarButton")
            page.wait_for_function("window.innerWidth < 640")
            sidebar = page.get_by_test_id("stSidebar")
            if sidebar.get_attribute("aria-expanded") == "false":
                expect(toggle).to_be_visible(timeout=15000)
                toggle.click()
            page.get_by_role("button", name="Sair", exact=True).click()
            expect(page.get_by_role("button", name="Entrar", exact=True)).to_be_visible()
            page.reload()
            expect(page.get_by_role("button", name="Entrar", exact=True)).to_be_visible()
            assert not any(c["name"] == "gerenciador_sessao" for c in context.cookies())
            assert not errors, errors
        except Exception:
            page.screenshot(
                path=str(OUTPUT / f"audit-{engine_name}-failure.png"), animations="disabled"
            )
            raise
        finally:
            browser.close()
