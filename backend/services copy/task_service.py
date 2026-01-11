import requests
import os
import streamlit as st

API_URL = st.secrets.get("API_URL") or os.getenv("API_URL")

class TaskService:
    @staticmethod
    def login(username, password):
        res = requests.post(f"{API_URL}/token", data={
            "username": username,
            "password": password
        })
        return res.json() if res.status_code == 200 else None

    @staticmethod
    def listar(token):
        headers = {"Authorization": f"Bearer {token}"}
        res = requests.get(f"{API_URL}/tarefas", headers=headers)
        return res.json() if res.status_code == 200 else []

    @staticmethod
    def concluir(tarefa_id, token):
        headers = {"Authorization": f"Bearer {token}"}
        return requests.patch(
            f"{API_URL}/tarefas/{tarefa_id}/concluir",
            headers=headers
        ).status_code == 200

    @staticmethod
    def deletar(tarefa_id, token):
        headers = {"Authorization": f"Bearer {token}"}
        return requests.delete(
            f"{API_URL}/tarefas/{tarefa_id}",
            headers=headers
        ).status_code == 200
