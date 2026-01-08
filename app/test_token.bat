@echo off
REM Script para testar geração de token

echo 🔑 Testando endpoint /token_generate/
echo ================================================================================

curl -X POST "http://localhost:8000/token_generate/" ^
  -H "Content-Type: application/x-www-form-urlencoded" ^
  -d "username=superadmin@gmail.com&password=123123123"

echo.
echo.
echo ================================================================================
echo Se funcionou, você verá um JSON com "access_token" e "token_type"
pause
