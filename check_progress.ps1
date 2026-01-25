# Check Phase 2 Experiment Progress

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "SKYT PHASE 2 EXPERIMENT PROGRESS" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# Count completed experiments from metrics CSV
if (Test-Path "outputs/metrics_summary.csv") {
    $lines = (Get-Content "outputs/metrics_summary.csv" | Measure-Object -Line).Lines
    $completed = $lines - 1  # Subtract header
    
    $total = 180  # 12 contracts × 3 models × 5 temps
    $progress = ($completed / $total) * 100
    
    Write-Host "Completed: $completed / $total configurations" -ForegroundColor Green
    Write-Host "Progress: $([math]::Round($progress, 1))%" -ForegroundColor Yellow
    
    # Estimate remaining time (rough estimate: 2 min per config)
    $remaining = $total - $completed
    $estimatedMinutes = $remaining * 2
    $estimatedHours = [math]::Round($estimatedMinutes / 60, 1)
    
    Write-Host "Estimated remaining: ~$estimatedHours hours`n" -ForegroundColor Cyan
    
    # Show last 5 completed
    Write-Host "Last 5 completed experiments:" -ForegroundColor White
    Write-Host "------------------------------" -ForegroundColor Gray
    Get-Content "outputs/metrics_summary.csv" | Select-Object -Last 5
    
} else {
    Write-Host "No results yet. Experiment may still be starting...`n" -ForegroundColor Yellow
}

Write-Host "`n========================================`n" -ForegroundColor Cyan
