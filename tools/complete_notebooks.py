"""Create completed, locally reproducible versions of the supplied course notebooks."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
UPLOAD = ROOT.parent / "upload"
OUT = ROOT / "notebooks"
OUT.mkdir(parents=True, exist_ok=True)


def lines(text: str) -> list[str]:
    return text.strip("\n") .splitlines(keepends=True)


def load(name: str) -> dict:
    with (UPLOAD / name).open(encoding="utf-8") as handle:
        return json.load(handle)


def set_code(nb: dict, index: int, source: str) -> None:
    cell = nb["cells"][index]
    cell["cell_type"] = "code"
    cell["source"] = lines(source)
    cell["execution_count"] = None
    cell["outputs"] = []


def replace_all(nb: dict, old: str, new: str) -> None:
    for cell in nb["cells"]:
        if "source" in cell:
            source = "".join(cell["source"])
            if old in source:
                cell["source"] = lines(source.replace(old, new))


def add_reproducibility_note(nb: dict, text: str) -> None:
    nb["cells"].append(
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": lines(text),
        }
    )


def write(nb: dict, filename: str) -> None:
    with (OUT / filename).open("w", encoding="utf-8") as handle:
        json.dump(nb, handle, ensure_ascii=False, indent=1)
        handle.write("\n")


# ---------------------------------------------------------------------------
# SQL exploratory analysis
# ---------------------------------------------------------------------------
sql = load("jupyter-labs-eda-sql-coursera_sqllite(2).ipynb")
set_code(
    sql,
    3,
    """# This completed version uses Python's built-in SQLite driver; no SQL magic extension is required.
import sqlite3
import pandas as pd
from pathlib import Path
""",
)
set_code(
    sql,
    5,
    """base_dir = Path("../data")
con = sqlite3.connect(":memory:")
""",
)
set_code(sql, 6, "# SQL magic is optional; the queries below run through pandas and sqlite3.")
set_code(sql, 7, "# The in-memory database is ready.")
set_code(sql, 8, "# pandas is used for loading and displaying query results.")
set_code(sql, 9, "# The notebook uses the in-memory SQLite connection named con.")
set_code(
    sql,
    10,
    """df = pd.read_csv(base_dir / "Spacex.csv")
df.to_sql("SPACEXTBL", con, if_exists="replace", index=False)
""",
)
set_code(sql, 12, "con.execute('DROP TABLE IF EXISTS SPACEXTABLE')")
set_code(
    sql,
    13,
    """con.execute('CREATE TABLE SPACEXTABLE AS SELECT * FROM SPACEXTBL WHERE Date IS NOT NULL')
""",
)
set_code(
    sql,
    15,
    """query = '''
SELECT DISTINCT "Launch_Site"
FROM SPACEXTABLE
ORDER BY "Launch_Site"
'''
pd.read_sql_query(query, con)
""",
)
set_code(
    sql,
    17,
    """query = '''
SELECT *
FROM SPACEXTABLE
WHERE "Launch_Site" LIKE 'CCA%'
LIMIT 5
'''
pd.read_sql_query(query, con)
""",
)
set_code(
    sql,
    19,
    """query = '''
SELECT SUM("PAYLOAD_MASS__KG_") AS total_payload_kg
FROM SPACEXTABLE
WHERE "Customer" LIKE '%NASA (CRS)%'
'''
pd.read_sql_query(query, con)
""",
)
set_code(
    sql,
    21,
    """query = '''
SELECT AVG("PAYLOAD_MASS__KG_") AS average_payload_kg
FROM SPACEXTABLE
WHERE "Booster_Version" LIKE '%F9 v1.1%'
'''
pd.read_sql_query(query, con)
""",
)
set_code(
    sql,
    23,
    """query = '''
SELECT MIN("Date") AS first_successful_ground_pad_landing
FROM SPACEXTABLE
WHERE "Landing_Outcome" LIKE 'Success (ground pad)%'
'''
pd.read_sql_query(query, con)
""",
)
set_code(
    sql,
    25,
    """query = '''
SELECT "Booster_Version"
FROM SPACEXTABLE
WHERE "Landing_Outcome" LIKE 'Success (drone ship)%'
  AND "PAYLOAD_MASS__KG_" > 4000
  AND "PAYLOAD_MASS__KG_" < 6000
ORDER BY "Booster_Version"
'''
pd.read_sql_query(query, con)
""",
)
set_code(
    sql,
    27,
    """query = '''
SELECT
  CASE WHEN TRIM("Mission_Outcome") LIKE 'Success%' THEN 'Success' ELSE 'Failure' END AS outcome,
  COUNT(*) AS count
FROM SPACEXTABLE
GROUP BY outcome
ORDER BY outcome
'''
pd.read_sql_query(query, con)
""",
)
set_code(
    sql,
    29,
    """query = '''
SELECT "Booster_Version"
FROM SPACEXTABLE
WHERE "PAYLOAD_MASS__KG_" = (
  SELECT MAX("PAYLOAD_MASS__KG_") FROM SPACEXTABLE
)
ORDER BY "Booster_Version"
'''
pd.read_sql_query(query, con)
""",
)
set_code(
    sql,
    31,
    """query = '''
SELECT substr("Date", 6, 2) AS month,
       "Landing_Outcome",
       "Booster_Version",
       "Launch_Site"
FROM SPACEXTABLE
WHERE TRIM("Landing_Outcome") LIKE 'Failure (drone ship)%'
  AND substr("Date", 1, 4) = '2015'
ORDER BY month
'''
pd.read_sql_query(query, con)
""",
)
set_code(
    sql,
    33,
    """query = '''
SELECT TRIM("Landing_Outcome") AS landing_outcome,
       COUNT(*) AS count
FROM SPACEXTABLE
WHERE "Date" BETWEEN '2010-06-04' AND '2017-03-20'
GROUP BY TRIM("Landing_Outcome")
ORDER BY count DESC, landing_outcome
'''
pd.read_sql_query(query, con)
""",
)
add_reproducibility_note(
    sql,
    """### Reproducibility

