# Today's Experimental Plan - Improving Δ_rescue

## 📊 Yesterday's Baseline Results

### Algorithm Performance
| Algorithm | Temp | R_raw | R_anchor(pre) | Δ_rescue | Status |
|-----------|------|-------|---------------|----------|--------|
| **Slugify** | 0.5 | 0.500 | 0.100 | **0.800** | ✅ EXCELLENT |
| Fibonacci Basic | 0.5 | 0.600 | 0.800 | 0.200 | ⚠️ MODERATE |
| Fibonacci Recursive | 0.3 | 1.000 | 1.000 | 0.000 | ❌ NO DIVERSITY |

### Key Observations
1. **Slugify shows SKYT works** - 80% improvement from transformations
2. **Fibonacci has potential** - Only 20% improvement, could be much higher
3. **Temperature matters** - Temp 0.3 too low (100% identical), need 0.5-0.7
4. **Error handling is key** - LLMs generate diverse error handling patterns

---

## 🎯 Today's Goals

### Primary Goal
**Increase Δ_rescue from 0.200 → 0.500+ for Fibonacci** using OOD policy normalization

### Secondary Goals
1. Validate OOD policy system improves real experiments
2. Identify remaining transformation gaps
3. Generate publication-ready results

---

## 🔬 Experimental Protocol

### Experiment 1: Fibonacci with OOD Normalization

**Hypothesis**: OOD policy will normalize error handling, increasing Δ_rescue by 30-50%

**Setup:**
- Contract: `fibonacci_basic` (updated with `must_return: 0` policy)
- Temperatures: 0.5, 0.7
- Runs: 10 per temperature
- OOD Policy: `must_return` with `return_value: 0`

**Commands:**
```bash
# Temperature 0.5
python main.py --contract fibonacci_basic --runs 10 --temperature 0.5 --output-dir results/fib_ood_t05

# Temperature 0.7 (higher diversity)
python main.py --contract fibonacci_basic --runs 10 --temperature 0.7 --output-dir results/fib_ood_t07
```

**Expected Outcomes:**
- **Before OOD**: Some runs have `raise ValueError`, others `return 0` → high distance
- **After OOD**: Transformation normalizes all to `return 0` → low distance
- **Predicted Δ_rescue**: 0.400-0.600 (vs 0.200 yesterday)

---

### Experiment 2: Fibonacci Recursive with OOD

**Hypothesis**: Recursive fibonacci needs higher temperature to show diversity

