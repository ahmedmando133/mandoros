"""
PRISMA Outcome Explorer & Statistical Readiness Engine.
Harmonizes endpoints across clinical trials, assesses scale compatibility,
evaluates meta-analytic synthesis readiness, and bridges to the read-only REML core.
"""

from typing import Any, Optional
import pandas as pd

from src.prisma.models import PrismaTrial, PrismaOutcome, StatisticalReadinessSpec


class PrismaOutcomeExplorer:
    """Exploration and readiness assessment service for cross-trial clinical endpoints."""

    def __init__(self, trials: dict[str, PrismaTrial]):
        self.trials = trials

    def list_all_outcomes(self) -> list[dict[str, Any]]:
        """Inventories all unique outcome parameters across all trials with reporting statistics."""
        grouped: dict[str, dict[str, Any]] = {}

        for tid, trial in self.trials.items():
            for out in trial.outcomes:
                param = out.parameter_name.strip()
                if not param:
                    continue

                if param not in grouped:
                    grouped[param] = {
                        "parameter_name": param,
                        "domain": out.domain or "Efficacy",
                        "trials": set(),
                        "arms_count": 0,
                        "units": set(),
                        "timepoints": set(),
                        "statistical_types": set(),
                        "has_variance": True,
                    }

                grouped[param]["trials"].add(tid)
                grouped[param]["arms_count"] += 1
                if out.unit:
                    grouped[param]["units"].add(out.unit.strip())
                if out.timepoint_label():
                    grouped[param]["timepoints"].add(out.timepoint_label())
                if out.statistical_type:
                    grouped[param]["statistical_types"].add(out.statistical_type)
                if out.statistical_type.startswith("continuous") and out.mean is not None and out.sd is None:
                    grouped[param]["has_variance"] = False

        results = []
        for param, data in sorted(grouped.items(), key=lambda x: (len(x[1]["trials"]), x[0]), reverse=True):
            k = len(data["trials"])
            units = list(data["units"])
            harmonized = len(units) <= 1
            readiness = "Ready" if k >= 2 and harmonized and data["has_variance"] else ("Partial" if k >= 2 else "Single-Trial")

            results.append({
                "Parameter Name": param,
                "Clinical Domain": data["domain"],
                "Trials (k)": k,
                "Reporting Trials": ", ".join(sorted(list(data["trials"]))),
                "Extracted Arms (N)": data["arms_count"],
                "Units Observed": ", ".join(units) if units else "None / Score",
                "Unit Harmonization": "✅ Aligned" if harmonized else "⚠️ Mixed Scales",
                "Timepoints": ", ".join(sorted(list(data["timepoints"]))),
                "Readiness Verdict": readiness,
            })

        return results

    def get_outcome_matrix_df(self, parameter_name: str) -> pd.DataFrame:
        """
        Builds a detailed arm-by-arm table for a specific outcome across all reporting trials,
        showing timepoint, sample sizes, values, and exact cell provenance.
        """
        rows = []
        param_clean = parameter_name.strip().lower()

        for tid, trial in self.trials.items():
            matching_outcomes = [
                o for o in trial.outcomes
                if (o.parameter_name or "").strip().lower() == param_clean
            ]

            for out in matching_outcomes:
                rows.append({
                    "Trial ID": tid,
                    "Study Citation": trial.citation_short(),
                    "Arm Name": out.arm_name or out.arm_id,
                    "Domain": out.domain,
                    "Timepoint": out.timepoint_label(),
                    "Sample Size (N)": out.sample_size or "NR",
                    "Mean / Baseline": out.mean if out.mean is not None else "NR",
                    "SD / SE": out.sd if out.sd is not None else "NR",
                    "Change (Δ)": out.change_value if out.change_value is not None else "NR",
                    "Change SD": out.change_sd if out.change_sd is not None else "NR",
                    "Events / Total": f"{int(out.events)}/{int(out.total)}" if out.events is not None and out.total is not None else "NR",
                    "Unit": out.unit or "Score / NR",
                    "p-value": out.p_value or "NR",
                    "Provenance": out.provenance.citation(),
                })

        return pd.DataFrame(rows) if rows else pd.DataFrame({"Message": [f"No trials report outcome '{parameter_name}'."]})

    def evaluate_readiness(self, parameter_name: str) -> StatisticalReadinessSpec:
        """
        Thoroughly evaluates statistical synthesis readiness for a given outcome.
        Identifies feasible effect estimators, missing inputs, and scale incompatibilities.
        """
        param_clean = parameter_name.strip().lower()
        reporting_trials: dict[str, list[PrismaOutcome]] = {}
        all_units = set()
        timepoints = set()
        stat_types = set()
        total_pts = 0

        for tid, trial in self.trials.items():
            matches = [o for o in trial.outcomes if (o.parameter_name or "").strip().lower() == param_clean]
            if matches:
                reporting_trials[tid] = matches
                for m in matches:
                    if m.unit:
                        all_units.add(m.unit.strip())
                    if m.timepoint_label():
                        timepoints.add(m.timepoint_label())
                    if m.statistical_type:
                        stat_types.add(m.statistical_type)
                    if m.sample_size:
                        total_pts += m.sample_size

        k = len(reporting_trials)
        units_list = sorted(list(all_units))
        units_harmonized = len(units_list) <= 1

        missing_inputs = []
        feasible_analyses = []
        recommendations = []
        domain = "Efficacy"

        if k == 0:
            return StatisticalReadinessSpec(
                outcome_name=parameter_name,
                reporting_trials_count=0,
                readiness_score=0.0,
                readiness_status="No Evidence Found",
                recommendations=["Verify outcome spelling or check if endpoint was extracted under an alternative synonym."],
            )

        # Inspect arms within reporting trials
        arms_count = sum(len(outs) for outs in reporting_trials.values())
        continuous_ready_trials = 0
        binary_ready_trials = 0

        for tid, outs in reporting_trials.items():
            domain = outs[0].domain or "Efficacy"
            # Check for experimental vs comparator arm presence
            trial_obj = self.trials.get(tid)
            has_exp = any(
                any(a.arm_id == o.arm_id and a.intervention_type == "experimental" for a in trial_obj.arms)
                for o in outs
            ) if trial_obj else True

            for o in outs:
                if o.mean is not None:
                    if o.sd is None and o.change_sd is None:
                        missing_inputs.append(f"{tid} ({o.arm_name}): Mean reported ({o.mean}) without SD/SE")
                    else:
                        continuous_ready_trials += 1
                elif o.events is not None and o.total is not None:
                    binary_ready_trials += 1
                elif o.change_value is not None and o.change_sd is None:
                    missing_inputs.append(f"{tid} ({o.arm_name}): Change from baseline ({o.change_value}) lacks SD_delta")

        # Determine Feasibility
        if k < 2:
            readiness_status = "Single-Trial Observation (Synthesis Infeasible)"
            recommendations.append("A minimum of k >= 2 independent RCTs is mathematically required to compute between-study variance (tau^2) and pool evidence.")
            score = 35.0
        else:
            # Multi-trial scenario
            if units_harmonized:
                feasible_analyses.append("Continuous Raw Mean Difference (MD) Pooling")
                feasible_analyses.append("Restricted Maximum Likelihood (REML) Meta-Analysis")
                feasible_analyses.append("DerSimonian-Laird Random-Effects Modeling")
                recommendations.append("Identical measurement units allow direct Raw Mean Difference (MD) pooling with high clinical interpretability.")
            else:
                feasible_analyses.append("Standardized Mean Difference (SMD / Hedges' g) Pooling")
                recommendations.append(f"Mixed measurement units ({', '.join(units_list)}) detected. Scale-free Standardized Mean Difference (SMD) must be used instead of raw MD.")

            if len(timepoints) > 1:
                recommendations.append(f"Follow-up timepoints vary ({', '.join(sorted(list(timepoints)))}). Consider subgrouping by duration or longitudinal meta-regression.")

            if missing_inputs:
                score = max(40.0, 85.0 - len(missing_inputs) * 10.0)
                readiness_status = "Partially Feasible (Variance Imputation Needed)"
                recommendations.append(f"Missing variance parameters detected in {len(missing_inputs)} arm(s). Extract SD from confidence intervals or consult supplementary tables.")
            else:
                score = 95.0 if units_harmonized else 85.0
                readiness_status = "Ready for REML Meta-Analysis"
                recommendations.append("Full sample sizes, central tendencies, and dispersion measures are present across all comparator arms.")

        return StatisticalReadinessSpec(
            outcome_name=parameter_name,
            domain=domain,
            reporting_trials_count=k,
            total_patients=total_pts,
            arms_count=arms_count,
            statistical_type=", ".join(stat_types) if stat_types else "continuous",
            common_unit=units_list[0] if units_list else "Score",
            all_units=units_list,
            units_harmonized=units_harmonized,
            feasible_analyses=feasible_analyses,
            missing_inputs=missing_inputs,
            readiness_score=score,
            readiness_status=readiness_status,
            recommendations=recommendations,
        )

    def compute_reml_preview_safe(self, parameter_name: str) -> dict[str, Any]:
        """
        Safely executes a read-only trial-level meta-analysis using MANDOROS's existing
        statistical core without altering any files or pipelines.
        """
        spec = self.evaluate_readiness(parameter_name)
        if spec.reporting_trials_count < 2 or spec.missing_inputs:
            return {
                "success": False,
                "reason": spec.readiness_status,
                "missing": spec.missing_inputs,
                "recommendation": spec.recommendations,
            }

        try:
            from src.meta_predictive import run_meta_analysis

            # Assemble trial pairs for meta-analysis
            study_data = []
            param_clean = parameter_name.strip().lower()

            for tid, trial in self.trials.items():
                matching = [o for o in trial.outcomes if (o.parameter_name or "").strip().lower() == param_clean]
                if len(matching) >= 2:
                    # Find experimental vs control
                    exp_o = next((o for o in matching if "placebo" not in o.arm_name.lower() and "control" not in o.arm_name.lower()), matching[0])
                    ctrl_o = next((o for o in matching if "placebo" in o.arm_name.lower() or "control" in o.arm_name.lower()), matching[1])

                    n_e = exp_o.sample_size or 50
                    m_e = exp_o.mean if exp_o.mean is not None else (exp_o.change_value or 0.0)
                    sd_e = exp_o.sd if exp_o.sd is not None else (exp_o.change_sd or 1.0)

                    n_c = ctrl_o.sample_size or 50
                    m_c = ctrl_o.mean if ctrl_o.mean is not None else (ctrl_o.change_value or 0.0)
                    sd_c = ctrl_o.sd if ctrl_o.sd is not None else (ctrl_o.change_sd or 1.0)

                    study_data.append({
                        "study_id": tid,
                        "n_e": n_e,
                        "mean_e": m_e,
                        "sd_e": sd_e,
                        "n_c": n_c,
                        "mean_c": m_c,
                        "sd_c": sd_c,
                    })

            if len(study_data) < 2:
                return {
                    "success": False,
                    "reason": "Could not pair experimental vs control arms for at least 2 trials.",
                    "details": f"Paired studies count = {len(study_data)}",
                }

            # Call read-only meta-analysis core
            meta_res = run_meta_analysis(study_data, effect_type="MD" if spec.units_harmonized else "SMD", method="REML")
            return {
                "success": True,
                "pooled_effect": meta_res.get("pooled_effect"),
                "ci_lower": meta_res.get("ci_lower"),
                "ci_upper": meta_res.get("ci_upper"),
                "p_value": meta_res.get("p_value"),
                "i2": meta_res.get("i2"),
                "tau2": meta_res.get("tau2"),
                "q_stat": meta_res.get("q"),
                "studies_pooled": len(study_data),
                "model": "Restricted Maximum Likelihood (REML)",
                "metric": "Mean Difference (MD)" if spec.units_harmonized else "Standardized Mean Difference (SMD)",
            }
        except Exception as e:
            return {
                "success": False,
                "reason": f"Calculation halted: {str(e)}",
            }
