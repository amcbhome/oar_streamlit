
import pandas as pd
import numpy as np

def compute_oar_table(oar_inputs, beta=0.5, deadband=0.05, cap=0.10, ewma_alpha=0.3):
    df = oar_inputs.copy()
    df["oar_budget"] = df["budgeted_overhead"] / df["normal_capacity_mh"]
    df["oar_actual"] = df["actual_overhead"] / df["actual_driver_mh"]
    df["oar_rolling"] = df["oar_actual"].ewm(alpha=ewma_alpha, adjust=False).mean()

    def bounded(row):
        ob = row["oar_budget"]
        oroll = row["oar_rolling"]
        variance = (oroll - ob) / ob if ob else 0.0
        if abs(variance) < deadband:
            return ob, variance
        proposal = ob * (1 + beta * variance)
        lower = ob * (1 - cap)
        upper = ob * (1 + cap)
        return float(np.clip(proposal, lower, upper)), variance

    props = df.apply(bounded, axis=1, result_type="expand")
    df["oar_proposal"] = props[0]
    df["variance_pct"] = props[1] * 100.0
    return df

def build_production_table(production_today, drivers_today, pricebook, oar_for_costing):
    prod = production_today.merge(drivers_today, on="product", how="left").merge(pricebook, on="product", how="left")
    def unit_cost(row):
        dm = row["direct_material"]
        dl = row["direct_labour"]
        oh = row["mh_per_unit"] * oar_for_costing
        conv = 1.0 if row["status"] == "finished" else float(row.get("wip_conv_pct", 1.0))
        dm_component = dm
        dl_component = dl * conv
        oh_component = oh * conv
        return dm_component + dl_component + oh_component
    prod["unit_cost"] = prod.apply(unit_cost, axis=1)
    prod["line_value"] = prod["unit_cost"] * prod["quantity"]

    # effective driver for absorption reconciliation
    prod["mh_effective"] = np.where(
        prod["status"].eq("finished"),
        prod["mh_per_unit"] * prod["quantity"],
        prod["mh_per_unit"] * prod["quantity"] * prod["wip_conv_pct"]
    )
    return prod

def reconcile_applied_overhead(prod, oar_budget, oar_operational, actual_overhead_period):
    driver_mh = prod["mh_effective"].sum()
    applied_reporting = driver_mh * oar_budget
    applied_operational = driver_mh * oar_operational
    return {
        "driver_mh": float(driver_mh),
        "applied_reporting": float(applied_reporting),
        "applied_operational": float(applied_operational),
        "actual_overhead": float(actual_overhead_period),
        "under_over_vs_reporting": float(actual_overhead_period - applied_reporting),
        "under_over_vs_operational": float(actual_overhead_period - applied_operational),
    }
