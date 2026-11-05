$ErrorActionPreference = 'Stop'

$repoRoot = Split-Path -Parent $PSScriptRoot
$names = @(
    'c4_landscape',
    'c4_context',
    'c4_container',
    'use_case',
    'sequence_batch_prediction',
    'ml_pipeline_activity',
    'ml_pipeline',
    'system_architecture'
)

$missing = @()
foreach ($name in $names) {
    foreach ($format in @('svg', 'png')) {
        $path = Join-Path $repoRoot ("diagrams\{0}\{1}.{2}" -f $format, $name, $format)
        if (-not (Test-Path -LiteralPath $path)) {
            $missing += $path
        }
    }
}

if ($missing.Count -gt 0) {
    Write-Host 'Не найдены экспорты:' -ForegroundColor Yellow
    $missing | ForEach-Object { Write-Host " - $_" }
    throw 'Комплект диаграмм ещё не готов к коммиту.'
}

Write-Host 'Проверка пройдена: найдены все 8 SVG и 8 PNG.' -ForegroundColor Green
