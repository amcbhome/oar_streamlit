
# Automating the Overhead Absorption Rate (OAR) — Streamlit App

A Business Intelligence app that automates **Overhead Absorption Rates** for **IFRS (IAS 2)**-compliant inventory valuation,
with live dashboards, WIP handling, and under/over-absorption reconciliation.

## Features
- **Budget vs Actual vs Rolling OAR** (EWMA smoothing; deadband & monthly caps)
- **Live unit costing** for finished goods and WIP (materials 100%, conversion by % complete)
- **Inventory valuation by product** and site total
- **Under/Over-absorption** check vs reporting OAR
- CSV uploads for `oar_inputs`, `production_today`, `drivers_today`, `pricebook`

## Folder Structure
```
oar_streamlit/
├── app.py
├── README.md
├── requirements.txt
├── data/
│   ├── oar_inputs.csv
│   ├── production_today.csv
│   ├── drivers_today.csv
│   └── pricebook.csv
└── src/
    └── oar.py
```

## Data Contracts
- **oar_inputs.csv**: `period,budgeted_overhead,normal_capacity_mh,actual_overhead,actual_driver_mh`
- **production_today.csv**: `product,status,quantity,wip_conv_pct` (status in {finished,wip})
- **drivers_today.csv**: `product,mh_per_unit,kwh_per_unit,labour_hours_per_unit`
- **pricebook.csv**: `product,direct_material,direct_labour`

## Run Locally
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Deploy on Streamlit Community Cloud
1. Push this folder to a **new GitHub repo**.
2. Go to https://share.streamlit.io/
3. Select the repo and `app.py` as the entrypoint.
4. Set Python version to 3.10+ (or default).
5. Deploy.

## Notes
- The app uses **Operational OAR** for live costing (configurable). Financial reporting can stay anchored to **Budgeted OAR** (IAS 2 normal capacity).
- Charts use matplotlib; no styles specified as requested.
- Extend with an optimisation tab using `pulp` for scheduling to stabilise OAR.
