# Talent Matching Algorithm

## Overview

The Talent Matching Engine uses a benchmark-driven approach to match employees with positions or compare them against high-performer profiles.

## Core Concept

The engine compares all employees against a **benchmark group** - a set of reference employees (typically high performers) selected based on user input. This benchmark establishes the ideal profile for scoring and comparison.

---

## Operating Modes

### Mode A: Position Recommendations (Toggle OFF)
**Purpose:** Find best position matches for specific employees

**Configuration:**
- Select specific employees
- Toggle: OFF
- Output: Ranked position recommendations for each selected employee

### Mode A: Manual Benchmark (Toggle ON)
**Purpose:** Use selected employees as the benchmark and rank all other employees

**Configuration:**
- Select benchmark employees  
- Toggle: ON
- Output: All employees ranked by similarity to selected benchmark

### Mode B: Filter-Based Benchmark
**Purpose:** Create benchmark from high performers matching specific criteria

**Configuration:**
- No manual selection
- Apply filters (position, department, division, grade)
- Output: All employees ranked against filtered high-performer benchmark

### Default Mode
**Purpose:** Use all high performers as benchmark

**Configuration:**
- No manual selection
- No filters applied
- Output: All employees ranked against all high performers (rating ≥ 5)

---

## Scoring Methodology

The scoring system uses a three-level hierarchy:

### Level 1: Variable Match Rate (tv_match_rate)

Compares individual variables against benchmark baseline:

**Numeric Variables** (Competencies, IQ, GTQ):
```
match_rate = (employee_score / baseline_score) × 100
```

**Reverse-Scored Variables** (PAPI I, K, Z, T):
```
match_rate = ((2 × baseline_score - employee_score) / baseline_score) × 100
```

**Categorical Variables** (MBTI, DISC):
- Match: 100
- No match: 0

### Level 2: Group Match Rate (tgv_match_rate)

Weighted average of related variables:
```
group_match_rate = Σ(tv_match_rate × tv_weight) / Σ(tv_weight)
```

### Level 3: Final Match Rate

Weighted sum across all groups:
```
final_match_rate = Σ(tgv_match_rate × tgv_weight)
```

---

## Benchmark Priority

The system determines benchmarks in this order:

1. **Manual Selection (Toggle ON)** → Uses selected employees
2. **Filter-Based** → Uses high performers matching filters
3. **Default** → Uses all high performers (rating ≥ 5)

---

## Technical Implementation

The algorithm is implemented using a SQL pipeline with Common Table Expressions (CTEs):

- `params` - Input parameters
- `manual_set` - Manually selected employees
- `filter_based_set` - Employees matching filters
- `fallback_benchmark` - Default high performers
- `final_bench` - Final benchmark determination
- `baseline_*` - Baseline calculations
- `*_tv` - Variable-level scoring
- `tgv_match` - Group-level scoring
- `final_match` - Final scoring
- `final_results` - Output generation

---

## Key Rules

1. **No Hybrid Modes** - Each mode operates independently
2. **Benchmark Consistency** - All baselines derived from `final_bench` only
3. **No Result Filtering** - SQL returns all employees; filtering happens in UI
4. **Fallback Required** - System always maintains a valid baseline

---

For database schema details, see `SQL-scheme.md`.
For SQL implementation details, see `SQL_ENGINE_TEMPLATE.sql`.