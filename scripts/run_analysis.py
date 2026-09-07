"""Run the core SpaceX capstone analysis and save reproducible result tables."""

from __future__ import annotations

import json
import sqlite3
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn import preprocessing
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import confusion_matrix
from sklearn.model_selection import GridSearchCV, train_test_split
from sklearn.neighbors import KNeighborsClassifier
from sklearn.svm import SVC
from sklearn.tree import DecisionTreeClassifier



def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Return the great-circle distance between two coordinates in kilometres."""

    from math import atan2, cos, radians, sin, sqrt

    earth_radius_km = 6373.0
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlon, dlat = lon2 - lon1, lat2 - lat1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    return earth_radius_km * 2 * atan2(sqrt(a), sqrt(1 - a))


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
OUTPUT = ROOT / "outputs"
OUTPUT.mkdir(exist_ok=True)
warnings.filterwarnings("ignore")


def clean_value(value):
    if isinstance(value, dict):
        return {str(key): clean_value(val) for key, val in value.items()}
    if isinstance(value, (list, tuple)):
        return [clean_value(item) for item in value]
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        return float(value)
    if pd.isna(value):
        return None
    return value


def save_table(frame: pd.DataFrame, name: str) -> None:
    frame.to_csv(OUTPUT / name, index=False)


def run_models(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    features = pd.read_csv(DATA / "dataset_part_3.csv")
    y = df["Class"].to_numpy()
    x = preprocessing.StandardScaler().fit_transform(features)
    x_train, x_test, y_train, y_test = train_test_split(x, y, test_size=0.2, random_state=2)

    grids = [
        (
            "Logistic Regression",
            LogisticRegression(max_iter=1000),
            {"C": [0.01, 0.1, 1], "penalty": ["l2"], "solver": ["lbfgs"]},
        ),
        (
            "SVM",
            SVC(),
            {"kernel": ["linear", "rbf", "poly", "sigmoid"], "C": np.logspace(-3, 3, 5), "gamma": np.logspace(-3, 3, 5)},
        ),
        (
            "Decision Tree",
            DecisionTreeClassifier(),
            {
                "criterion": ["gini", "entropy"],
                "splitter": ["best", "random"],
                "max_depth": [2 * n for n in range(1, 10)],
                "max_features": [None, "sqrt", "log2"],
                "min_samples_leaf": [1, 2, 4],
                "min_samples_split": [2, 5, 10],
                "random_state": [2],
            },
        ),
        (
            "KNN",
            KNeighborsClassifier(),
            {"n_neighbors": list(range(1, 11)), "algorithm": ["auto", "ball_tree", "kd_tree", "brute"], "p": [1, 2]},
        ),
    ]

    rows = []
    fitted = {}
    for name, estimator, parameters in grids:
        search = GridSearchCV(estimator, parameters, cv=10)
        search.fit(x_train, y_train)
        prediction = search.predict(x_test)
        fitted[name] = search
        rows.append(
            {
                "model": name,
                "cv_accuracy": search.best_score_,
                "test_accuracy": search.score(x_test, y_test),
                "best_params": json.dumps(clean_value(search.best_params_), sort_keys=True),
                "true_negative": confusion_matrix(y_test, prediction).tolist()[0][0],
                "false_positive": confusion_matrix(y_test, prediction).tolist()[0][1],
                "false_negative": confusion_matrix(y_test, prediction).tolist()[1][0],
                "true_positive": confusion_matrix(y_test, prediction).tolist()[1][1],
            }
        )
    results = pd.DataFrame(rows).sort_values("cv_accuracy", ascending=False).reset_index(drop=True)
    save_table(results, "model_comparison.csv")
    return results, {"train_rows": len(x_train), "test_rows": len(x_test), "features": features.shape[1]}


def run_sql(raw: pd.DataFrame) -> dict:
    connection = sqlite3.connect(":memory:")
    raw.to_sql("SPACEXTBL", connection, index=False, if_exists="replace")
    connection.execute("CREATE TABLE SPACEXTABLE AS SELECT * FROM SPACEXTBL WHERE Date IS NOT NULL")

    def query(sql: str) -> pd.DataFrame:
        return pd.read_sql_query(sql, connection)

    sql_results = {
        "unique_launch_sites": query('SELECT DISTINCT "Launch_Site" FROM SPACEXTABLE ORDER BY "Launch_Site"')["Launch_Site"].tolist(),
        "nasa_crs_payload_kg": query('SELECT SUM("PAYLOAD_MASS__KG_") AS value FROM SPACEXTABLE WHERE "Customer" LIKE \'%NASA (CRS)%\'').iloc[0, 0],
        "f9_v11_average_payload_kg": query('SELECT AVG("PAYLOAD_MASS__KG_") AS value FROM SPACEXTABLE WHERE "Booster_Version" LIKE \'%F9 v1.1%\'').iloc[0, 0],
        "first_successful_ground_pad_landing": query('SELECT MIN("Date") AS value FROM SPACEXTABLE WHERE "Landing_Outcome" LIKE \'Success (ground pad)%\'').iloc[0, 0],
        "drone_ship_4_to_6_t_boosters": query('SELECT "Booster_Version" FROM SPACEXTABLE WHERE "Landing_Outcome" LIKE \'Success (drone ship)%\' AND "PAYLOAD_MASS__KG_" > 4000 AND "PAYLOAD_MASS__KG_" < 6000 ORDER BY "Booster_Version"')["Booster_Version"].tolist(),
        "mission_outcomes": query('SELECT CASE WHEN TRIM("Mission_Outcome") LIKE \'Success%\' THEN \'Success\' ELSE \'Failure\' END AS outcome, COUNT(*) AS count FROM SPACEXTABLE GROUP BY outcome ORDER BY outcome').to_dict("records"),
        "maximum_payload_boosters": query('SELECT "Booster_Version" FROM SPACEXTABLE WHERE "PAYLOAD_MASS__KG_" = (SELECT MAX("PAYLOAD_MASS__KG_") FROM SPACEXTABLE) ORDER BY "Booster_Version"')["Booster_Version"].tolist(),
        "2015_drone_ship_failures": query('SELECT substr("Date", 6, 2) AS month, "Booster_Version", "Launch_Site" FROM SPACEXTABLE WHERE TRIM("Landing_Outcome") LIKE \'Failure (drone ship)%\' AND substr("Date", 1, 4) = \'2015\' ORDER BY month').to_dict("records"),
        "landing_outcome_ranking": query('SELECT TRIM("Landing_Outcome") AS landing_outcome, COUNT(*) AS count FROM SPACEXTABLE WHERE "Date" BETWEEN \'2010-06-04\' AND \'2017-03-20\' GROUP BY TRIM("Landing_Outcome") ORDER BY count DESC, landing_outcome').to_dict("records"),
    }
    for key, value in sql_results.items():
        if isinstance(value, pd.Timestamp):
            sql_results[key] = value.strftime("%Y-%m-%d")
    return clean_value(sql_results)


def main() -> None:
    df = pd.read_csv(DATA / "dataset_part_2.csv")
    raw = pd.read_csv(DATA / "Spacex.csv")
    df["Year"] = df["Date"].str[:4].astype(int)
    df["payload_bin"] = pd.cut(
        df["PayloadMass"],
        bins=[-1, 1000, 3000, 5000, 7000, 10000, 20000],
        labels=["0-1t", "1-3t", "3-5t", "5-7t", "7-10t", "10-20t"],
    )

    site = df.groupby("LaunchSite")["Class"].agg(count="count", successes="sum", success_rate="mean").reset_index()
    orbit = df.groupby("Orbit")["Class"].agg(count="count", successes="sum", success_rate="mean").reset_index().sort_values("success_rate", ascending=False)
    yearly = df.groupby("Year")["Class"].agg(count="count", successes="sum", success_rate="mean").reset_index()
    payload = df.groupby("payload_bin", observed=True)["Class"].agg(count="count", successes="sum", success_rate="mean").reset_index()
    save_table(site, "site_success.csv")
    save_table(orbit, "orbit_success.csv")
    save_table(yearly, "yearly_success.csv")
    save_table(payload, "payload_bins.csv")

    dash = pd.read_csv(DATA / "spacex_launch_dash.csv")
    dash["payload_bin"] = pd.cut(dash["Payload Mass (kg)"], bins=[-1, 1000, 3000, 5000, 7000, 10000], labels=["0-1t", "1-3t", "3-5t", "5-7t", "7-10t"])
    dash_site = dash.groupby("Launch Site")["class"].agg(count="count", successes="sum", success_rate="mean").reset_index()
    dash_payload = dash.groupby("payload_bin", observed=True)["class"].agg(count="count", successes="sum", success_rate="mean").reset_index()
    booster = dash.groupby("Booster Version Category")["class"].agg(count="count", successes="sum", success_rate="mean").reset_index().sort_values("success_rate", ascending=False)
    save_table(dash_site, "dashboard_site_success.csv")
    save_table(dash_payload, "dashboard_payload_bins.csv")
    save_table(booster, "booster_category_success.csv")

    geo = pd.read_csv(DATA / "spacex_launch_geo.csv")
    geo_site = geo.groupby("Launch Site")["class"].agg(count="count", successes="sum", success_rate="mean").reset_index()
    save_table(geo_site, "geo_site_success.csv")
    selected = geo.loc[geo["Launch Site"] == "CCAFS LC-40"].iloc[0]
    coast = [28.56230, -80.57000]
    city = [28.4011, -80.6057]
    distances = {
        "coastline_distance_km": calculate_distance(selected["Lat"], selected["Long"], *coast),
        "city_distance_km": calculate_distance(selected["Lat"], selected["Long"], *city),
    }

    sql_results = run_sql(raw)
    model_results, model_setup = run_models(df)
    best_model = model_results.iloc[0]
    report = {
        "dataset": {
            "rows": len(df),
            "successful_landings": int(df["Class"].sum()),
            "failed_landings": int((df["Class"] == 0).sum()),
            "success_rate": float(df["Class"].mean()),
            "date_range": [df["Date"].min(), df["Date"].max()],
            "launch_sites": sorted(df["LaunchSite"].unique().tolist()),
            "orbits": sorted(df["Orbit"].unique().tolist()),
        },
        "eda": {
            "site_success": site.to_dict("records"),
            "orbit_success": orbit.to_dict("records"),
            "yearly_success": yearly.to_dict("records"),
            "payload_bins": payload.to_dict("records"),
        },
        "dashboard": {
            "rows": len(dash),
            "largest_success_count_site": dash_site.sort_values("successes", ascending=False).iloc[0]["Launch Site"],
            "highest_success_rate_site": dash_site.sort_values("success_rate", ascending=False).iloc[0]["Launch Site"],
            "site_success": dash_site.to_dict("records"),
            "payload_bins": dash_payload.to_dict("records"),
            "booster_categories": booster.to_dict("records"),
        },
        "sql": sql_results,
        "map": {"site_success": geo_site.to_dict("records"), "distances": distances},
        "models": {
            "setup": model_setup,
            "comparison": model_results.drop(columns=["best_params"]).to_dict("records"),
            "best_cv_model": best_model["model"],
            "best_cv_accuracy": best_model["cv_accuracy"],
        },
    }
    with (OUTPUT / "results.json").open("w", encoding="utf-8") as handle:
        json.dump(clean_value(report), handle, indent=2)
    print(json.dumps(clean_value({"dataset": report["dataset"], "best_model": report["models"]}), indent=2))


if __name__ == "__main__":
    main()
