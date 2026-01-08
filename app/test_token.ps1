# Script PowerShell para testar geração de token

Write-Host "🔑 Testando endpoint /token_generate/" -ForegroundColor Cyan
Write-Host "=" * 80

$body = @{
    username = "superadmin@gmail.com"
    password = "123123123"
}

try {
    $response = Invoke-RestMethod -Uri "http://localhost:8000/token_generate/" `
                                   -Method POST `
                                   -ContentType "application/x-www-form-urlencoded" `
                                   -Body $body
    
    Write-Host "`n✅ TOKEN GERADO COM SUCESSO!" -ForegroundColor Green
    Write-Host "=" * 80
    Write-Host "Access Token:" -ForegroundColor Yellow
    Write-Host $response.access_token
    Write-Host "`nToken Type:" -ForegroundColor Yellow
    Write-Host $response.token_type
    Write-Host "`n💡 Use este token no header Authorization:" -ForegroundColor Cyan
    Write-Host "Authorization: Bearer $($response.access_token.Substring(0, 50))..." -ForegroundColor Gray
    
} catch {
    Write-Host "`n❌ ERRO ao gerar token!" -ForegroundColor Red
    Write-Host "Detalhes: $($_.Exception.Message)" -ForegroundColor Red
    
    if ($_.ErrorDetails.Message) {
        Write-Host "Resposta do servidor:" -ForegroundColor Yellow
        Write-Host $_.ErrorDetails.Message
    }
}

Write-Host "`n" + "=" * 80
Write-Host "Pressione qualquer tecla para sair..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