This version reads `../data/Spacex.csv`, executes all ten SQL tasks against an in-memory SQLite table, and keeps the original task wording for auditability.
""",
)
write(sql, "01_eda_sql_completed.ipynb")


# ---------------------------------------------------------------------------
# EDA and visualization
# ---------------------------------------------------------------------------
eda = load("jupyter-labs-eda-dataviz-v2(2).ipynb")
replace_all(
    eda,
    "https://cf-courses-data.s3.us.cloud-object-storage.appdomain.cloud/IBM-DS0321EN-SkillsNetwork/datasets/dataset_part_2.csv",
    "../data/dataset_part_2.csv",
)
set_code(eda, 13, "# Dependencies are listed in requirements.txt; no notebook-side installation is required.")
set_code(
    eda,
    25,
    """plt.figure(figsize=(12, 5))
sns.scatterplot(data=df, x="FlightNumber", y="LaunchSite", hue="Class", palette={0: "#D1495B", 1: "#2A9D8F"}, s=70)
plt.title("Launch outcome by flight number and launch site")
plt.xlabel("Flight number")
plt.ylabel("Launch site")
plt.show()
""",
)
set_code(
    eda,
    29,
    """plt.figure(figsize=(12, 5))
sns.scatterplot(data=df, x="PayloadMass", y="LaunchSite", hue="Class", palette={0: "#D1495B", 1: "#2A9D8F"}, s=70)
plt.title("Payload mass and launch outcome by launch site")
plt.xlabel("Payload mass (kg)")
plt.ylabel("Launch site")
plt.show()
""",
)
set_code(
    eda,
    34,
    """success_by_orbit = df.groupby("Orbit", as_index=True)["Class"].mean().sort_values(ascending=False)
success_by_orbit.plot(kind="bar", figsize=(10, 5), color="#3D8DFF")
plt.title("Average landing success rate by orbit")
plt.ylabel("Success rate")
plt.xlabel("Orbit")
plt.ylim(0, 1.05)
plt.xticks(rotation=45)
plt.show()
""",
)
set_code(
    eda,
    38,
    """plt.figure(figsize=(12, 5))
sns.scatterplot(data=df, x="FlightNumber", y="Orbit", hue="Class", palette={0: "#D1495B", 1: "#2A9D8F"}, s=70)
plt.title("Launch outcome by flight number and orbit")
plt.xlabel("Flight number")
plt.ylabel("Orbit")
plt.show()
""",
)
set_code(
    eda,
    42,
    """plt.figure(figsize=(12, 5))
sns.scatterplot(data=df, x="PayloadMass", y="Orbit", hue="Class", palette={0: "#D1495B", 1: "#2A9D8F"}, s=70)
plt.title("Payload mass and landing outcome by orbit")
plt.xlabel("Payload mass (kg)")
plt.ylabel("Orbit")
plt.show()
""",
)
set_code(
    eda,
    47,
    """df["Year"] = df["Date"].str[:4].astype(int)
df[["Date", "Year"]].head()
""",
)
set_code(
    eda,
    48,
    """yearly_success = df.groupby("Year", as_index=False)["Class"].mean()
plt.figure(figsize=(10, 5))
sns.lineplot(data=yearly_success, x="Year", y="Class", marker="o", color="#3D8DFF")
plt.title("Landing success rate increased over the study period")
plt.ylabel("Success rate")
plt.ylim(0, 1.05)
plt.grid(True, alpha=0.25)
plt.show()
""",
)
set_code(
    eda,
    55,
    """categorical_columns = ["Orbit", "LaunchSite", "LandingPad", "Serial"]
