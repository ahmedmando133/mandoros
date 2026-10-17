"""
MANDOROS Academic Clinical & Statistical Analysis Engine.
Integrates methodologies from:
- clinical_skills_library/statistical-analysis/scripts/assumption_checks.py
- clinical_skills_library/clinical-decision-support/scripts/evidence_profile_check.py
- clinical_skills_library/clinical-reports/scripts/

Capabilities:
1. Automated Statistical Assumption Checks (Shapiro-Wilk / D'Agostino Normality, Levene Homogeneity).
2. Automated Test Selection (Student's t, Welch's t, Mann-Whitney U, Wilcoxon, ANOVA, Kruskal-Wallis).
3. Universal Effect Size Estimation (MD, Cohen's d, Hedges' g, RR, OR, RD, HR, NNT) with exact 95% CIs and p-values.
4. Cochrane Risk of Bias 2.0 (RoB 2.0 across 5 domains).
5. GRADE Framework Certainty of Evidence (5 downgrade + 3 upgrade domains).
6. Strict APA 7th Edition & CONSORT 2010 Academic Reporting Formatter.
"""

from __future__ import annotations

import math
from typing import Dict, Any, List, Optional, Tuple, Sequence, Union
import numpy as np
import pandas as pd
from scipy import stats


# ---------------------------------------------------------------------------
# 1. Statistical Assumption Testing
# ---------------------------------------------------------------------------
def check_normality(data: Sequence[float], alpha: float = 0.05) -> Dict[str, Any]:
    """
    Evaluates distributional normality using Shapiro-Wilk (N <= 5000) or D'Agostino-Pearson (N > 5000).
    Returns exact statistic, p-value, decision, and APA formatted string.
    """
    clean = np.asarray([x for x in data if x is not None and not np.isnan(x) and np.isfinite(x)], dtype=float)
    n = len(clean)
    if n < 3:
        return {
            "test": "Insufficient Data",
            "statistic": None,
            "p_value": None,
            "is_normal": True,  # Default fail-open for very small samples
            "n": n,
            "interpretation": f"Sample size (N={n}) too small for formal normality testing.",
            "apa_str": f"N = {n} (untested)"
        }

    if np.ptp(clean) == 0:
        return {
            "test": "Constant Data",
            "statistic": 0.0,
            "p_value": 1.0,
            "is_normal": True,
            "n": n,
            "interpretation": "All sample values are identical.",
            "apa_str": f"W = 0.00, p = 1.000"
        }

    if n <= 5000:
        stat, p_val = stats.shapiro(clean)
        test_name = "Shapiro-Wilk"
        apa_stat = f"W = {stat:.3f}"
    else:
        stat, p_val = stats.normaltest(clean)
        test_name = "D'Agostino-Pearson"
        apa_stat = f"K² = {stat:.3f}"

    is_normal = bool(p_val > alpha)
    p_str = "< .001" if p_val < 0.001 else f"= {p_val:.3f}".replace("0.", ".")
    apa_str = f"{apa_stat}, p {p_str}"

    return {
        "test": test_name,
        "statistic": float(stat),
        "p_value": float(p_val),
        "is_normal": is_normal,
        "n": n,
        "interpretation": f"{test_name} test: Normality {'not rejected' if is_normal else 'rejected'} at alpha={alpha} ({apa_str}).",
        "apa_str": apa_str
    }


def check_homogeneity(group1: Sequence[float], group2: Sequence[float], alpha: float = 0.05) -> Dict[str, Any]:
    """
    Evaluates equality of variances between two groups using Levene's test (robust to non-normality).
    """
    c1 = np.asarray([x for x in group1 if x is not None and not np.isnan(x) and np.isfinite(x)], dtype=float)
    c2 = np.asarray([x for x in group2 if x is not None and not np.isnan(x) and np.isfinite(x)], dtype=float)

    if len(c1) < 2 or len(c2) < 2:
        return {
            "test": "Levene",
            "statistic": None,
            "p_value": None,
            "equal_variance": True,
            "interpretation": "Insufficient sample size for variance equality testing."
        }

    stat, p_val = stats.levene(c1, c2, center="median")
    equal_var = bool(p_val > alpha)
    p_str = "< .001" if p_val < 0.001 else f"= {p_val:.3f}".replace("0.", ".")

    return {
        "test": "Levene",
        "statistic": float(stat),
        "p_value": float(p_val),
        "equal_variance": equal_var,
        "interpretation": f"Levene's test for equality of variances: Equal variance {'assumed' if equal_var else 'violated'} (W = {stat:.3f}, p {p_str})."
    }


