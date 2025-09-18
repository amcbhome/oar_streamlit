
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

from src.oar import compute_oar_table, build_production_table, reconcile_applied_overhead

st.set_page_config(page_title="Automating the OAR • Live Inventory Valuation", layout="wide")

st.title("Automating the Overhead Absorption Rate (OAR)")
st.caption("IFRS (IAS 2) compliant inventory valuation with BI-style monitoring")

# Sidebar config
st.sidebar.header("Configuration")
beta = st.sidebar.slider("β (nudge factor)", 0.0, 1.0, 0.5, 0.05)
deadband = st.sidebar.slider("Deadband (±%)", 0.0, 20.0, 5.0, 0.5) / 100
cap = st.sidebar.slider("Monthly cap (±%)", 0.0, 50.0, 10.0, 1.0) / 100
alpha = st.sidebar.slider("EWMA α (rolling OAR)", 0.0, 1.0, 0.3, 0.05)
use_operational = st.sidebar.checkbox("Use Operational OAR for live unit costs", True)

st.sidebar.divider()
st.sidebar.subheader("Data upload (optional)")
uploaded_oar = st.sidebar.file_uploader("oar_inputs.csv", type=["csv"])
uploaded_prod = st.sidebar.file_uploader("production_today.csv", type=["csv"])
uploaded_drivers = st.sidebar.file_uploader("drivers_today.csv", type=["csv"])
uploaded_price = st.sidebar.file_uploader("pricebook.csv", type=["csv"])

# Load data
data_path = Path("data")
oar_inputs = pd.read_csv(uploaded_oar) if uploaded_oar else pd.read_csv(data_path / "oar_inputs.csv")
production_today = pd.read_csv(uploaded_prod) if uploaded_prod else pd.read_csv(data_path / "production_today.csv")
drivers_today = pd.read_csv(uploaded_drivers) if uploaded_drivers else pd.read_csv(data_path / "drivers_today.csv")
pricebook = pd.read_csv(uploaded_price) if uploaded_price else pd.read_csv(data_path / "pricebook.csv")

# Compute OAR table
oar_table = compute_oar_table(oar_inputs, beta=beta, deadband=deadband, cap=cap, ewma_alpha=alpha)
today = oar_table.iloc[-1]
OAR_BUDGET = float(today["oar_budget"])
OAR_OPERATIONAL = float(today["oar_rolling"])
OAR_FOR_COSTING = OAR_OPERATIONAL if use_operational else OAR_BUDGET
OAR_PROPOSAL = float(today["oar_proposal"])
VARIANCE_PCT = float(today["variance_pct"])

# KPI row
c1, c2, c3, c4 = st.columns(4)
c1.metric("OAR (Budget, £/mh)", f"{OAR_BUDGET:,.2f}")
c2.metric("OAR (Operational, £/mh)", f"{OAR_OPERATIONAL:,.2f}", f"{VARIANCE_PCT:,.2f}% vs budget")
c3.metric("OAR (Proposal, £/mh)", f"{OAR_PROPOSAL:,.2f}")
c4.metric("Deadband / Cap", f"±{deadband*100:.1f}% / ±{cap*100:.1f}%")

# Build production valuation
prod = build_production_table(production_today, drivers_today, pricebook, OAR_FOR_COSTING)
live_total = prod["line_value"].sum()

c5, c6 = st.columns(2)
with c5:
    st.subheader("Live Inventory Value (premises)")
    st.write(f"**£{live_total:,.2f}**")
    st.dataframe(prod[["product","status","quantity","wip_conv_pct","mh_per_unit","direct_material","direct_labour","unit_cost","line_value"]], use_container_width=True)
with c6:
    st.subheader("Inventory Value by Product")
    by_prod = prod.groupby("product", as_index=False)["line_value"].sum()
    fig = plt.figure()
    plt.bar(by_prod["product"], by_prod["line_value"])
    plt.title("Live Inventory Value by Product")
    plt.xlabel("Product")
    plt.ylabel("Value (£)")
    st.pyplot(fig)

st.divider()
st.subheader("OAR History")
st.caption("Budget vs Actual vs Rolling (operational)")
fig2 = plt.figure()
plt.plot(oar_table["period"], oar_table["oar_budget"], label="OAR_budget")
plt.plot(oar_table["period"], oar_table["oar_actual"], label="OAR_actual")
plt.plot(oar_table["period"], oar_table["oar_rolling"], label="OAR_rolling")
plt.title("OAR History")
plt.xlabel("Period")
plt.ylabel("£ per machine-hour")
plt.legend()
st.pyplot(fig2)

st.divider()
st.subheader("Under/Over-Absorption Reconciliation")
recon = reconcile_applied_overhead(
    prod,
    oar_budget=OAR_BUDGET,
    oar_operational=OAR_OPERATIONAL,
    actual_overhead_period=float(today["actual_overhead"])
)
st.json(recon)

# Downloads
st.divider()
st.subheader("Downloads")
st.download_button("Download current OAR table (CSV)",
                   data=oar_table.to_csv(index=False).encode("utf-8"),
                   file_name="oar_table_out.csv",
                   mime="text/csv")
st.download_button("Download current production valuation (CSV)",
                   data=prod.to_csv(index=False).encode("utf-8"),
                   file_name="production_valuation_out.csv",
                   mime="text/csv")

st.caption("Built for master’s projects: IAS 2 compliant logic with BI-style monitoring and optional optimisation add-ons.")