**Setup:**
- Contract: `fibonacci_recursive` (updated with `must_return: 0` policy)
- Temperatures: 0.5, 0.7 (higher than yesterday's 0.3)
- Runs: 10 per temperature

**Commands:**
```bash
# Temperature 0.5
python main.py --contract fibonacci_recursive --runs 10 --temperature 0.5 --output-dir results/fib_rec_ood_t05

# Temperature 0.7
python main.py --contract fibonacci_recursive --runs 10 --temperature 0.7 --output-dir results/fib_rec_ood_t07
```

**Expected Outcomes:**
- Higher temps → more diverse base case handling
- OOD policy normalizes `n < 0` handling
- **Predicted Δ_rescue**: 0.300-0.500

---

### Experiment 3: Slugify Replication (Control)

**Hypothesis**: Slugify results should be reproducible

**Setup:**
- Contract: `slugify` (no changes needed - already working)
- Temperature: 0.5 (same as yesterday)
- Runs: 10

**Commands:**
```bash
python main.py --contract slugify --runs 10 --temperature 0.5 --output-dir results/slugify_control
```

**Expected Outcomes:**
- **Should replicate**: Δ_rescue ≈ 0.800
- Validates system stability

---

### Experiment 4: Failure Analysis

**Identify what's NOT being transformed:**

```bash
python analyze_failures.py
```

**Outputs:**
- Common patterns in failed transformations
- Recommendations for new transformation rules
- Specific code snippets that need attention

---

## 📈 Success Metrics

### Tier 1 Success (Minimum Viable)
- ✅ Fibonacci Δ_rescue > 0.400 (up from 0.200)
- ✅ OOD policies enforce normalization
- ✅ No regressions on slugify

### Tier 2 Success (Target)
- ✅ Fibonacci Δ_rescue > 0.500
- ✅ Fibonacci Recursive Δ_rescue > 0.300
- ✅ Clear evidence OOD policies work

### Tier 3 Success (Stretch)
- ✅ Fibonacci Δ_rescue > 0.700 (approaching slugify)
- ✅ All algorithms show > 0.500 improvement
- ✅ Publication-ready graphs

---

## 🔧 Technical Changes Made

### 1. Updated Contracts (DONE ✅)
- `fibonacci_basic`: Changed OOD policy from "allow" → "must_return: 0"
- `fibonacci_recursive`: Added OOD policy "must_return: 0"
- Both now enforce canonical error handling

### 2. Analysis Tools (DONE ✅)
- Created `analyze_failures.py` to identify transformation gaps
- Automated pattern detection for common failures

---

## ⏱️ Timeline

**Morning (2-3 hours):**
1. ✅ Update contracts (DONE)
2. Run Experiment 1 (fibonacci_basic, 2 temps) - 30 min
3. Run Experiment 2 (fibonacci_recursive, 2 temps) - 30 min
4. Run Experiment 3 (slugify control) - 15 min

**Afternoon (2-3 hours):**
5. Run failure analysis - 15 min
6. Analyze results and generate graphs - 1 hour
7. Compare with/without OOD policies - 1 hour
8. Document findings - 30 min

---

## 📊 Analysis Checklist

After experiments complete:

### 1. Quantitative Analysis
- [ ] Calculate Δ_rescue for all experiments
- [ ] Compare with/without OOD policies
- [ ] Generate histogram plots
- [ ] Statistical significance tests

### 2. Qualitative Analysis
- [ ] Inspect transformed code samples
- [ ] Verify OOD normalization working
- [ ] Identify remaining transformation gaps
- [ ] Document edge cases

### 3. Visualizations
- [ ] Distance plots (before/after transformation)
- [ ] Δ_rescue comparison charts
- [ ] Transformation success rates
- [ ] Error handling diversity analysis

---

## 🎯 Expected Improvements

### Why This Will Work

**Problem Yesterday:**
```python
# Run 1: LLM generates this
if n < 0:
    raise ValueError("negative")
# Canon distance: 0.0

# Run 2: LLM generates this  
if n < 0:
    return 0
# Canon distance: 0.288 (different from Run 1!)
```

**Solution Today:**
```python
# Run 1: Generated code
if n < 0:
    raise ValueError("negative")
    
# Run 1: After OOD transformation
if n < 0:
    return 0  # Normalized!
# Canon distance: 0.0

# Run 2: Generated code
if n < 0:
    return 0
    
# Run 2: After OOD transformation  
if n < 0:
    return 0  # Already canonical
# Canon distance: 0.0

# Both converge! Δ_rescue improved!
```

---

## 🚨 Potential Issues & Mitigation

### Issue 1: OOD Policy Too Strict
**Symptom**: Transformations rejected
**Mitigation**: Check validation logs, may need to relax to "forbid_transform"

### Issue 2: Not Enough Diversity
**Symptom**: R_raw still too high (>0.8)
**Mitigation**: Increase temperature to 0.7 or 0.9

### Issue 3: Transformations Still Failing
**Symptom**: Δ_rescue not improving
**Mitigation**: Run `analyze_failures.py`, add missing transformation rules

---

## 📝 Documentation to Update

After experiments:

1. **Results Summary** - New Δ_rescue numbers
2. **OOD Policy Validation** - Evidence system works
3. **Publication Figures** - Comparison graphs
4. **Future Work** - Identified gaps and next steps

---

## 🎉 Success Indicators

**By end of day, we should have:**

✅ **Concrete Evidence**: OOD policies improve Δ_rescue by 30-50%
✅ **Reproducible Results**: Slugify control matches yesterday
✅ **Publication-Ready Data**: 3 algorithms, multiple temps, clear improvements
✅ **Identified Gaps**: List of remaining transformation challenges
✅ **System Validation**: OOD policy system works in real experiments

---

## 🚀 Next Steps After Today

**If successful:**
1. Add more OOD policies to other contracts
2. Publish results showing SKYT effectiveness
3. Extend to more complex algorithms

**If issues found:**
1. Debug specific transformation failures
2. Add missing transformation rules
3. Refine OOD policies

---

**Status**: Ready to execute
**Estimated Time**: 4-6 hours
**Risk Level**: Low (backward compatible, tested)
**Expected Impact**: High (30-50% Δ_rescue improvement)