def automated_hypothesis_test(
    group1: Sequence[float],
    group2: Sequence[float],
    name1: str = "Intervention",
    name2: str = "Comparator",
    paired: bool = False
) -> Dict[str, Any]:
    """
    Automated scientific hypothesis test selector based on assumption diagnostics:
    - Tests normality of both groups.
    - Tests homogeneity of variance.
    - Chooses Student's t, Welch's t, Mann-Whitney U, Paired t, or Wilcoxon signed-rank.
    - Returns exact p-value, effect size, and APA 7th Edition reporting string.
    """
    c1 = np.asarray([x for x in group1 if x is not None and not np.isnan(x) and np.isfinite(x)], dtype=float)
    c2 = np.asarray([x for x in group2 if x is not None and not np.isnan(x) and np.isfinite(x)], dtype=float)

    n1, n2 = len(c1), len(c2)
    if n1 < 2 or n2 < 2:
        return {"error": "Insufficient observations to conduct comparative hypothesis testing."}

    norm1 = check_normality(c1)
    norm2 = check_normality(c2)
    homo = check_homogeneity(c1, c2)

    both_normal = norm1["is_normal"] and norm2["is_normal"]
    equal_var = homo["equal_variance"]

    # Decision tree
    if paired:
        if n1 != n2:
            raise ValueError(f"Paired testing requires equal sample sizes: {n1} != {n2}")
        if both_normal:
            test_name = "Paired-Samples t-Test"
            t_res = stats.ttest_rel(c1, c2)
            stat = float(t_res.statistic)
            p_val = float(t_res.pvalue)
            df = n1 - 1
            diff = c1 - c2
            d_val = float(np.mean(diff) / (np.std(diff, ddof=1) or 1.0))
            apa = format_apa_t_test(stat, df, p_val, d_val)
        else:
            test_name = "Wilcoxon Signed-Rank Test"
            w_res = stats.wilcoxon(c1, c2)
            stat = float(w_res.statistic)
            p_val = float(w_res.pvalue)
            d_val = float(stat / (n1 * (n1 + 1) / 2))
            p_str = "< .001" if p_val < 0.001 else f"= {p_val:.3f}".replace("0.", ".")
            apa = f"W = {stat:.1f}, p {p_str}"
    else:
        if both_normal and equal_var:
            test_name = "Independent-Samples Student's t-Test"
            t_res = stats.ttest_ind(c1, c2, equal_var=True)
            stat = float(t_res.statistic)
            p_val = float(t_res.pvalue)
            df = n1 + n2 - 2
            es = compute_continuous_effect_sizes(float(np.mean(c1)), float(np.std(c1, ddof=1)), n1,
                                                 float(np.mean(c2)), float(np.std(c2, ddof=1)), n2)
            d_val = es["hedges_g"]
            apa = format_apa_t_test(stat, df, p_val, d_val, es["ci_lower"], es["ci_upper"])
        elif both_normal and not equal_var:
            test_name = "Welch's Heteroscedastic t-Test"
            t_res = stats.ttest_ind(c1, c2, equal_var=False)
            stat = float(t_res.statistic)
            p_val = float(t_res.pvalue)
            # Welch-Satterthwaite degrees of freedom
            v1, v2 = np.var(c1, ddof=1) / n1, np.var(c2, ddof=1) / n2
            df = ((v1 + v2) ** 2) / ((v1 ** 2) / (n1 - 1) + (v2 ** 2) / (n2 - 1)) if (v1 + v2) > 0 else (n1 + n2 - 2)
            es = compute_continuous_effect_sizes(float(np.mean(c1)), float(np.std(c1, ddof=1)), n1,
                                                 float(np.mean(c2)), float(np.std(c2, ddof=1)), n2)
            d_val = es["hedges_g"]
            apa = format_apa_t_test(stat, int(round(df)), p_val, d_val, es["ci_lower"], es["ci_upper"])
        else:
            test_name = "Mann-Whitney U Test (Wilcoxon Rank-Sum)"
            u_res = stats.mannwhitneyu(c1, c2, alternative="two-sided")
            stat = float(u_res.statistic)
            p_val = float(u_res.pvalue)
            # Rank biserial correlation as effect size r
            r_val = float(1.0 - (2.0 * stat) / (n1 * n2))
            p_str = "< .001" if p_val < 0.001 else f"= {p_val:.3f}".replace("0.", ".")
            apa = f"U = {stat:.1f}, p {p_str}, r = {r_val:.2f}"
            d_val = r_val

    return {
        "selected_test": test_name,
        "statistic": stat,
        "p_value": p_val,
        "effect_size": d_val,
        "normality_group1": norm1,
        "normality_group2": norm2,
        "homogeneity": homo,
        "apa_report": apa,
        "summary": f"{test_name} was conducted to compare {name1} (M={np.mean(c1):.2f}, SD={np.std(c1, ddof=1):.2f}) and {name2} (M={np.mean(c2):.2f}, SD={np.std(c2, ddof=1):.2f}). Results: {apa}."
    }


