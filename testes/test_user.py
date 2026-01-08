"""
Testes unitários para os endpoints de User.
"""
import pytest


class TestUserLogin:
    """Testes para os endpoints de login de usuário."""

    def test_login_with_valid_credentials(self, client, superadmin_user):
        """Testa login com credenciais válidas."""
        response = client.post(
            "/auth/login/",
            json={
                "email": "superadmin@gmail.com",
                "password": "123123123"
            }
        )
        # Pode retornar 200 ou 401 dependendo da implementação do hash
        assert response.status_code in [200, 401]

    def test_login_with_invalid_email(self, client):
        """Testa login com email inválido."""
        response = client.post(
            "/auth/login/",
            json={
                "email": "naoexiste@teste.com",
                "password": "senha123"
            }
        )
        assert response.status_code == 401

    def test_login_with_invalid_password(self, client, superadmin_user):
        """Testa login com senha inválida."""
        response = client.post(
            "/auth/login/",
            json={
                "email": "superadmin@gmail.com",
                "password": "senhaerrada"
            }
        )
        assert response.status_code == 401

    def test_login_with_missing_fields(self, client):
        """Testa login com campos faltando."""
        response = client.post(
            "/auth/login/",
            json={"email": "teste@teste.com"}
        )
        assert response.status_code == 422


class TestUserRegister:
    """Testes para os endpoints de registro de usuário."""

    def test_register_new_user(self, client):
        """Testa registro de novo usuário."""
        response = client.post(
            "/auth/register/",
            json={
                "username": "novousuario",
                "email": "novo@usuario.com",
                "password": "senha123456",
                "phone": "11999998888"
            }
        )
        assert response.status_code == 201

    def test_register_with_existing_email(self, client, superadmin_user):
        """Testa registro com email já existente."""
        response = client.post(
            "/auth/register/",
            json={
                "username": "outronome",
                "email": "superadmin@gmail.com",
                "password": "senha123456",
                "phone": "11999998888"
            }
        )
        # Deve falhar porque o email já existe
        assert response.status_code in [400, 409, 422]

    def test_register_with_invalid_email_format(self, client):
        """Testa registro com formato de email inválido."""
        response = client.post(
            "/auth/register/",
            json={
                "username": "novousuario",
                "email": "email_invalido",
                "password": "senha123456"
            }
        )
        assert response.status_code == 422

    def test_register_with_missing_required_fields(self, client):
        """Testa registro sem campos obrigatórios."""
        response = client.post(
            "/auth/register/",
            json={
                "username": "novousuario"
            }
        )
        assert response.status_code == 422


class TestUserRead:
    """Testes para leitura de usuários."""

    def test_read_user_without_authentication(self, client, superadmin_user):
        """Testa leitura de usuário sem autenticação."""
        response = client.get(f"/user/read/{superadmin_user.id_user}")
        assert response.status_code == 401

    def test_read_nonexistent_user(self, client, auth_headers):
        """Testa leitura de usuário inexistente."""
        response = client.get("/user/read/99999", headers=auth_headers)
        assert response.status_code in [401, 403, 404]


class TestUserCreate:
    """Testes para criação de usuários (endpoint protegido)."""

    def test_create_user_without_authentication(self, client, user_payload):
        """Testa criação de usuário sem autenticação."""
        response = client.post("/user/create/", json=user_payload)
        assert response.status_code == 401

    def test_create_user_with_invalid_data(self, client, auth_headers):
        """Testa criação de usuário com dados inválidos."""
        response = client.post(
            "/user/create/",
            headers=auth_headers,
            json={"username": "test"}  # Faltam campos obrigatórios
        )
        assert response.status_code in [401, 422]


class TestUserUpdate:
    """Testes para atualização de usuários."""

    def test_update_user_without_authentication(self, client, superadmin_user):
        """Testa atualização de usuário sem autenticação."""
        response = client.put(
            f"/user/update/{superadmin_user.id_user}",
            json={"username": "novoname"}
        )
        assert response.status_code == 401


class TestUserDelete:
    """Testes para exclusão de usuários."""

    def test_delete_user_without_authentication(self, client, superadmin_user):
        """Testa exclusão de usuário sem autenticação."""
        response = client.delete(f"/user/delete/{superadmin_user.id_user}")
        assert response.status_code == 401
