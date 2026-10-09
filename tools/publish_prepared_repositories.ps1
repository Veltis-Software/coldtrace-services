$ErrorActionPreference = 'Stop'
$taskSource = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
$taskExports = [IO.Path]::GetFullPath((Join-Path $taskSource '..\coldtrace-sprint1-repositories'))
$taskNames = @('coldtrace-shared', 'coldtrace-monitoring-service', 'coldtrace-alert-service', 'coldtrace-api-gateway', 'coldtrace-edge-gateway', 'coldtrace-infrastructure')

function Invoke-TaskGit([string]$taskPath, [string[]]$taskArguments) {
    & git -C $taskPath @taskArguments
    if ($LASTEXITCODE -ne 0) { throw "Git failed in $taskPath" }
}

# Verify all permissions before creating branches or publishing any content.
foreach ($taskName in @('coldtrace-services') + $taskNames) {
    $taskCanPush = & gh api "repos/Veltis-Software/$taskName" --jq '.permissions.push'
    if ($LASTEXITCODE -ne 0 -or $taskCanPush -ne 'true') {
        throw "The active gh account needs Write access to Veltis-Software/$taskName."
    }
}
foreach ($taskName in $taskNames) {
    $taskPath = Join-Path $taskExports $taskName
    if (-not (Test-Path -LiteralPath $taskPath)) { throw "Missing prepared directory: $taskPath" }
    if (Test-Path -LiteralPath (Join-Path $taskPath '.git')) {
        throw "Existing Git checkout requires inspection before importing: $taskPath"
    }
    & gh api "repos/Veltis-Software/$taskName/branches/main" --silent
    if ($LASTEXITCODE -ne 0) { throw "$taskName must have an initial main branch (README)." }
}

# Preserve the exact shared revision referenced by consumer workflows.
Invoke-TaskGit $taskSource @('push', 'https://github.com/Veltis-Software/coldtrace-shared.git', '08ab5ee5321e3d7e5e4ec0b3c454a5f5da9bfcc3:refs/tags/v0.1.0-sprint1')
foreach ($taskName in $taskNames) {
    $taskPath = Join-Path $taskExports $taskName
    Invoke-TaskGit $taskPath @('init')
    Invoke-TaskGit $taskPath @('remote', 'add', 'origin', "https://github.com/Veltis-Software/$taskName.git")
    Invoke-TaskGit $taskPath @('fetch', 'origin', 'main')
    Invoke-TaskGit $taskPath @('symbolic-ref', 'HEAD', 'refs/heads/codex/tp1-import')
    Invoke-TaskGit $taskPath @('update-ref', 'refs/heads/codex/tp1-import', 'FETCH_HEAD')
    # Load only the index; retain the prepared working files.
    Invoke-TaskGit $taskPath @('read-tree', 'FETCH_HEAD')
    Invoke-TaskGit $taskPath @('add', '.')
    Invoke-TaskGit $taskPath @('commit', '-m', "feat(tp1): import verified $taskName increment")
    Invoke-TaskGit $taskPath @('push', '-u', 'origin', 'codex/tp1-import')
}
Invoke-TaskGit $taskSource @('push', '-u', 'origin', 'codex/tp1-architecture-implementation')
Write-Output 'Branches published. Open and attach review PRs in Codex; inspect CI before merging.'
