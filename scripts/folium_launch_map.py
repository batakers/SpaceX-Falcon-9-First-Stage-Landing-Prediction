"""Generate the interactive Folium launch-site map used in the capstone."""

from math import atan2, cos, radians, sin, sqrt
from pathlib import Path

import folium
import pandas as pd
from folium.features import DivIcon
from folium.plugins import MarkerCluster, MousePosition


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "spacex_launch_geo.csv"
OUTPUT = ROOT / "outputs" / "launch_sites_map.html"


def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Return the great-circle distance between two coordinates in kilometres."""

    earth_radius_km = 6373.0
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlon, dlat = lon2 - lon1, lat2 - lat1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    return earth_radius_km * 2 * atan2(sqrt(a), sqrt(1 - a))


def build_map() -> tuple[folium.Map, dict[str, float]]:
    df = pd.read_csv(DATA)
    launch_sites = df.groupby("Launch Site", as_index=False).first()[["Launch Site", "Lat", "Long"]]
    nasa_coordinate = [29.559684888503615, -95.0830971930759]
    site_map = folium.Map(location=nasa_coordinate, zoom_start=5)

    for _, row in launch_sites.iterrows():
        coordinate = [row["Lat"], row["Long"]]
        folium.Circle(
            coordinate,
            radius=1000,
            color="#3D8DFF",
            fill=True,
            fill_opacity=0.25,
            popup=row["Launch Site"],
        ).add_to(site_map)
        folium.Marker(coordinate, popup=row["Launch Site"]).add_to(site_map)

    df["marker_color"] = df["class"].map({1: "green", 0: "red"})
    marker_cluster = MarkerCluster().add_to(site_map)
    for _, row in df.iterrows():
        folium.Marker(
            [row["Lat"], row["Long"]],
            popup=f"{row['Launch Site']} | class={row['class']}",
            icon=folium.Icon(color=row["marker_color"], icon="rocket", prefix="fa"),
        ).add_to(marker_cluster)

    formatter = "function(num) {return L.Util.formatNum(num, 5);};"
    MousePosition(
        position="topright",
        separator=" Long: ",
        empty_string="NaN",
        lng_first=False,
        num_digits=5,
        prefix="Lat:",
        lat_formatter=formatter,
        lng_formatter=formatter,
    ).add_to(site_map)

    selected = launch_sites.loc[launch_sites["Launch Site"] == "CCAFS LC-40"].iloc[0]
    launch_coordinate = [float(selected["Lat"]), float(selected["Long"])]
    coastline_coordinate = [28.56230, -80.57000]
    city_coordinate = [28.4011, -80.6057]
    coast_distance = calculate_distance(*launch_coordinate, *coastline_coordinate)
    city_distance = calculate_distance(*launch_coordinate, *city_coordinate)

    folium.Marker(
        coastline_coordinate,
        icon=DivIcon(
            icon_size=(140, 20),
            icon_anchor=(0, 0),
            html=f'<div style="font-size: 12px; color:#d35400;"><b>{coast_distance:.2f} km to coast</b></div>',
        ),
    ).add_to(site_map)
    folium.PolyLine([launch_coordinate, coastline_coordinate], color="#D1495B", weight=2).add_to(site_map)
    folium.Marker(city_coordinate, popup="Nearest reference city").add_to(site_map)
    folium.PolyLine([launch_coordinate, city_coordinate], color="purple", weight=2, dash_array="5, 5").add_to(site_map)

    return site_map, {"coastline_distance_km": coast_distance, "city_distance_km": city_distance}


if __name__ == "__main__":
    OUTPUT.parent.mkdir(exist_ok=True)
    site_map, distances = build_map()
    site_map.save(OUTPUT)
    print({key: round(value, 2) for key, value in distances.items()})
    print(f"Saved {OUTPUT}")

