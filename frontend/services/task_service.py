import requests


class APIError(Exception):
    def __init__(self, message: str, status_code: int | None = None):
        super().__init__(message)
        self.status_code = status_code


class TaskService:
    def __init__(self, api_url: str):
        self.api_url = api_url.rstrip("/")

    def _request(self, method: str, path: str, token: str | None = None, **kwargs):
        headers = {"Authorization": f"Bearer {token}"} if token else {}
        try:
            response = requests.request(
                method, f"{self.api_url}{path}", headers=headers, timeout=10, **kwargs
            )
        except requests.RequestException:
            raise APIError(
                "Não foi possível conectar à API. Verifique a conexão e tente novamente."
            ) from None
        if response.status_code >= 400:
            messages = {
                400: "Senha atual incorreta ou dados inválidos. Confira e tente novamente.",
                401: "Credenciais inválidas ou sessão expirada. Entre novamente.",
                403: "Acesso não permitido. Solicite acesso ao responsável.",
                404: "Registro não encontrado. Atualize a página.",
                409: "Usuário ou e-mail já cadastrado.",
                422: "Dados inválidos. Confira os campos informados.",
            }
            if path.startswith("/ordens") and response.status_code == 409:
                try:
                    detail = response.json().get("detail")
                    if isinstance(detail, str):
                        messages[409] = detail
                except ValueError:
                    pass
            raise APIError(
                messages.get(
                    response.status_code,
                    "A API não conseguiu concluir a operação. Tente novamente.",
                ),
                response.status_code,
            )
        try:
            return response.json()
        except ValueError:
            raise APIError("Resposta inválida da API. Tente novamente.") from None

    def login(self, username: str, password: str):
        return self._request("POST", "/token", data={"username": username, "password": password})

    def listar(self, token: str):
        return self._request("GET", "/tarefas", token)

    def criar(self, titulo: str, prioridade: str, token: str):
        return self._request(
            "POST", "/tarefas", token, json={"titulo": titulo, "prioridade": prioridade}
        )

    def concluir(self, tarefa_id: int, token: str):
        return self._request("PATCH", f"/tarefas/{tarefa_id}/concluir", token)

    def deletar(self, tarefa_id: int, token: str):
        return self._request("DELETE", f"/tarefas/{tarefa_id}", token)

    def me(self, token: str):
        return self._request("GET", "/usuarios/me", token)

    def setores(self, token: str):
        return self._request("GET", "/setores", token)

    def funcionarios(self, token: str):
        return self._request("GET", "/admin/funcionarios", token)

    def criar_funcionario(self, data: dict, token: str):
        return self._request("POST", "/admin/funcionarios", token, json=data)

    def atualizar_funcionario(self, usuario_id: int, data: dict, token: str):
        return self._request("PATCH", f"/admin/funcionarios/{usuario_id}", token, json=data)

    def redefinir_senha(self, usuario_id: int, password: str, token: str):
        return self._request(
            "POST", f"/admin/funcionarios/{usuario_id}/senha", token, json={"password": password}
        )

    def minha_senha(self, current_password: str, password: str, token: str):
        return self._request(
            "POST",
            "/usuarios/me/senha",
            token,
            json={"current_password": current_password, "password": password},
        )

    def ordens(self, token: str, **params):
        return self._request("GET", "/ordens", token, params=params)

    def criar_ordem(self, data: dict, token: str):
        return self._request("POST", "/ordens", token, json=data)

    def historico_ordem(self, ident: int, token: str):
        return self._request("GET", f"/ordens/{ident}/historico", token)

    def etapa_ordem(self, ident: int, data: dict, token: str):
        return self._request("PATCH", f"/ordens/{ident}/etapa", token, json=data)

    def coletar_ordem(self, ident: int, data: dict, token: str):
        return self._request("POST", f"/ordens/{ident}/coleta", token, json=data)

    def cancelar_ordem(self, ident: int, data: dict, token: str):
        return self._request("POST", f"/ordens/{ident}/cancelamento", token, json=data)

    def notificacoes(self, token: str, **params):
        return self._request("GET", "/notificacoes", token, params=params)

    def ler_notificacao(self, ident: int, token: str):
        return self._request("PATCH", f"/notificacoes/{ident}/lida", token)