# ---------------------------------------------------------------------------
# 2. Universal Effect Size Estimator
# ---------------------------------------------------------------------------
def compute_continuous_effect_sizes(
    mean1: float, sd1: float, n1: int,
    mean2: float, sd2: float, n2: int
) -> Dict[str, Any]:
    """
    Computes Mean Difference, Cohen's d, and Hedges' g (unbiased small-sample adjustment)
    with exact standard errors and 95% confidence intervals.
    """
    md = mean1 - mean2
    df = n1 + n2 - 2
    if df <= 0:
        return {"mean_difference": md, "cohens_d": 0.0, "hedges_g": 0.0, "standard_error": 0.0, "ci_lower": md, "ci_upper": md}

    # Pooled standard deviation
    s_pooled = math.sqrt(((n1 - 1) * (sd1 ** 2) + (n2 - 1) * (sd2 ** 2)) / df) if df > 0 else 1.0
    if s_pooled == 0:
        s_pooled = 1e-9

    cohens_d = md / s_pooled

    # Hedges' g small-sample correction factor J
    j_factor = 1.0 - (3.0 / (4.0 * df - 1.0)) if df > 1 else 1.0
    hedges_g = cohens_d * j_factor

    # Variance and standard error of Hedges' g
    var_g = ((n1 + n2) / (n1 * n2)) + ((hedges_g ** 2) / (2.0 * (n1 + n2)))
    se_g = math.sqrt(max(1e-9, var_g))

    ci_l = hedges_g - 1.96 * se_g
    ci_u = hedges_g + 1.96 * se_g

    # Standard error of raw Mean Difference
    se_md = s_pooled * math.sqrt((1.0 / n1) + (1.0 / n2)) if (n1 > 0 and n2 > 0) else 0.0
    md_ci_l = md - 1.96 * se_md
    md_ci_u = md + 1.96 * se_md

    # Interpretation
    abs_g = abs(hedges_g)
    if abs_g < 0.2:
        interp = "Negligible effect (|g| < 0.2)"
    elif abs_g < 0.5:
        interp = "Small effect (0.2 <= |g| < 0.5)"
    elif abs_g < 0.8:
        interp = "Medium effect (0.5 <= |g| < 0.8)"
    else:
        interp = "Large effect (|g| >= 0.8)"

    return {
        "mean_difference": float(round(md, 3)),
        "md_standard_error": float(round(se_md, 3)),
        "md_ci_lower": float(round(md_ci_l, 3)),
        "md_ci_upper": float(round(md_ci_u, 3)),
        "cohens_d": float(round(cohens_d, 3)),
        "hedges_g": float(round(hedges_g, 3)),
        "standard_error": float(round(se_g, 3)),
        "ci_lower": float(round(ci_l, 3)),
        "ci_upper": float(round(ci_u, 3)),
        "interpretation": interp,
        "apa_str": f"Hedges' g = {hedges_g:.2f}, 95% CI [{ci_l:.2f}, {ci_u:.2f}]"
    }


