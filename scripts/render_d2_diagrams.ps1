$ErrorActionPreference = 'Stop'

$repoRoot = Split-Path -Parent $PSScriptRoot
$d2 = Get-Command 'd2' -ErrorAction Stop

$sourceDir = Join-Path $repoRoot 'diagrams\source'
$svgDir = Join-Path $repoRoot 'diagrams\svg'
$pngDir = Join-Path $repoRoot 'diagrams\png'

New-Item -ItemType Directory -Force -Path $svgDir, $pngDir | Out-Null

$diagrams = @(
    @{ Name = 'ml_pipeline'; Source = 'ml_pipeline.d2' },
    @{ Name = 'system_architecture'; Source = 'system_architecture.d2' }
)

foreach ($diagram in $diagrams) {
    $source = Join-Path $sourceDir $diagram.Source
    if (-not (Test-Path -LiteralPath $source)) {
        throw "Не найден исходник D2: $source"
    }

    $svg = Join-Path $svgDir ($diagram.Name + '.svg')
    $png = Join-Path $pngDir ($diagram.Name + '.png')
    $svgTemp = Join-Path $svgDir ($diagram.Name + '.tmp.svg')
    $pngTemp = Join-Path $pngDir ($diagram.Name + '.tmp.png')

    Remove-Item -LiteralPath $svg, $png, $svgTemp, $pngTemp -Force -ErrorAction SilentlyContinue

    try {
        & $d2.Source $source $svgTemp
        if ($LASTEXITCODE -ne 0) {
            throw "D2 не смог создать SVG для $($diagram.Name) (код $LASTEXITCODE)."
        }

        & $d2.Source $source $pngTemp
        if ($LASTEXITCODE -ne 0) {
            throw "D2 не смог создать PNG для $($diagram.Name) (код $LASTEXITCODE)."
        }

        if (-not (Test-Path -LiteralPath $svgTemp) -or (Get-Item -LiteralPath $svgTemp).Length -eq 0) {
            throw "SVG для $($diagram.Name) не создан или пуст."
        }
        if (-not (Test-Path -LiteralPath $pngTemp) -or (Get-Item -LiteralPath $pngTemp).Length -eq 0) {
            throw "PNG для $($diagram.Name) не создан или пуст."
        }

        Move-Item -LiteralPath $svgTemp -Destination $svg -Force
        Move-Item -LiteralPath $pngTemp -Destination $png -Force
        Write-Host "Созданы: $svg и $png"
    }
    catch {
        Remove-Item -LiteralPath $svgTemp, $pngTemp, $svg, $png -Force -ErrorAction SilentlyContinue
        throw
    }
}

Write-Host 'Генерация двух D2-диаграмм завершена успешно.' -ForegroundColor Green
