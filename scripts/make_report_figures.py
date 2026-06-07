"""Render the report figures as static PNGs using **Plotly**, so they match the
charts produced by the project's Streamlit dashboard (`app/dashboard.py`) and
reporting module (`src/bikeshare/reporting.py`).

Figures are written into docs/figures with the dashboard's Chinese labels,
preserving the dashboard's chart definitions and styling.

Run from the repository root:

    python scripts/make_report_figures.py
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

ROOT = Path(__file__).resolve().parents[1]
PROC = ROOT / "data" / "processed"
MODELS = ROOT / "models"
TABLES = ROOT / "reports" / "tables"
OUT = ROOT / "docs" / "figures"

WEATHER_COLS = ["temperature_2m", "relative_humidity_2m", "precipitation", "wind_speed_10m"]

WEEKDAY_ZH = {0: "星期一", 1: "星期二", 2: "星期三", 3: "星期四", 4: "星期五", 5: "星期六", 6: "星期日"}
WEEKDAY_ORDER = [WEEKDAY_ZH[i] for i in range(7)]

# Chinese chart labels, matching app/dashboard.py.
L = {
    "daily_title": "每日骑行总量",
    "date": "日期", "rides": "骑行量",
    "hourly_title": "小时平均需求",
    "hour": "小时", "mean_hourly": "平均小时骑行量",
    "weekday_title": "星期平均需求",
    "weekday": "星期", "mean_daily": "日平均需求",
    "corr_title": "需求与天气变量相关性",
    "weather_title": "不同天气的日平均需求",
    "scenario": "天气状态",
    "holiday_title": "节假日 vs 非节假日平均需求",
    "daytype": "日期类型", "holiday": "节假日", "nonholiday": "非节假日",
    "metrics_title": "模型误差指标对比（测试集）",
    "model": "模型", "value": "误差", "metric": "指标",
    "monthly_title": "月每日平均需求",
    "month": "月份",
    "error_title": "HGB 预测误差分布（测试集）",
    "error": "预测误差（预测 − 真实）", "count": "频数",
    "pred_title": "城市级测试集预测对比（最后 21 天）",
    "time": "时间", "hourly_rides": "小时骑行量",
    "actual": "真实需求",
    "box_title": "Top 站点净需求预测 RMSE 分布",
    "rmse": "RMSE",
    "cluster_title": "站点画像聚类",
    "avg_net": "平均净需求（pickup − dropoff）", "weekend_share": "周末流量占比",
    "map_title": "站点累计净流入空间分布（dropoff − pickup）",
    "net_inflow": "净流入",
    "station_title": "站点净需求预测 — Columbus Circle / Union Station（最后 14 天）",
    "net_demand": "净需求", "actual_net": "真实净需求", "pred": "模型预测（HGB）",
}


def save(fig: go.Figure, name: str, width: int, height: int) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / name
    fig.write_image(path, width=width, height=height, scale=2)
    print(f"wrote {path.relative_to(ROOT)}")


def load_metrics() -> pd.DataFrame:
    """City-level model metrics loaded from the project's actual training output.

    Mirrors bikeshare.modeling.load_metrics so figures stay in sync with the
    committed models/metrics.json instead of hard-coded numbers.
    """
    with (MODELS / "metrics.json").open("r", encoding="utf-8") as fh:
        metrics = json.load(fh)
    return pd.DataFrame(metrics).T


def load_data() -> dict:
    hourly = pd.read_csv(PROC / "hourly_demand.csv", parse_dates=["timestamp"])
    features = pd.read_csv(PROC / "model_features.csv", parse_dates=["timestamp"])
    preds = pd.read_csv(MODELS / "predictions.csv", parse_dates=["timestamp"])
    metrics = load_metrics()
    station_metrics = pd.read_csv(TABLES / "station_model_metrics.csv")
    clusters = pd.read_csv(TABLES / "station_clusters.csv")
    station_preds = pd.read_csv(MODELS / "station_predictions.csv", parse_dates=["timestamp"])
    station_hourly = pd.read_csv(PROC / "station_hourly.csv", parse_dates=["timestamp"])
    return dict(hourly=hourly, features=features, preds=preds, metrics=metrics,
                station_metrics=station_metrics, clusters=clusters,
                station_preds=station_preds, station_hourly=station_hourly)


def weather_daily_summary(hourly: pd.DataFrame) -> pd.DataFrame:
    """Replicates app/dashboard.py weather_daily_summary on the committed data."""
    d = hourly.copy()
    d["date"] = d["timestamp"].dt.date
    daily = d.groupby("date").agg(
        daily_demand=("cnt", "sum"),
        precipitation=("precipitation", "sum"),
        max_temperature=("temperature_2m", "max"),
        min_temperature=("temperature_2m", "min"),
        max_wind_speed=("wind_speed_10m", "max"),
    ).reset_index()
    cond = [daily.precipitation >= 0.5, daily.max_temperature >= 30,
            daily.min_temperature <= 5, daily.max_wind_speed >= 25]
    daily["weather_scenario"] = np.select(cond, ["降水", "高温", "低温", "大风"], default="常规天气")
    summary = daily.groupby("weather_scenario", as_index=False).agg(
        daily_demand=("daily_demand", "mean"), days=("date", "nunique"))
    order = ["常规天气", "降水", "高温", "低温", "大风"]
    summary = pd.DataFrame({"weather_scenario": order}).merge(summary, on="weather_scenario", how="left")
    baseline = float(summary.loc[summary.weather_scenario == "常规天气", "daily_demand"].iloc[0])
    summary["relative_to_normal"] = summary["daily_demand"] / baseline
    return summary


def build(D: dict) -> None:
    hourly, features = D["hourly"], D["features"]

    # fig01 — daily ridership (dashboard: px.line "每日骑行总量")
    daily = hourly.assign(date=hourly["timestamp"].dt.date).groupby("date", as_index=False)["cnt"].sum()
    f = px.line(daily, x="date", y="cnt", title=L["daily_title"])
    f.update_layout(xaxis_title=L["date"], yaxis_title=L["rides"])
    save(f, "fig01_daily_demand.png", 1000, 380)

    # fig02 — hourly profile (dashboard: px.bar "小时平均需求")
    hp = hourly.groupby(hourly["timestamp"].dt.hour)["cnt"].mean().reset_index()
    hp.columns = ["hour", "avg_demand"]
    f = px.bar(hp, x="hour", y="avg_demand", title=L["hourly_title"])
    f.update_layout(xaxis_title=L["hour"], yaxis_title=L["mean_hourly"])
    save(f, "fig02_hourly_profile.png", 640, 380)

    # fig04 — demand-weather correlation (dashboard: px.imshow, Teal, text .2f)
    corr = hourly[["cnt", *WEATHER_COLS]].corr(numeric_only=True)
    f = px.imshow(corr, text_auto=".2f", title=L["corr_title"], color_continuous_scale="Teal")
    save(f, "fig04_weather_corr.png", 560, 460)

    # Daily summary by day_type / weekday / scenario (dashboard "数据概览")
    od = features.assign(
        date=features["timestamp"].dt.date,
        day_type=features["is_holiday"].map({1: L["holiday"], 0: L["nonholiday"]}),
        weekday=features["timestamp"].dt.weekday,
    )
    daily_summary = od.groupby(["date", "day_type", "weekday"], as_index=False)["cnt"].sum().rename(
        columns={"cnt": "daily_demand"})

    # fig03 — weekday profile (dashboard: px.bar "星期平均需求", daily mean)
    wd = daily_summary.assign(name=daily_summary["weekday"].map(WEEKDAY_ZH))
    wd = wd.groupby("name", as_index=False)["daily_demand"].mean()
    wd["name"] = pd.Categorical(wd["name"], categories=WEEKDAY_ORDER, ordered=True)
    wd = wd.sort_values("name")
    f = px.bar(wd, x="name", y="daily_demand", title=L["weekday_title"])
    f.update_layout(xaxis_title=L["weekday"], yaxis_title=L["mean_daily"])
    save(f, "fig03_weekday_profile.png", 640, 380)

    # fig06 — holiday vs non-holiday (dashboard: px.bar "节假日 vs 非节假日平均需求")
    ht = daily_summary.groupby("day_type", as_index=False)["daily_demand"].mean()
    f = px.bar(ht, x="day_type", y="daily_demand", title=L["holiday_title"])
    f.update_layout(xaxis_title=L["daytype"], yaxis_title=L["mean_daily"])
    save(f, "fig06_holiday.png", 520, 380)

    # fig05 — weather scenario (dashboard: px.bar "不同天气的日平均需求", Set2)
    ws = weather_daily_summary(hourly)
    f = px.bar(ws, x="weather_scenario", y="daily_demand",
               text=ws["relative_to_normal"].map(lambda v: f"{v:.2f}x"),
               title=L["weather_title"], color="weather_scenario",
               color_discrete_sequence=px.colors.qualitative.Set2)
    f.update_traces(textposition="outside")
    f.update_layout(showlegend=False, xaxis_title=L["scenario"], yaxis_title=L["mean_daily"])
    save(f, "fig05_weather_scenario.png", 680, 400)

    # fig07 — model error comparison (dashboard: grouped bar; models/metrics.json)
    m = D["metrics"].sort_values("RMSE")
    long = m.reset_index(names="model").melt(id_vars="model", value_vars=["MAE", "RMSE", "MAPE"],
                                             var_name="metric", value_name="value")
    f = px.bar(long, x="model", y="value", color="metric", barmode="group", title=L["metrics_title"])
    f.update_layout(xaxis_title=L["model"], yaxis_title=L["value"], legend_title=L["metric"])
    save(f, "fig07_model_metrics.png", 900, 430)

    # fig13 — monthly mean daily demand (dashboard: px.bar "月每日平均需求")
    md = daily_summary.assign(month=pd.to_datetime(daily_summary["date"]).dt.month)
    md = md.groupby("month", as_index=False)["daily_demand"].mean()
    f = px.bar(md, x="month", y="daily_demand", title=L["monthly_title"])
    f.update_xaxes(dtick=1)
    f.update_layout(xaxis_title=L["month"], yaxis_title=L["mean_daily"])
    save(f, "fig13_monthly_demand.png", 700, 380)

    # fig08 — prediction comparison (dashboard go.Scatter lines; actual + HGB + LSTM, last 21 days)
    preds = D["preds"].sort_values("timestamp")
    tail = preds.tail(24 * 21)
    f = go.Figure()
    f.add_trace(go.Scatter(x=tail["timestamp"], y=tail["actual"], name=L["actual"], mode="lines"))
    f.add_trace(go.Scatter(x=tail["timestamp"], y=tail["hist_gradient_boosting"],
                           name="HistGradientBoosting", mode="lines"))
    if "lstm" in tail.columns:
        f.add_trace(go.Scatter(x=tail["timestamp"], y=tail["lstm"], name="LSTM", mode="lines"))
    f.update_layout(title=L["pred_title"], xaxis_title=L["time"], yaxis_title=L["hourly_rides"],
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0))
    save(f, "fig08_prediction_comparison.png", 1000, 400)

    # fig14 — HGB prediction-error distribution (dashboard: px.histogram "预测误差分布")
    err = preds.assign(error=preds["hist_gradient_boosting"] - preds["actual"])
    f = px.histogram(err, x="error", nbins=40, title=L["error_title"])
    f.update_layout(xaxis_title=L["error"], yaxis_title=L["count"], showlegend=False)
    save(f, "fig14_error_distribution.png", 700, 380)

    # fig09 — station RMSE box (reporting.py: px.box points='all')
    order = ["hist_gradient_boosting", "random_forest", "xgboost", "ridge"]
    sm = D["station_metrics"].copy()
    sm["model"] = pd.Categorical(sm["model"], categories=order, ordered=True)
    f = px.box(sm.sort_values("model"), x="model", y="RMSE", points="all", title=L["box_title"])
    f.update_layout(xaxis_title=L["model"], yaxis_title=L["rmse"])
    save(f, "fig09_station_rmse_box.png", 720, 430)

    # fig10 — cluster profile (dashboard: px.scatter "站点画像聚类")
    cl = D["clusters"].copy()
    f = px.scatter(cl, x="avg_net_demand", y="weekend_share", size="volume_total",
                   color="cluster_label", hover_name="station_name", title=L["cluster_title"])
    f.update_layout(xaxis_title=L["avg_net"], yaxis_title=L["weekend_share"], legend_title="")
    save(f, "fig10_station_clusters.png", 820, 480)

    # fig11 — station net-inflow map (dashboard: scatter_map OSM; all-time aggregate)
    sh = D["station_hourly"]
    agg = sh.groupby("station_name", as_index=False).agg(
        pickup=("pickup_count", "sum"), dropoff=("dropoff_count", "sum"),
        latitude=("latitude", "median"), longitude=("longitude", "median"))
    agg = agg.dropna(subset=["latitude", "longitude"])
    agg["net_inflow"] = agg["dropoff"] - agg["pickup"]
    agg["activity"] = (agg["pickup"] + agg["dropoff"]).clip(lower=1)
    limit = max(float(agg["net_inflow"].abs().quantile(0.95)), 1.0)
    f = px.scatter_map(
        agg, lat="latitude", lon="longitude", color="net_inflow", size="activity", size_max=34,
        hover_name="station_name", color_continuous_scale=[(0.0, "#2563eb"), (0.5, "#f8fafc"), (1.0, "#dc2626")],
        range_color=(-limit, limit), zoom=11.5, map_style="open-street-map", title=L["map_title"],
        center={"lat": float(agg["latitude"].mean()), "lon": float(agg["longitude"].mean())})
    f.update_layout(margin={"l": 0, "r": 0, "t": 48, "b": 0}, coloraxis_colorbar={"title": L["net_inflow"]})
    save(f, "fig11_station_map.png", 900, 600)

    # fig12 — single-station net demand (dashboard go.Scatter; Columbus Circle, last 14 days)
    name = "Columbus Circle / Union Station"
    sub = D["station_preds"][D["station_preds"]["station_name"] == name].sort_values("timestamp").tail(24 * 14)
    f = go.Figure()
    f.add_trace(go.Scatter(x=sub["timestamp"], y=sub["actual"], name=L["actual_net"], mode="lines"))
    f.add_trace(go.Scatter(x=sub["timestamp"], y=sub["hist_gradient_boosting"], name=L["pred"], mode="lines"))
    f.update_layout(title=L["station_title"], xaxis_title=L["time"], yaxis_title=L["net_demand"],
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0))
    save(f, "fig12_station_example.png", 1000, 380)


def main() -> None:
    build(load_data())
    print(f"All figures written to {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