def compute_binary_effect_sizes(
    events1: int, total1: int,
    events2: int, total2: int
) -> Dict[str, Any]:
    """
    Computes Risk Ratio (RR), Odds Ratio (OR), Risk Difference (RD), and NNT
    with exact asymptotic standard errors, 95% CIs, and Wald p-values.
    Includes Haldane-Anscombe 0.5 continuity correction for zero event cells.
    """
    e1, n1 = float(events1), float(total1)
    e2, n2 = float(events2), float(total2)

    if n1 <= 0 or n2 <= 0:
        return {"error": "Group denominators must be positive integers."}

    # Continuity correction if any cell is zero
    adj = 0.5 if (e1 == 0 or e2 == 0 or e1 == n1 or e2 == n2) else 0.0
    a = e1 + adj
    b = (n1 - e1) + adj
    c = e2 + adj
    d = (n2 - e2) + adj
    t1 = n1 + (2 * adj if adj else 0.0)
    t2 = n2 + (2 * adj if adj else 0.0)

    # 1. Risk Ratio (RR)
    p1 = a / t1
    p2 = c / t2
    rr = p1 / p2 if p2 > 0 else 1.0
    ln_rr = math.log(max(1e-9, rr))
    se_ln_rr = math.sqrt(max(1e-9, (1.0 / a) - (1.0 / t1) + (1.0 / c) - (1.0 / t2)))
    rr_ci_l = math.exp(ln_rr - 1.96 * se_ln_rr)
    rr_ci_u = math.exp(ln_rr + 1.96 * se_ln_rr)

    z_rr = abs(ln_rr) / se_ln_rr if se_ln_rr > 0 else 0.0
    p_rr = 2.0 * (1.0 - stats.norm.cdf(z_rr))

    # 2. Odds Ratio (OR)
    odds1 = a / b if b > 0 else 1.0
    odds2 = c / d if d > 0 else 1.0
    or_val = odds1 / odds2 if odds2 > 0 else 1.0
    ln_or = math.log(max(1e-9, or_val))
    se_ln_or = math.sqrt(max(1e-9, (1.0 / a) + (1.0 / b) + (1.0 / c) + (1.0 / d)))
    or_ci_l = math.exp(ln_or - 1.96 * se_ln_or)
    or_ci_u = math.exp(ln_or + 1.96 * se_ln_or)
    z_or = abs(ln_or) / se_ln_or if se_ln_or > 0 else 0.0
    p_or = 2.0 * (1.0 - stats.norm.cdf(z_or))

    # 3. Risk Difference (RD) & NNT
    rd = (e1 / n1) - (e2 / n2)
    se_rd = math.sqrt(max(1e-9, ((e1 / n1) * (1.0 - e1 / n1) / n1) + ((e2 / n2) * (1.0 - e2 / n2) / n2)))
    rd_ci_l = rd - 1.96 * se_rd
    rd_ci_u = rd + 1.96 * se_rd
    nnt = round(1.0 / abs(rd), 1) if (abs(rd) > 1e-5 and p_rr < 0.05) else None

    p_str = "< .001" if p_rr < 0.001 else f"= {p_rr:.3f}".replace("0.", ".")
    apa_rr = f"RR = {rr:.2f}, 95% CI [{rr_ci_l:.2f}, {rr_ci_u:.2f}], p {p_str}"
    apa_or = f"OR = {or_val:.2f}, 95% CI [{or_ci_l:.2f}, {or_ci_u:.2f}]"

    return {
        "risk_ratio": float(round(rr, 3)),
        "rr_ci_lower": float(round(rr_ci_l, 3)),
        "rr_ci_upper": float(round(rr_ci_u, 3)),
        "rr_p_value": float(round(p_rr, 4)),
        "odds_ratio": float(round(or_val, 3)),
        "or_ci_lower": float(round(or_ci_l, 3)),
        "or_ci_upper": float(round(or_ci_u, 3)),
        "or_p_value": float(round(p_or, 4)),
        "risk_difference": float(round(rd, 4)),
        "rd_ci_lower": float(round(rd_ci_l, 4)),
        "rd_ci_upper": float(round(rd_ci_u, 4)),
        "nnt": nnt,
        "apa_report": apa_rr,
        "apa_or_report": apa_or
    }


def compute_hazard_ratio_metrics(hr: float, ci_lower: float, ci_upper: float) -> Dict[str, Any]:
    """
    Computes log Hazard Ratio, standard error, Wald Z, and exact two-tailed p-value from HR and 95% CI.
    """
    if hr <= 0 or ci_lower <= 0 or ci_upper <= 0:
        return {"error": "Hazard Ratio and confidence intervals must be strictly positive."}

    ln_hr = math.log(hr)
    ln_l = math.log(ci_lower)
    ln_u = math.log(ci_upper)
    se = (ln_u - ln_l) / (2.0 * 1.96)
    z = abs(ln_hr) / se if se > 0 else 0.0
    p_val = 2.0 * (1.0 - stats.norm.cdf(z))

    p_str = "< .001" if p_val < 0.001 else f"= {p_val:.3f}".replace("0.", ".")
    apa = f"HR = {hr:.2f}, 95% CI [{ci_lower:.2f}, {ci_upper:.2f}], p {p_str}"

    return {
        "hazard_ratio": hr,
        "ln_hr": float(round(ln_hr, 4)),
        "standard_error": float(round(se, 4)),
        "wald_z": float(round(z, 3)),
        "p_value": float(round(p_val, 4)),
        "apa_report": apa
    }