features_one_hot = pd.get_dummies(features, columns=categorical_columns, dtype=float)
features_one_hot.head()
""",
)
set_code(
    eda,
    58,
    """features_one_hot = features_one_hot.astype("float64")
features_one_hot.to_csv("../data/dataset_part_3_generated.csv", index=False)
features_one_hot.shape
""",
)
add_reproducibility_note(
    eda,
    """### Reproducibility

All plots use `../data/dataset_part_2.csv`. The final feature matrix is one-hot encoded and saved to `../data/dataset_part_3_generated.csv` for modeling.
""",
)
write(eda, "02_eda_dataviz_completed.ipynb")


# ---------------------------------------------------------------------------
# Folium geospatial analysis
# ---------------------------------------------------------------------------
geo = load("lab-jupyter-launch-site-location-v2(2).ipynb")
replace_all(geo, "_TODO:_", "Completed task:")
set_code(geo, 8, "# Install folium in the notebook environment if it is not already available.")
set_code(
    geo,
    9,
    """import folium
import pandas as pd
from pathlib import Path
""",
)
set_code(geo, 16, "spacex_df = pd.read_csv(Path('../data/spacex_launch_geo.csv'))")
set_code(
    geo,
    31,
    """site_map = folium.Map(location=nasa_coordinate, zoom_start=5)
for _, row in launch_sites_df.iterrows():
    coordinate = [row["Lat"], row["Long"]]
    folium.Circle(
        coordinate,
        radius=1000,
        color="#3D8DFF",
        fill=True,
        fill_opacity=0.25,
        popup=row["Launch Site"],
    ).add_to(site_map)
    folium.Marker(
        coordinate,
        popup=row["Launch Site"],
        icon=DivIcon(
            icon_size=(160, 20),
            icon_anchor=(0, 0),
            html=f'<div style="font-size: 12px; color:#17324D;"><b>{row["Launch Site"]}</b></div>',
        ),
    ).add_to(site_map)
site_map
""",
)
set_code(geo, 43, "launch_sites_df['marker_color'] = 'blue'")
set_code(
    geo,
    46,
    """marker_cluster = MarkerCluster().add_to(site_map)
for _, record in spacex_df.iterrows():
    folium.Marker(
        location=[record["Lat"], record["Long"]],
        popup=f'{record["Launch Site"]} | class={record["class"]}',
        icon=folium.Icon(color=record["marker_color"], icon="rocket", prefix="fa"),
    ).add_to(marker_cluster)
site_map
""",
)
set_code(
    geo,
    59,
    """selected_site = launch_sites_df.loc[launch_sites_df["Launch Site"] == "CCAFS LC-40"].iloc[0]
launch_site_coordinate = [float(selected_site["Lat"]), float(selected_site["Long"])]
coastline_coordinate = [28.56230, -80.57000]
distance_coastline = calculate_distance(
    launch_site_coordinate[0], launch_site_coordinate[1],
    coastline_coordinate[0], coastline_coordinate[1],
)
coordinates = [launch_site_coordinate, coastline_coordinate]
distance_coastline
""",
)
set_code(
    geo,
    61,
    """distance_marker = folium.Marker(
    coastline_coordinate,
    icon=DivIcon(
        icon_size=(140, 20),
        icon_anchor=(0, 0),
        html='<div style="font-size: 12px; color:#d35400;"><b>{:.2f} km to coast</b></div>'.format(distance_coastline),
    ),
).add_to(site_map)
site_map
""",
)
set_code(
    geo,
    63,
    """lines = folium.PolyLine(locations=coordinates, weight=2, color="#D1495B")
site_map.add_child(lines)
site_map
""",
)
set_code(
    geo,
    73,
    """city_coordinate = [28.4011, -80.6057]  # Cocoa Beach area
city_distance = calculate_distance(
    launch_site_coordinate[0], launch_site_coordinate[1],
    city_coordinate[0], city_coordinate[1],
)
""",
)
set_code(
    geo,
    74,
    """folium.Marker(
    city_coordinate,
    popup="Nearest reference city",
    icon=folium.Icon(color="purple", icon="home", prefix="fa"),
).add_to(site_map)
folium.PolyLine(
    locations=[launch_site_coordinate, city_coordinate],
    weight=2,
    color="purple",
    dash_array="5, 5",
).add_to(site_map)
""",
)
set_code(
    geo,
    75,
    """Path("../outputs").mkdir(exist_ok=True)
site_map.save("../outputs/launch_sites_map.html")
print({"coastline_distance_km": round(distance_coastline, 2), "city_distance_km": round(city_distance, 2)})
site_map
""",
)
add_reproducibility_note(
    geo,
    """### Reproducibility

