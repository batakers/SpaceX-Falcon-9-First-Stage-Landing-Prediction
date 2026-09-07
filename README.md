# SpaceX Falcon 9 First-Stage Landing Prediction

This repository contains the completed notebooks and Python files for the IBM Data Science Capstone project. The project combines data wrangling, exploratory data analysis, SQL, geospatial analysis with Folium, an interactive Plotly Dash dashboard, and binary classification models.

## Repository contents

- `notebooks/01_eda_sql_completed.ipynb` - SQL exploratory analysis with ten completed queries.
- `notebooks/02_eda_dataviz_completed.ipynb` - EDA, visual analytics, and one-hot feature engineering.
- `notebooks/03_folium_launch_sites_completed.ipynb` - launch-site map, success/failure clusters, and proximity lines.
- `notebooks/04_machine_learning_completed.ipynb` - standardized features, 10-fold GridSearchCV, and model comparison.
- `spacex_dash_app.py` - Plotly Dash application with launch-site dropdown and payload range slider.
- `scripts/run_analysis.py` - reproducible analysis runner that writes tables and `outputs/results.json`.
- `scripts/folium_launch_map.py` - standalone Folium map generator.
- `data/` - course datasets used by the notebooks and dashboard.

## Run locally

```bash
python -m pip install -r requirements.txt
python scripts/run_analysis.py
python scripts/folium_launch_map.py
python spacex_dash_app.py
```

The Dash application runs on port `8050`. The Folium map is saved to `outputs/launch_sites_map.html`.

## Main findings

- The cleaned modeling dataset contains 90 launches, 60 successful landings, and an overall landing success rate of 66.7%.
- KSC LC 39A has the highest success rate among the three normalized sites with repeated observations: 77.3% (17 of 22).
- Higher payload bands in the study data are associated with stronger outcomes: 7,000-10,000 kg reaches 90.0% success.
- Decision Tree has the strongest validation result in the completed model comparison; all four tuned models score 83.3% on the held-out test set.

## Data provenance

The datasets are the IBM Skills Network SpaceX capstone datasets referenced by the course notebooks. The original source URLs are preserved in the notebooks' reference sections.

