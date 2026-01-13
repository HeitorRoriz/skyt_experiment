# Cleanup Guide for Camera-Ready Submission

**Purpose:** Organize documentation and remove temporary files for clean camera-ready submission.

---

## Manual File Organization

### Step 1: Move Reference Documentation to docs/

```bash
# Create directories
mkdir -p docs/archive

# Move reference docs
mv IMPLEMENTATION_COMPLETE.md docs/
mv METRICS_IMPLEMENTATION.md docs/
mv FINAL_TRANSFORMATION_REPORT.md docs/
mv VALIDATION_RESULTS.md docs/
mv PHASE2_COMPLETION_REPORT.md docs/
mv PHASE3_VALIDATION_RESULTS.md docs/
mv PHASE4_VALIDATION_RESULTS.md docs/
mv QUICK_START_METRICS.md docs/
mv README_metrics.md docs/
mv SKYT_COMPLETE_OVERVIEW.md docs/
```

### Step 2: Archive Historical Documentation

```bash
# Move to archive
mv TRANSFORMATION_IMPLEMENTATION_PLAN.md docs/archive/
mv PROPERTY_MAPPING_IMPLEMENTATION_PLAN.md docs/archive/
mv TRANSFORMATION_VALIDATION_CHECKLIST.md docs/archive/
mv INCOMPLETE_TRANSFORMATIONS_ANALYSIS.md docs/archive/
mv DELTA_RESCUE_ROOT_CAUSE.md docs/archive/
mv DEBUG_CHECKLIST_STATUS.md docs/archive/
mv OOD_QUICK_REFERENCE.md docs/archive/
mv OUT_OF_DOMAIN_POLICY.md docs/archive/
mv OOD_IMPLEMENTATION_SUMMARY.md docs/archive/
mv CONTRACT_AWARE_VALIDATION.md docs/archive/
mv VARIABLE_NAMING_CONSTRAINTS.md docs/archive/
mv PROPERTY_TRANSFORMATION_MAPPING.md docs/archive/
mv TODAYS_EXPERIMENTAL_PLAN.md docs/archive/
```

### Step 3: Remove Temporary Files

```bash
# Remove debug/temp files
rm -f debug_run.txt
rm -f pipeline_debug.txt
rm -f analyze_failures.py
rm -f organize_docs.ps1
```

---

## Essential Files (Keep in Root)

After cleanup, your root directory should contain:

### Core Documentation (8 files)
- ✅ README.md
- ✅ DISTANCE_METRICS.md
- ✅ STATISTICAL_METHODS.md
- ✅ LIMITATIONS.md
- ✅ DISCUSSION_CAMERA_READY.md
- ✅ CROSS_MODEL_SUPPORT.md
- ✅ MULTI_FILE_ROADMAP.md
- ✅ REVIEWER_RESPONSES.md
- ✅ DOCUMENTATION_INDEX.md
- ✅ CLEANUP_GUIDE.md (this file)

### Project Files
- LICENSE.txt
- requirements.txt
- .gitignore
- .env (not committed)
- main.py

### Directories
- src/ (source code)
- tests/ (test suite)
- contracts/ (contract templates)
- api/ (API server)
- workers/ (Celery workers)
- web/ (frontend)
- docs/ (reference documentation)
- docs/archive/ (historical documentation)

---

## Verification Checklist

After cleanup, verify:

- [ ] All 9 essential .md files in root
- [ ] 10 reference docs in docs/
- [ ] 13 historical docs in docs/archive/
- [ ] No debug/temp files in root
- [ ] Git status clean (all changes committed)
- [ ] All cross-references in docs still work

---

## Git Commands

```bash
# Add organized structure
git add docs/
git add CLEANUP_GUIDE.md

# Commit cleanup
git commit -m "chore: organize documentation for camera-ready submission

Moved reference documentation to docs/
Moved historical documentation to docs/archive/
Removed temporary debug files
Essential documentation remains in root for easy access

See DOCUMENTATION_INDEX.md for complete file organization"

# Verify clean state
git status
```

---

## Quick Cleanup (One Command)

If you prefer a single command approach:

```bash
# Create directories and move files in one go
mkdir -p docs/archive && \
mv IMPLEMENTATION_COMPLETE.md METRICS_IMPLEMENTATION.md FINAL_TRANSFORMATION_REPORT.md VALIDATION_RESULTS.md PHASE2_COMPLETION_REPORT.md PHASE3_VALIDATION_RESULTS.md PHASE4_VALIDATION_RESULTS.md QUICK_START_METRICS.md README_metrics.md SKYT_COMPLETE_OVERVIEW.md docs/ 2>/dev/null; \
mv TRANSFORMATION_IMPLEMENTATION_PLAN.md PROPERTY_MAPPING_IMPLEMENTATION_PLAN.md TRANSFORMATION_VALIDATION_CHECKLIST.md INCOMPLETE_TRANSFORMATIONS_ANALYSIS.md DELTA_RESCUE_ROOT_CAUSE.md DEBUG_CHECKLIST_STATUS.md OOD_QUICK_REFERENCE.md OUT_OF_DOMAIN_POLICY.md OOD_IMPLEMENTATION_SUMMARY.md CONTRACT_AWARE_VALIDATION.md VARIABLE_NAMING_CONSTRAINTS.md PROPERTY_TRANSFORMATION_MAPPING.md TODAYS_EXPERIMENTAL_PLAN.md docs/archive/ 2>/dev/null; \
rm -f debug_run.txt pipeline_debug.txt analyze_failures.py organize_docs.ps1 2>/dev/null; \
echo "Cleanup complete! See DOCUMENTATION_INDEX.md for file locations."
```

---

## After Cleanup

Your repository structure will be:

```
skyt_experiment/
├── README.md                           # Project overview
├── DISTANCE_METRICS.md                 # Metric justification
├── STATISTICAL_METHODS.md              # Statistical rigor
├── LIMITATIONS.md                      # Threats to validity
├── DISCUSSION_CAMERA_READY.md          # N-Version, determinism
├── CROSS_MODEL_SUPPORT.md              # Multi-model evaluation
├── MULTI_FILE_ROADMAP.md               # Future work plan
├── REVIEWER_RESPONSES.md               # Reviewer concern mapping
├── DOCUMENTATION_INDEX.md              # Documentation organization
├── CLEANUP_GUIDE.md                    # This file
├── main.py                             # CLI entry point
├── requirements.txt                    # Dependencies
├── src/                                # Source code
├── tests/                              # Test suite
├── contracts/                          # Contract templates
├── docs/                               # Reference documentation
│   ├── IMPLEMENTATION_COMPLETE.md
│   ├── METRICS_IMPLEMENTATION.md
│   ├── ... (10 files)
│   └── archive/                        # Historical documentation
│       ├── TRANSFORMATION_IMPLEMENTATION_PLAN.md
│       ├── ... (13 files)
├── api/                                # API server
├── workers/                            # Celery workers
└── web/                                # Frontend
```

Clean, organized, and ready for camera-ready submission! 🎉
