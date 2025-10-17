param(
    [switch]$Build,
    [string]$Configuration = "Release",
    [switch]$RunCTests,
    [switch]$RunPythonTests
)

$projectRoot = (Get-Location).Path
$buildRoot   = Join-Path $projectRoot "build"
$targetBin   = Join-Path $buildRoot $Configuration

function Write-Info($m) { Write-Host $m }
function Write-Err($m)  { Write-Host $m -ForegroundColor Red }

if ($Build) {
    if (-not (Test-Path $buildRoot)) {
        Write-Info "Gerando projeto CMake..."
        cmake -S $projectRoot -B $buildRoot -G "Visual Studio 17 2022" -A x64 -DCMAKE_BUILD_TYPE=$Configuration
    }
    Write-Info "Compilando ($Configuration)..."
    cmake --build $buildRoot --config $Configuration -- /m
    if ($LASTEXITCODE -ne 0) { Write-Err "Build retornou código $LASTEXITCODE. Continuando." }
}

if ($RunCTests) {
    if (Get-Command ctest -ErrorAction SilentlyContinue) {
        Push-Location $buildRoot
        ctest -C $Configuration --output-on-failure
        $ctestExit = $LASTEXITCODE
        Pop-Location
        if ($ctestExit -ne 0) { Write-Err "ctest retornou $ctestExit." }
    } else {
        Write-Err "ctest não encontrado no PATH."
    }
}

$searchRoots = @()
if (Test-Path $targetBin) { $searchRoots += $targetBin } else { $searchRoots += $buildRoot }
$searchRoots += Join-Path $buildRoot "bin\$Configuration"
$searchRoots += Join-Path $buildRoot "bin"
$searchRoots = $searchRoots | Where-Object { Test-Path $_ } | Select-Object -Unique

if (-not $searchRoots) {
    Write-Err "Pasta build não encontrada. Saindo."
    exit 2
}

$testExes = @()
foreach ($r in $searchRoots) {
    $testExes += Get-ChildItem -Path $r -Recurse -Filter 'test_*.exe' -File -ErrorAction SilentlyContinue
}
$testExes = $testExes | Sort-Object FullName

if (-not $testExes -or $testExes.Count -eq 0) {
    Write-Err "Nenhum test_*.exe encontrado em: $($searchRoots -join ', ')"
    exit 3
}

$timestamp = (Get-Date).ToString("yyyyMMdd_HHmmss")
$logsRoot  = Join-Path $buildRoot "tests_logs\$Configuration\$timestamp"
New-Item -ItemType Directory -Path $logsRoot -Force | Out-Null

$failures  = @()
$successes = @()

foreach ($f in $testExes) {
    $exe  = $f.FullName
    $name = $f.BaseName
    $log  = Join-Path $logsRoot "$name.log"
    Write-Info "==> $name"
    & "$exe" 2>&1 | Tee-Object -FilePath $log
    $code = $LASTEXITCODE
    if ($code -ne 0) {
        Write-Err "    FAIL ($code)"
        $failures += [PSCustomObject]@{ Name=$name; ExitCode=$code; Log=$log; Path=$exe }
    } else {
        Write-Info "    OK"
        $successes += [PSCustomObject]@{ Name=$name; Log=$log; Path=$exe }
    }
}

if ($RunPythonTests) {
    if (Get-Command pytest -ErrorAction SilentlyContinue) {
        $pyLog = Join-Path $logsRoot "pytest.log"
        Push-Location (Join-Path $projectRoot "tests\python")
        pytest -q 2>&1 | Tee-Object -FilePath $pyLog
        $pyCode = $LASTEXITCODE
        Pop-Location
        if ($pyCode -ne 0) {
            $failures += [PSCustomObject]@{ Name='pytest'; ExitCode=$pyCode; Log=$pyLog; Path='tests/python' }
            Write-Err "pytest: FAIL ($pyCode)"
        } else {
            $successes += [PSCustomObject]@{ Name='pytest'; Log=$pyLog; Path='tests/python' }
            Write-Info "pytest: OK"
        }
    } else {
        Write-Err "pytest não encontrado no PATH."
    }
}

$totalExecuted = $testExes.Count
if ($RunPythonTests) { $totalExecuted += 1 }

Write-Host ""
Write-Host "Resumo:"
Write-Host "  Executados: $totalExecuted"
Write-Host "  Sucessos:   $($successes.Count)"
Write-Host "  Falhas:     $($failures.Count)"

if ($failures.Count -gt 0) {
    Write-Host ""
    Write-Err "Falhas detalhadas:"
    $failures | ForEach-Object {
        Write-Err " - $($_.Name) (exit $($_.ExitCode)) log: $($_.Log)"
    }
    Write-Err ""
    Write-Err "Logs em: $logsRoot"
    exit 1
}

Write-Host ""
Write-Host "Todos os testes concluidos com sucesso. Logs: $logsRoot"
exit 0