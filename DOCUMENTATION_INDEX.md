# SKYT Documentation Index

**Last Updated:** January 13, 2026  
**Camera-Ready Branch:** camera-ready-msr2026

This index organizes all SKYT documentation for the MSR 2026 camera-ready submission.

---

## 📋 Essential Documentation (For Paper)

### Core Technical Documentation

1. **README.md**
   - Project overview and quick start
   - Installation and usage
   - Core concepts

2. **DISTANCE_METRICS.md** ⭐
   - Normalized Levenshtein distance on AST
   - Distance aggregation strategy
   - Anchor selection rationale
   - Addresses "opaque metric" and "arbitrary anchor" concerns

3. **STATISTICAL_METHODS.md** ⭐
   - Confidence intervals (Wilson score, bootstrap)
   - Fisher's exact test
   - Effect sizes (Cohen's h, odds ratios)
   - Holm-Bonferroni correction
   - Addresses "lack of statistical analysis" concern

4. **LIMITATIONS.md** ⭐
   - Threats to validity (internal, external, construct)
   - Single-file limitation
   - Sample size justification
   - Model drift concerns
   - Addresses "no threats to validity" concern

5. **DISCUSSION_CAMERA_READY.md** ⭐
   - N-Version Programming comparison
   - Determinism clarification
   - Addresses reviewer philosophical concerns

6. **CROSS_MODEL_SUPPORT.md** ⭐
   - Multi-model evaluation (GPT-4o-mini, GPT-5.2, Claude Sonnet 4.5)
   - API integration details
   - Addresses "single model" concern

7. **MULTI_FILE_ROADMAP.md** ⭐
   - 12-week implementation plan for multi-file support
   - Production SaaS integration
   - Research questions for future work
   - Addresses "multi-file limitation" concern

8. **REVIEWER_RESPONSES.md** ⭐
   - Comprehensive mapping of all reviewer concerns to solutions
   - Status tracking (16/19 completed)
   - Action items for camera-ready

---

## 🔬 Research & Validation (Reference)

### Implementation Reports

9. **IMPLEMENTATION_COMPLETE.md**
   - Complete system implementation summary
   - All core components documented

10. **METRICS_IMPLEMENTATION.md**
    - Three-tier metrics (R_raw, R_behavioral, R_structural)
    - Calculation methods

11. **FINAL_TRANSFORMATION_REPORT.md**
    - Transformation system validation
    - Success rates and patterns

### Validation Results

12. **VALIDATION_RESULTS.md**
    - Initial validation experiments
    - Baseline results

13. **PHASE2_COMPLETION_REPORT.md**
    - Phase 2 implementation results

14. **PHASE3_VALIDATION_RESULTS.md**
    - Phase 3 validation experiments

15. **PHASE4_VALIDATION_RESULTS.md**
    - Phase 4 validation experiments

---

## 🛠️ Development Documentation (Archive)

### Implementation Plans

16. **TRANSFORMATION_IMPLEMENTATION_PLAN.md**
    - Original transformation system design
    - Implementation roadmap

17. **PROPERTY_MAPPING_IMPLEMENTATION_PLAN.md**
    - Property-to-transformation mapping
    - Design decisions

18. **TRANSFORMATION_VALIDATION_CHECKLIST.md**
    - Validation checklist for transformations
    - Test coverage

### Analysis & Debugging

19. **INCOMPLETE_TRANSFORMATIONS_ANALYSIS.md**
    - Analysis of transformation failures
    - Improvement strategies

20. **DELTA_RESCUE_ROOT_CAUSE.md**
    - Root cause analysis of Δ_rescue metric
    - Bug fixes

21. **DEBUG_CHECKLIST_STATUS.md**
    - Debugging status tracking
    - Issue resolution

### Quick References

22. **QUICK_START_METRICS.md**
    - Quick reference for metrics
    - Usage examples

23. **README_metrics.md**
    - Metrics CSV template documentation
    - Data collection guide

24. **OOD_QUICK_REFERENCE.md**
    - Out-of-domain quick reference
    - Policy summary

---

## 📚 Specialized Topics

### Out-of-Domain Handling

25. **OUT_OF_DOMAIN_POLICY.md**
    - Policy for handling out-of-domain outputs
    - Detection and handling strategies

26. **OOD_IMPLEMENTATION_SUMMARY.md**
    - OOD implementation details
    - Code references

### Contract System

27. **CONTRACT_AWARE_VALIDATION.md**
    - Contract-aware validation system
    - Validation rules

28. **VARIABLE_NAMING_CONSTRAINTS.md**
    - Variable naming constraints in contracts
    - Enforcement mechanisms

### Property System

29. **PROPERTY_TRANSFORMATION_MAPPING.md**
    - Property-to-transformation mappings
    - Transformation strategies

30. **SKYT_COMPLETE_OVERVIEW.md**
    - Complete system overview
    - Architecture and components

---

## 📅 Experimental Plans (Archive)

31. **TODAYS_EXPERIMENTAL_PLAN.md**
    - Daily experimental planning
    - Ad-hoc experiments

---

## 🗂️ File Organization Recommendations

### Keep in Root (Essential)
```
README.md
DISTANCE_METRICS.md
STATISTICAL_METHODS.md
LIMITATIONS.md
DISCUSSION_CAMERA_READY.md
CROSS_MODEL_SUPPORT.md
MULTI_FILE_ROADMAP.md
REVIEWER_RESPONSES.md
DOCUMENTATION_INDEX.md (this file)
```

### Move to docs/ (Reference)
```
IMPLEMENTATION_COMPLETE.md
METRICS_IMPLEMENTATION.md
FINAL_TRANSFORMATION_REPORT.md
VALIDATION_RESULTS.md
PHASE2_COMPLETION_REPORT.md
PHASE3_VALIDATION_RESULTS.md
PHASE4_VALIDATION_RESULTS.md
QUICK_START_METRICS.md
README_metrics.md
SKYT_COMPLETE_OVERVIEW.md
```

### Move to docs/archive/ (Historical)
```
TRANSFORMATION_IMPLEMENTATION_PLAN.md
PROPERTY_MAPPING_IMPLEMENTATION_PLAN.md
TRANSFORMATION_VALIDATION_CHECKLIST.md
INCOMPLETE_TRANSFORMATIONS_ANALYSIS.md
DELTA_RESCUE_ROOT_CAUSE.md
DEBUG_CHECKLIST_STATUS.md
OOD_QUICK_REFERENCE.md
OUT_OF_DOMAIN_POLICY.md
OOD_IMPLEMENTATION_SUMMARY.md
CONTRACT_AWARE_VALIDATION.md
VARIABLE_NAMING_CONSTRAINTS.md
PROPERTY_TRANSFORMATION_MAPPING.md
TODAYS_EXPERIMENTAL_PLAN.md
```

---

## 📖 Usage Guide

### For Paper Writing

**Refer to these documents:**
1. DISTANCE_METRICS.md - Methods section (distance metric justification)
2. STATISTICAL_METHODS.md - Statistical analysis section
3. LIMITATIONS.md - Threats to validity section
4. DISCUSSION_CAMERA_READY.md - Discussion section
5. REVIEWER_RESPONSES.md - Addressing reviewer comments

### For Code Understanding

**Refer to these documents:**
1. README.md - Quick start
2. IMPLEMENTATION_COMPLETE.md - System architecture
3. METRICS_IMPLEMENTATION.md - Metrics calculation
4. SKYT_COMPLETE_OVERVIEW.md - Complete overview

### For Future Development

**Refer to these documents:**
1. MULTI_FILE_ROADMAP.md - Multi-file support plan
2. LIMITATIONS.md - Known limitations and future work
3. TRANSFORMATION_IMPLEMENTATION_PLAN.md - Transformation system design

---

## 🎯 Camera-Ready Checklist

### Documentation Status

- ✅ Distance metrics explained (DISTANCE_METRICS.md)
- ✅ Statistical methods documented (STATISTICAL_METHODS.md)
- ✅ Limitations acknowledged (LIMITATIONS.md)
- ✅ N-Version comparison (DISCUSSION_CAMERA_READY.md)
- ✅ Multi-model support (CROSS_MODEL_SUPPORT.md)
- ✅ Multi-file roadmap (MULTI_FILE_ROADMAP.md)
- ✅ Reviewer responses mapped (REVIEWER_RESPONSES.md)

### Remaining Tasks

- ⏳ Run full experiments (3,600 generations)
- ⏳ Create replication package (Zenodo)
- ⏳ Verify anonymous repository link
- ⏳ Fix "monotonicity check" header in paper

---

## 📞 Contact

**Author:** Heitor Roriz Filho  
**Institution:** [Your Institution]  
**Email:** [Your Email]  
**Repository:** https://github.com/HeitorRoriz/skyt_experiment

---

**Note:** Documents marked with ⭐ are essential for camera-ready submission and should be referenced in the paper.
