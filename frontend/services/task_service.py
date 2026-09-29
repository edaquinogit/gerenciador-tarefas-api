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
                401: "Credenciais inválidas ou sessão expirada. Entre novamente.",
                403: "Acesso não permitido. Solicite acesso ao responsável.",
                404: "Registro não encontrado. Atualize a página.",
                409: "Usuário ou e-mail já cadastrado.",
                422: "Dados inválidos. Confira os campos informados.",
            }
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
