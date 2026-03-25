<#
Publish script for AutonomousDataOps repository.

Usage:
  .\scripts\publish.ps1 -RemoteUrl "https://github.com/user/repo.git" -Name "Your Name" -Email "you@example.com"

If no parameters are given the script uses the default remote URL set below.
#>

param(
    [string]$RemoteUrl = 'https://github.com/martinakbrehm/AutonomousDataOps-v1.git',
    [string]$Name = '',
    [string]$Email = ''
)

function Exec-Git {
    param([string[]]$Args)
    & git @Args 2>&1
}

Write-Host "Working directory: $(Get-Location)"

if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    Write-Error "git não encontrado no PATH. Instale o Git e reabra o PowerShell."
    exit 1
}

if ($Name -ne '') {
    git config user.name "$Name"
    Write-Host "Git user.name definido para: $Name"
}
if ($Email -ne '') {
    git config user.email "$Email"
    Write-Host "Git user.email definido para: $Email"
}

# Initialize repository if needed
if (-not (Test-Path .git)) {
    Write-Host "Inicializando repositório git..."
    Exec-Git init | Write-Host
}

# Add or update remote
$existing = Exec-Git remote | Out-String
if ($existing -match 'origin') {
    Write-Host "Remote 'origin' já existe; atualizando URL para $RemoteUrl"
    Exec-Git remote set-url origin $RemoteUrl | Write-Host
} else {
    Write-Host "Adicionando remote origin -> $RemoteUrl"
    Exec-Git remote add origin $RemoteUrl | Write-Host
}

# Add all files and commit if there are changes
Exec-Git add . | Out-Null
$status = Exec-Git status --porcelain
if ($status) {
    Write-Host "Criando commit inicial..."
    Exec-Git commit -m "Initial commit" | Write-Host
} else {
    Write-Host "Nada para commitar. Pulando commit."
}

# Ensure main branch and push
Exec-Git branch -M main | Out-Null
Write-Host "Fazendo push para origin main (pode solicitar autenticação)..."
Exec-Git push -u origin main | Write-Host

Write-Host "Operação concluída. Se houver erros, verifique as mensagens acima e tente novamente."