The interactive map reads `../data/spacex_launch_geo.csv`, adds site circles, success/failure marker clusters, mouse coordinates, and proximity lines, then saves `../outputs/launch_sites_map.html`.
""",
)
write(geo, "03_folium_launch_sites_completed.ipynb")


# ---------------------------------------------------------------------------
# Machine learning classification
# ---------------------------------------------------------------------------
ml = load("SpaceX-Machine-Learning-Prediction-Part-5-v1(2).ipynb")
set_code(
    ml,
    12,
    """# Dependencies are listed in requirements.txt; this notebook assumes they are installed.
""",
)
set_code(
    ml,
    14,
    """import warnings
warnings.filterwarnings("ignore")

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn import preprocessing
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from sklearn.tree import DecisionTreeClassifier
from sklearn.neighbors import KNeighborsClassifier
""",
)
set_code(ml, 19, "data = pd.read_csv('../data/dataset_part_2.csv')")
set_code(ml, 21, "X = pd.read_csv('../data/dataset_part_3.csv')")
set_code(ml, 25, "Y = data['Class'].to_numpy()")
set_code(
    ml,
    28,
    """transform = preprocessing.StandardScaler()
X = transform.fit_transform(X)
""",
)
set_code(
    ml,
    33,
    """X_train, X_test, Y_train, Y_test = train_test_split(
    X, Y, test_size=0.2, random_state=2
)
""",
)
set_code(
    ml,
    39,
    """parameters = {"C": [0.01, 0.1, 1], "penalty": ["l2"], "solver": ["lbfgs"]}
lr = LogisticRegression(max_iter=1000)
logreg_cv = GridSearchCV(lr, parameters, cv=10)
logreg_cv.fit(X_train, Y_train)
""",
)
set_code(ml, 44, "logreg_test_accuracy = logreg_cv.score(X_test, Y_test)\nprint('test accuracy:', logreg_test_accuracy)")
set_code(
    ml,
    50,
    """parameters = {
    "kernel": ("linear", "rbf", "poly", "sigmoid"),
    "C": np.logspace(-3, 3, 5),
    "gamma": np.logspace(-3, 3, 5),
}
svm = SVC()
svm_cv = GridSearchCV(svm, parameters, cv=10)
svm_cv.fit(X_train, Y_train)
""",
)
set_code(ml, 55, "svm_test_accuracy = svm_cv.score(X_test, Y_test)\nprint('test accuracy:', svm_test_accuracy)")
set_code(
    ml,
    60,
    """parameters = {
    "criterion": ["gini", "entropy"],
    "splitter": ["best", "random"],
    "max_depth": [2 * n for n in range(1, 10)],
    "max_features": [None, "sqrt", "log2"],
    "min_samples_leaf": [1, 2, 4],
    "min_samples_split": [2, 5, 10],
    "random_state": [2],
}
tree = DecisionTreeClassifier()
tree_cv = GridSearchCV(tree, parameters, cv=10)
tree_cv.fit(X_train, Y_train)
""",
)
set_code(ml, 65, "tree_test_accuracy = tree_cv.score(X_test, Y_test)\nprint('test accuracy:', tree_test_accuracy)")
set_code(
    ml,
    70,
    """parameters = {
    "n_neighbors": list(range(1, 11)),
    "algorithm": ["auto", "ball_tree", "kd_tree", "brute"],
    "p": [1, 2],
}
knn = KNeighborsClassifier()
knn_cv = GridSearchCV(knn, parameters, cv=10)
knn_cv.fit(X_train, Y_train)
""",
)
set_code(ml, 75, "knn_test_accuracy = knn_cv.score(X_test, Y_test)\nprint('test accuracy:', knn_test_accuracy)")
set_code(
    ml,
    80,
    """model_results = pd.DataFrame([
    {"model": "Logistic Regression", "cv_accuracy": logreg_cv.best_score_, "test_accuracy": logreg_test_accuracy},
    {"model": "SVM", "cv_accuracy": svm_cv.best_score_, "test_accuracy": svm_test_accuracy},
    {"model": "Decision Tree", "cv_accuracy": tree_cv.best_score_, "test_accuracy": tree_test_accuracy},
    {"model": "KNN", "cv_accuracy": knn_cv.best_score_, "test_accuracy": knn_test_accuracy},
]).sort_values("cv_accuracy", ascending=False)
model_results
""",
)
add_reproducibility_note(
    ml,
    """### Reproducibility

The model uses the one-hot encoded `../data/dataset_part_3.csv`, standardizes the 83 input features, reserves 20% for testing with `random_state=2`, and tunes four classifiers with 10-fold cross-validation.
""",
)
write(ml, "04_machine_learning_completed.ipynb")


print(f"Wrote completed notebooks to {OUT}")