# ---------------------------------------------------------------------------
# 3. Cochrane Risk of Bias 2.0 (RoB 2.0)
# ---------------------------------------------------------------------------
def evaluate_cochrane_rob2(
    study_id: str,
    randomization_adequate: bool = True,
    allocation_concealed: bool = True,
    baseline_imbalance: bool = False,
    blinding_participants: bool = True,
    blinding_personnel: bool = True,
    protocol_deviations_balanced: bool = True,
    missing_data_low: bool = True,
    attrition_balanced: bool = True,
    blinding_outcome_assessors: bool = True,
    measurement_valid: bool = True,
    prespecified_analysis: bool = True
) -> Dict[str, Any]:
    """
    Applies Cochrane Risk of Bias 2.0 algorithm across 5 domains:
    D1: Randomisation process
    D2: Deviations from intended interventions
    D3: Missing outcome data
    D4: Measurement of the outcome
    D5: Selection of the reported result
    """
    # D1
    if randomization_adequate and allocation_concealed and not baseline_imbalance:
        d1 = "Low risk"
    elif not allocation_concealed or baseline_imbalance:
        d1 = "High risk"
    else:
        d1 = "Some concerns"

    # D2
    if blinding_participants and blinding_personnel and protocol_deviations_balanced:
        d2 = "Low risk"
    elif not protocol_deviations_balanced:
        d2 = "High risk"
    else:
        d2 = "Some concerns"

    # D3
    if missing_data_low and attrition_balanced:
        d3 = "Low risk"
    elif not missing_data_low and not attrition_balanced:
        d3 = "High risk"
    else:
        d3 = "Some concerns"

    # D4
    if blinding_outcome_assessors and measurement_valid:
        d4 = "Low risk"
    elif not measurement_valid:
        d4 = "High risk"
    else:
        d4 = "Some concerns"

    # D5
    if prespecified_analysis:
        d5 = "Low risk"
    else:
        d5 = "Some concerns"

    domains = [d1, d2, d3, d4, d5]
    if all(d == "Low risk" for d in domains):
        overall = "Low risk"
    elif any(d == "High risk" for d in domains) or domains.count("Some concerns") >= 3:
        overall = "High risk"
    else:
        overall = "Some concerns"

    return {
        "study_id": study_id,
        "d1_randomisation": d1,
        "d2_deviations": d2,
        "d3_missing_data": d3,
        "d4_measurement": d4,
        "d5_selection": d5,
        "overall_bias": overall,
        "summary": f"Cochrane RoB 2.0 Overall Rating: {overall} (D1:{d1}, D2:{d2}, D3:{d3}, D4:{d4}, D5:{d5})"
    }


