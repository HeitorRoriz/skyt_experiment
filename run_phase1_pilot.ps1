# Phase 1 Pilot - Complete 30 Generations
# 1 contract × 3 models × 2 temps × 5 runs = 30 calls

$ErrorActionPreference = "Stop"

Write-Host "=" -NoNewline -ForegroundColor Cyan
Write-Host ("=" * 79) -ForegroundColor Cyan
Write-Host "SKYT PHASE 1 PILOT EXPERIMENT" -ForegroundColor Cyan
Write-Host "=" -NoNewline -ForegroundColor Cyan
Write-Host ("=" * 79) -ForegroundColor Cyan
Write-Host ""
Write-Host "Contract: fibonacci_basic" -ForegroundColor White
Write-Host "Models: gpt-4o-mini, gpt-4o, claude-3-5-sonnet-20241022" -ForegroundColor White
Write-Host "Temperatures: 0.0, 0.7" -ForegroundColor White
Write-Host "Runs per config: 5" -ForegroundColor White
Write-Host "Total generations: 30" -ForegroundColor White
Write-Host ""

$models = @("gpt-4o-mini", "gpt-4o", "claude-3-5-sonnet-20241022")
$temperatures = @(0.0, 0.7)
$contract = "fibonacci_basic"
$runs = 5

$totalCalls = 0
$successfulCalls = 0

foreach ($model in $models) {
    Write-Host ""
    Write-Host "=" -NoNewline -ForegroundColor Yellow
    Write-Host ("=" * 79) -ForegroundColor Yellow
    Write-Host "MODEL: $model" -ForegroundColor Yellow
    Write-Host "=" -NoNewline -ForegroundColor Yellow
    Write-Host ("=" * 79) -ForegroundColor Yellow
    Write-Host ""
    
    foreach ($temp in $temperatures) {
        Write-Host ""
        Write-Host "Temperature: $temp" -ForegroundColor Cyan
        Write-Host ("-" * 40) -ForegroundColor Cyan
        
        $totalCalls++
        
        try {
            # Run experiment
            python main.py --contract $contract --runs $runs --temperature $temp --model $model
            
            if ($LASTEXITCODE -eq 0) {
                $successfulCalls++
                Write-Host "✓ Completed $model at temp=$temp" -ForegroundColor Green
            } else {
                Write-Host "✗ FAILED $model at temp=$temp (exit code: $LASTEXITCODE)" -ForegroundColor Red
                Write-Host "Stopping experiment (stop-on-error mode)" -ForegroundColor Red
                exit 1
            }
            
            # Rate limiting (200ms)
            Start-Sleep -Milliseconds 200
            
        } catch {
            Write-Host "✗ EXCEPTION in $model at temp=$temp`: $_" -ForegroundColor Red
            Write-Host "Stopping experiment (stop-on-error mode)" -ForegroundColor Red
            exit 1
        }
    }
}

Write-Host ""
Write-Host "=" -NoNewline -ForegroundColor Green
Write-Host ("=" * 79) -ForegroundColor Green
Write-Host "PHASE 1 PILOT COMPLETE" -ForegroundColor Green
Write-Host "=" -NoNewline -ForegroundColor Green
Write-Host ("=" * 79) -ForegroundColor Green
Write-Host ""
Write-Host "Total configurations: $totalCalls" -ForegroundColor White
Write-Host "Successful: $successfulCalls" -ForegroundColor Green
Write-Host ""
Write-Host "Results saved to: outputs/" -ForegroundColor White
Write-Host "Check outputs/metrics_summary.csv for aggregate results" -ForegroundColor White
Write-Host ""
Write-Host "Please review the outputs before proceeding to Phase 2 (full experiment)." -ForegroundColor Yellow
Write-Host "=" -NoNewline -ForegroundColor Green
Write-Host ("=" * 79) -ForegroundColor Green
