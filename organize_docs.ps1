# organize_docs.ps1
# Organize SKYT documentation for camera-ready submission

Write-Host "Organizing SKYT documentation..." -ForegroundColor Cyan

# Create directories if they don't exist
New-Item -ItemType Directory -Force -Path "docs" | Out-Null
New-Item -ItemType Directory -Force -Path "docs\archive" | Out-Null

Write-Host "`nMoving reference documentation to docs/..." -ForegroundColor Yellow

# Move reference documentation to docs/
$refDocs = @(
    "IMPLEMENTATION_COMPLETE.md",
    "METRICS_IMPLEMENTATION.md",
    "FINAL_TRANSFORMATION_REPORT.md",
    "VALIDATION_RESULTS.md",
    "PHASE2_COMPLETION_REPORT.md",
    "PHASE3_VALIDATION_RESULTS.md",
    "PHASE4_VALIDATION_RESULTS.md",
    "QUICK_START_METRICS.md",
    "README_metrics.md",
    "SKYT_COMPLETE_OVERVIEW.md"
)

foreach ($doc in $refDocs) {
    if (Test-Path $doc) {
        Move-Item -Path $doc -Destination "docs\" -Force
        Write-Host "  Moved: $doc" -ForegroundColor Green
    }
}

Write-Host "`nMoving historical documentation to docs/archive/..." -ForegroundColor Yellow

# Move historical documentation to docs/archive/
$archiveDocs = @(
    "TRANSFORMATION_IMPLEMENTATION_PLAN.md",
    "PROPERTY_MAPPING_IMPLEMENTATION_PLAN.md",
    "TRANSFORMATION_VALIDATION_CHECKLIST.md",
    "INCOMPLETE_TRANSFORMATIONS_ANALYSIS.md",
    "DELTA_RESCUE_ROOT_CAUSE.md",
    "DEBUG_CHECKLIST_STATUS.md",
    "OOD_QUICK_REFERENCE.md",
    "OUT_OF_DOMAIN_POLICY.md",
    "OOD_IMPLEMENTATION_SUMMARY.md",
    "CONTRACT_AWARE_VALIDATION.md",
    "VARIABLE_NAMING_CONSTRAINTS.md",
    "PROPERTY_TRANSFORMATION_MAPPING.md",
    "TODAYS_EXPERIMENTAL_PLAN.md"
)

foreach ($doc in $archiveDocs) {
    if (Test-Path $doc) {
        Move-Item -Path $doc -Destination "docs\archive\" -Force
        Write-Host "  Archived: $doc" -ForegroundColor Green
    }
}

Write-Host "`nRemoving temporary files..." -ForegroundColor Yellow

# Remove temporary debug files
$tempFiles = @(
    "debug_run.txt",
    "pipeline_debug.txt",
    "analyze_failures.py"
)

foreach ($file in $tempFiles) {
    if (Test-Path $file) {
        Remove-Item -Path $file -Force
        Write-Host "  Removed: $file" -ForegroundColor Red
    }
}

Write-Host "`nEssential documentation remaining in root:" -ForegroundColor Cyan
$essentialDocs = @(
    "README.md",
    "DISTANCE_METRICS.md",
    "STATISTICAL_METHODS.md",
    "LIMITATIONS.md",
    "DISCUSSION_CAMERA_READY.md",
    "CROSS_MODEL_SUPPORT.md",
    "MULTI_FILE_ROADMAP.md",
    "REVIEWER_RESPONSES.md",
    "DOCUMENTATION_INDEX.md"
)

foreach ($doc in $essentialDocs) {
    if (Test-Path $doc) {
        Write-Host "  ✓ $doc" -ForegroundColor Green
    } else {
        Write-Host "  ✗ $doc (MISSING!)" -ForegroundColor Red
    }
}

Write-Host "`nDocumentation organization complete!" -ForegroundColor Cyan
Write-Host "See DOCUMENTATION_INDEX.md for complete documentation map." -ForegroundColor White
