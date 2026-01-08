from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse
import json
from datetime import datetime
from jose import jwt
from typing import Dict, Any
import httpx

router = APIRouter(
    prefix="/test",
    tags=["test"],
    responses={404: {"description": "Not found"}}
)

BASE_URL = "http://localhost:8181"

def decode_jwt_token_unsafe(token: str) -> Dict[Any, Any]:
    """Decodifica um token JWT sem verificar a assinatura (apenas para debug)"""
    try:
        decoded = jwt.get_unverified_claims(token)
        return decoded
    except Exception as e:
        return {"error": f"Erro ao decodificar token: {e}"}

@router.get("/auth-system", status_code=status.HTTP_200_OK)
async def test_complete_auth_system():
    """
    🧪 Testa todo o sistema de autenticação e autorização
    
    Executa testes em ordem:
    1. Login Superadmin 
    2. Criação de usuários pelo Superadmin
    3. Login Admin
    4. Criação de usuários pelo Admin (com restrições)
    5. Listagem de usuários
    6. Controle de permissões
    """
    
    results = {
        "test_summary": {
            "timestamp": datetime.now().isoformat(),
            "total_tests": 10,
            "passed": 0,
            "failed": 0,
            "errors": []
        },
        "tests": {}
    }
    
    try:
        # TESTE 1: Login do Superadmin
        print("🔐 Teste 1: Login Superadmin")
        test_name = "superadmin_login"
        
        superadmin_data = {
            "username": "superadmin@gmail.com",
            "password": "123123123"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{BASE_URL}/token_generate/",
                data=superadmin_data,
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
        
        if response.status_code == 200:
            token_data = response.json()
            superadmin_token = token_data["access_token"]
            decoded = decode_jwt_token_unsafe(superadmin_token)
            
            results["tests"][test_name] = {
                "status": "PASSED" if decoded.get("role") == "superadmin" else "FAILED",
                "expected_role": "superadmin",
                "actual_role": decoded.get("role"),
                "token_payload": decoded,
                "response_code": response.status_code
            }
            
            if decoded.get("role") == "superadmin":
                results["test_summary"]["passed"] += 1
            else:
                results["test_summary"]["failed"] += 1
                results["test_summary"]["errors"].append(f"Superadmin role incorrect: {decoded.get('role')}")
        else:
            results["tests"][test_name] = {
                "status": "FAILED",
                "error": response.text,
                "response_code": response.status_code
            }
            results["test_summary"]["failed"] += 1
            results["test_summary"]["errors"].append(f"Superadmin login failed: {response.status_code}")
            superadmin_token = None

        # TESTE 2: Criar usuário Admin pelo Superadmin
        print("👥 Teste 2: Criar Admin")
        test_name = "create_admin_by_superadmin"
        
        if superadmin_token:
            headers = {
                "Authorization": f"Bearer {superadmin_token}",
                "Content-Type": "application/json"
            }
            
            admin_user_data = {
                "username": "admin_test",
                "email": "admin_test@company.com",
                "password": "admin123",
                "role": "admin", 
                "company_id": 1
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{BASE_URL}/user/create/",
                    json=admin_user_data,
                    headers=headers
                )
            
            results["tests"][test_name] = {
                "status": "PASSED" if response.status_code == 201 else "FAILED",
                "response_code": response.status_code,
                "response_body": response.text
            }
            
            if response.status_code == 201:
                results["test_summary"]["passed"] += 1
            else:
                results["test_summary"]["failed"] += 1
                results["test_summary"]["errors"].append(f"Admin creation failed: {response.status_code}")
        else:
            results["tests"][test_name] = {"status": "SKIPPED", "reason": "No superadmin token"}
            results["test_summary"]["failed"] += 1

        # TESTE 3: Criar usuário comum pelo Superadmin  
        print("👤 Teste 3: Criar usuário comum")
        test_name = "create_user_by_superadmin"
        
        if superadmin_token:
            regular_user_data = {
                "username": "user_test",
                "email": "user_test@company.com",
                "password": "user123",
                "role": "user",
                "company_id": 1
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{BASE_URL}/user/create/",
                    json=regular_user_data,
                    headers=headers
                )
            
            results["tests"][test_name] = {
                "status": "PASSED" if response.status_code == 201 else "FAILED",
                "response_code": response.status_code,
                "response_body": response.text
            }
            
            if response.status_code == 201:
                results["test_summary"]["passed"] += 1
            else:
                results["test_summary"]["failed"] += 1
                results["test_summary"]["errors"].append(f"User creation failed: {response.status_code}")
        else:
            results["tests"][test_name] = {"status": "SKIPPED", "reason": "No superadmin token"}
            results["test_summary"]["failed"] += 1

        # TESTE 4: Login do Admin
        print("🔑 Teste 4: Login Admin") 
        test_name = "admin_login"
        
        admin_data = {
            "username": "admin_test@company.com",
            "password": "admin123"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{BASE_URL}/token_generate/",
                data=admin_data,
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
        
        if response.status_code == 200:
            token_data = response.json()
            admin_token = token_data["access_token"]
            decoded = decode_jwt_token_unsafe(admin_token)
            
            role_correct = decoded.get("role") == "admin"
            company_correct = decoded.get("company_id") == 1
            
            results["tests"][test_name] = {
                "status": "PASSED" if (role_correct and company_correct) else "FAILED",
                "expected_role": "admin",
                "actual_role": decoded.get("role"),
                "expected_company_id": 1,
                "actual_company_id": decoded.get("company_id"),
                "token_payload": decoded,
                "response_code": response.status_code
            }
            
            if role_correct and company_correct:
                results["test_summary"]["passed"] += 1
            else:
                results["test_summary"]["failed"] += 1
                results["test_summary"]["errors"].append(f"Admin login validation failed")
        else:
            results["tests"][test_name] = {
                "status": "FAILED",
                "error": response.text,
                "response_code": response.status_code
            }
            results["test_summary"]["failed"] += 1
            results["test_summary"]["errors"].append(f"Admin login failed: {response.status_code}")
            admin_token = None

        # TESTE 5: Admin criando usuário da própria empresa
        print("🏢 Teste 5: Admin criar usuário própria empresa")
        test_name = "admin_create_same_company"
        
        if admin_token:
            headers = {
                "Authorization": f"Bearer {admin_token}",
                "Content-Type": "application/json"
            }
            
            user_same_company = {
                "username": "user2_test",
                "email": "user2_test@company.com",
                "password": "user123",
                "role": "user",
                "company_id": 1
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{BASE_URL}/user/create/",
                    json=user_same_company,
                    headers=headers
                )
            
            results["tests"][test_name] = {
                "status": "PASSED" if response.status_code == 201 else "FAILED",
                "response_code": response.status_code,
                "response_body": response.text
            }
            
            if response.status_code == 201:
                results["test_summary"]["passed"] += 1
            else:
                results["test_summary"]["failed"] += 1
                results["test_summary"]["errors"].append(f"Admin same company creation failed: {response.status_code}")
        else:
            results["tests"][test_name] = {"status": "SKIPPED", "reason": "No admin token"}
            results["test_summary"]["failed"] += 1

        # TESTE 6: Admin tentando criar usuário de outra empresa (deve falhar)
        print("❌ Teste 6: Admin tentar criar usuário outra empresa")
        test_name = "admin_create_other_company"
        
        if admin_token:
            user_other_company = {
                "username": "user3_test", 
                "email": "user3_test@othercompany.com",
                "password": "user123",
                "role": "user",
                "company_id": 2  # Empresa diferente
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{BASE_URL}/user/create/",
                    json=user_other_company,
                    headers=headers
                )
            
            # Este deve falhar com 403
            results["tests"][test_name] = {
                "status": "PASSED" if response.status_code == 403 else "FAILED",
                "expected_code": 403,
                "actual_code": response.status_code,
                "response_body": response.text,
                "security_note": "Admin deve ser impedido de criar usuário de outra empresa"
            }
            
            if response.status_code == 403:
                results["test_summary"]["passed"] += 1
            else:
                results["test_summary"]["failed"] += 1 
                results["test_summary"]["errors"].append(f"SECURITY ISSUE: Admin created user in other company")
        else:
            results["tests"][test_name] = {"status": "SKIPPED", "reason": "No admin token"}
            results["test_summary"]["failed"] += 1

        # TESTE 7: Login usuário comum
        print("👤 Teste 7: Login usuário comum")
        test_name = "user_login"
        
        user_data = {
            "username": "user_test@company.com",
            "password": "user123"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{BASE_URL}/token_generate/",
                data=user_data,
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
        
        if response.status_code == 200:
            token_data = response.json()
            user_token = token_data["access_token"]
            decoded = decode_jwt_token_unsafe(user_token)
            
            role_correct = decoded.get("role") == "user"
            company_correct = decoded.get("company_id") == 1
            
            results["tests"][test_name] = {
                "status": "PASSED" if (role_correct and company_correct) else "FAILED",
                "expected_role": "user",
                "actual_role": decoded.get("role"),
                "token_payload": decoded,
                "response_code": response.status_code
            }
            
            if role_correct and company_correct:
                results["test_summary"]["passed"] += 1
            else:
                results["test_summary"]["failed"] += 1
                results["test_summary"]["errors"].append(f"User login validation failed")
        else:
            results["tests"][test_name] = {
                "status": "FAILED",
                "error": response.text,
                "response_code": response.status_code
            }
            results["test_summary"]["failed"] += 1
            results["test_summary"]["errors"].append(f"User login failed: {response.status_code}")
            user_token = None

        # TESTE 8: Usuário comum tentando criar usuário (deve falhar)
        print("🚫 Teste 8: Usuário comum tentar criar usuário")
        test_name = "user_create_permission_denied"
        
        if user_token:
            headers = {
                "Authorization": f"Bearer {user_token}",
                "Content-Type": "application/json"
            }
            
            new_user_data = {
                "username": "user4_test",
                "email": "user4_test@company.com",
                "password": "user123", 
                "role": "user",
                "company_id": 1
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{BASE_URL}/user/create/",
                    json=new_user_data,
                    headers=headers
                )
            
            # Este deve falhar com 403
            results["tests"][test_name] = {
                "status": "PASSED" if response.status_code == 403 else "FAILED",
                "expected_code": 403,
                "actual_code": response.status_code,
                "response_body": response.text,
                "security_note": "Usuário comum não deve ter permissão para criar usuários"
            }
            
            if response.status_code == 403:
                results["test_summary"]["passed"] += 1
            else:
                results["test_summary"]["failed"] += 1
                results["test_summary"]["errors"].append(f"SECURITY ISSUE: Regular user created another user")
        else:
            results["tests"][test_name] = {"status": "SKIPPED", "reason": "No user token"}
            results["test_summary"]["failed"] += 1

        # TESTE 9: Superadmin listando usuários
        print("📋 Teste 9: Superadmin listar usuários")
        test_name = "superadmin_list_users"
        
        if superadmin_token:
            headers = {"Authorization": f"Bearer {superadmin_token}"}
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{BASE_URL}/user/list/", headers=headers)
            
            results["tests"][test_name] = {
                "status": "PASSED" if response.status_code == 200 else "FAILED",
                "response_code": response.status_code,
                "user_count": len(response.json()) if response.status_code == 200 else 0,
                "note": "Superadmin deve ver todos os usuários do sistema"
            }
            
            if response.status_code == 200:
                results["test_summary"]["passed"] += 1
            else:
                results["test_summary"]["failed"] += 1
                results["test_summary"]["errors"].append(f"Superadmin list users failed: {response.status_code}")
        else:
            results["tests"][test_name] = {"status": "SKIPPED", "reason": "No superadmin token"}
            results["test_summary"]["failed"] += 1

        # TESTE 10: Admin listando usuários da própria empresa
        print("🏢 Teste 10: Admin listar usuários própria empresa")
        test_name = "admin_list_company_users"
        
        if admin_token:
            headers = {"Authorization": f"Bearer {admin_token}"}
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{BASE_URL}/user/list/", headers=headers)
            
            results["tests"][test_name] = {
                "status": "PASSED" if response.status_code == 200 else "FAILED",
                "response_code": response.status_code,
                "user_count": len(response.json()) if response.status_code == 200 else 0,
                "note": "Admin deve ver apenas usuários da própria empresa"
            }
            
            if response.status_code == 200:
                results["test_summary"]["passed"] += 1
            else:
                results["test_summary"]["failed"] += 1
                results["test_summary"]["errors"].append(f"Admin list users failed: {response.status_code}")
        else:
            results["tests"][test_name] = {"status": "SKIPPED", "reason": "No admin token"}
            results["test_summary"]["failed"] += 1

        # Calcular score final
        total_tests = results["test_summary"]["total_tests"]
        passed_tests = results["test_summary"]["passed"]
        success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
        
        results["test_summary"]["success_rate"] = f"{success_rate:.1f}%"
        results["test_summary"]["status"] = "SUCCESS" if success_rate >= 80 else "PARTIAL" if success_rate >= 50 else "FAILED"
        
        print(f"🏁 Testes finalizados: {passed_tests}/{total_tests} ({success_rate:.1f}%)")
        
        return results

    except httpx.ConnectError:
        error_msg = f"Não foi possível conectar ao servidor {BASE_URL}"
        results["test_summary"]["errors"].append(error_msg)
        results["test_summary"]["failed"] = results["test_summary"]["total_tests"]
        results["test_summary"]["status"] = "CONNECTION_ERROR"
        raise HTTPException(status_code=503, detail=error_msg)
        
    except Exception as e:
        error_msg = f"Erro inesperado durante os testes: {str(e)}"
        results["test_summary"]["errors"].append(error_msg)
        results["test_summary"]["status"] = "UNEXPECTED_ERROR"
        raise HTTPException(status_code=500, detail=error_msg)

@router.get("/auth-system/summary", status_code=status.HTTP_200_OK)
async def test_auth_system_summary():
    """
    📊 Retorna um resumo rápido dos testes de autenticação
    """
    try:
        # Teste rápido apenas do superadmin
        superadmin_data = {
            "username": "superadmin@gmail.com", 
            "password": "123123123"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{BASE_URL}/token_generate/",
                data=superadmin_data,
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
        
        if response.status_code == 200:
            token_data = response.json()
            decoded = decode_jwt_token_unsafe(token_data["access_token"])
            
            return {
                "status": "HEALTHY",
                "timestamp": datetime.now().isoformat(),
                "superadmin_login": "OK",
                "superadmin_role": decoded.get("role"),
                "message": "Sistema de autenticação funcionando. Execute /test/auth-system para testes completos."
            }
        else:
            return {
                "status": "UNHEALTHY", 
                "timestamp": datetime.now().isoformat(),
                "error": "Superadmin login failed",
                "response_code": response.status_code
            }
            
    except Exception as e:
        return {
            "status": "ERROR",
            "timestamp": datetime.now().isoformat(), 
            "error": str(e)
        }