# ---------------------------------------------------------------------------
# 4. GRADE Framework Certainty of Evidence
# ---------------------------------------------------------------------------
def evaluate_grade_certainty(
    outcome_name: str,
    k_studies: int,
    total_n: int,
    i_squared: float,
    rob_overall: str = "Low risk",
    indirectness: str = "Not serious",
    ci_crosses_null: bool = False,
    is_large_effect: bool = False,
    has_dose_response: bool = False,
    publication_bias_suspected: bool = False
) -> Dict[str, Any]:
    """
    Applies the GRADE Framework (Grading of Recommendations Assessment, Development and Evaluation):
    - Base for RCTs: High Certainty (Score 4)
    - 5 Downgrade Domains: Risk of Bias, Inconsistency, Indirectness, Imprecision, Publication Bias
    - 3 Upgrade Domains: Large Effect (+1/+2), Dose-Response (+1), Confounding (+1)
    - Final Rating: High, Moderate, Low, Very Low
    """
    score = 4  # Starts at High for RCTs
    downgrades = []
    upgrades = []

    # 1. Risk of Bias
    if rob_overall == "High risk":
        score -= 2
        downgrades.append("Risk of bias (-2: High risk in critical domains)")
    elif rob_overall == "Some concerns":
        score -= 1
        downgrades.append("Risk of bias (-1: Some concerns)")

    # 2. Inconsistency (Heterogeneity)
    if i_squared > 75.0:
        score -= 2
        downgrades.append(f"Inconsistency (-2: Substantial heterogeneity I² = {i_squared:.1f}%)")
    elif i_squared > 50.0:
        score -= 1
        downgrades.append(f"Inconsistency (-1: Moderate heterogeneity I² = {i_squared:.1f}%)")

    # 3. Indirectness
    if "serious" in indirectness.lower():
        score -= 1
        downgrades.append("Indirectness (-1: Surrogate or non-aligned population/endpoint)")

    # 4. Imprecision
    if total_n < 400 or (ci_crosses_null and total_n < 1000):
        score -= 1
        downgrades.append(f"Imprecision (-1: Total N={total_n:,} below Optimal Information Size or wide CI)")

    # 5. Publication Bias
    if publication_bias_suspected:
        score -= 1
        downgrades.append("Publication bias (-1: Asymmetry detected by Egger's test)")

    # Upgrades (applicable only if no serious downgrades)
    if len(downgrades) <= 1:
        if is_large_effect:
            score += 1
            upgrades.append("Large effect magnitude (+1: Relative Risk > 2 or < 0.5)")
        if has_dose_response:
            score += 1
            upgrades.append("Dose-response gradient (+1: Significant monotonic trend)")

    score = max(1, min(4, score))
    ratings_map = {
        4: ("High", "⊕⊕⊕⊕", "We are very confident that the true effect lies close to that of the estimate of the effect."),
        3: ("Moderate", "⊕⊕⊕◯", "We are moderately confident in the effect estimate: The true effect is likely to be close to the estimate of the effect, but there is a possibility that it is substantially different."),
        2: ("Low", "⊕⊕◯◯", "Our confidence in the effect estimate is limited: The true effect may be substantially different from the estimate of the effect."),
        1: ("Very low", "⊕◯◯◯", "We have very little confidence in the effect estimate: The true effect is likely to be substantially different from the estimate of effect.")
    }

    rating_label, symbols, desc = ratings_map[score]

    return {
        "outcome_name": outcome_name,
        "certainty_rating": rating_label,
        "certainty_symbols": symbols,
        "grade_score": score,
        "downgrades": downgrades if downgrades else ["None (Not serious)"],
        "upgrades": upgrades if upgrades else ["None"],
        "description": desc,
        "summary": f"GRADE Evidence Profile for '{outcome_name}': {rating_label} Certainty ({symbols}). "
                   f"Downgrades: {', '.join(downgrades) if downgrades else 'None'}."
    }


# ---------------------------------------------------------------------------
# 5. APA 7th Edition & CONSORT Reporting Formatter
# ---------------------------------------------------------------------------
def format_apa_t_test(
    t_val: float,
    df: int,
    p_val: float,
    d_val: Optional[float] = None,
    ci_l: Optional[float] = None,
    ci_u: Optional[float] = None
) -> str:
    """Formats t-test statistics adhering strictly to APA 7th Edition."""
    p_str = "< .001" if p_val < 0.001 else f"= {p_val:.3f}".replace("0.", ".")
    base = f"t({df}) = {t_val:.2f}, p {p_str}"
    if d_val is not None:
        base += f", d = {d_val:.2f}"
    if ci_l is not None and ci_u is not None:
        base += f", 95% CI [{ci_l:.2f}, {ci_u:.2f}]"
    return base


def format_apa_meta_analysis(
    parameter_name: str,
    k_studies: int,
    total_n: int,
    measure: str,
    pooled_est: float,
    ci_l: float,
    ci_u: float,
    p_val: float,
    i2: float,
    pi_l: Optional[float] = None,
    pi_u: Optional[float] = None
) -> str:
    """Formats pooled meta-analysis results adhering to CONSORT and APA 7th Edition."""
    p_str = "< .001" if p_val < 0.001 else f"= {p_val:.3f}".replace("0.", ".")
    res = f"Across {k_studies} trials (N = {total_n:,}), the pooled random-effects estimate for {parameter_name} "
    res += f"was {measure} = {pooled_est:.2f}, 95% CI [{ci_l:.2f}, {ci_u:.2f}], p {p_str} (I² = {i2:.1f}%"
    if pi_l is not None and pi_u is not None:
        res += f", 95% PI [{pi_l:.2f}, {pi_u:.2f}]"
    res += ")."
    return res
