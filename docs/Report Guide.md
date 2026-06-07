# 项目报告指南

## 环境配置

```bash
python -m venv .venv && source .venv/bin/activate    # 如尚未创建虚拟环境
python -m pip install -r requirements.txt            # 项目依赖
python -m pip install kaleido                        # 报告图表的静态导出后端
```

`kaleido` **不是**项目的运行时依赖，仅供 `scripts/make_report_figures.py` 将 Dashboard 的 Plotly 图表写出为 PNG。首次使用时，Plotly 可能会下载一个用于渲染的小型 Chrome 构建。导出报告 PDF 还需额外安装 `pandoc` 与提供 `xelatex` 的 LaTeX 引擎（TeX Live / MacTeX）。

## 复现报告图表

全部图表由一条脚本生成，它只读取已提交的文件，并写入 `docs/figures/`：

```bash
python scripts/make_report_figures.py
```

这些图与 `app/dashboard.py`、`src/bikeshare/reporting.py` 中**相同的 Plotly 定义**渲染，因此打印出的图与实时 Dashboard 一致（含中文标签）。报告通过 `figures/...` 相对路径嵌入这些 PNG。

同时，运行项目流水线时也会产生部分可交互图像到 `reports/figures/` 下

### 图表与数据源对应

下表按文件名给出每张图的数据源与定义来源；括号内为其在当前报告中的图号（图号按出现顺序自动编排，调整章节顺序后会变化，但文件名与数据源不变）。

| 文件 | 报告图号 | 数据源 | 定义来源 |
|---|---|---|---|
| `fig01_daily_demand.png` | 图1 | `hourly_demand.csv` | Dashboard「每日骑行总量」（px.line） |
| `fig02_hourly_profile.png` | 图2 | `hourly_demand.csv` | Dashboard「小时平均需求」（px.bar） |
| `fig03_weekday_profile.png` | 图3 | `model_features.csv` | Dashboard「星期平均需求」（px.bar，按日均值） |
| `fig13_monthly_demand.png` | 图4 | `model_features.csv` | Dashboard「月每日平均需求」（px.bar） |
| `fig04_weather_corr.png` | 图5 | `hourly_demand.csv` | Dashboard「需求与天气变量相关性」（px.imshow，Teal） |
| `fig06_holiday.png` | 图6 | `model_features.csv` | Dashboard「节假日 vs 非节假日平均需求」（px.bar） |
| `fig05_weather_scenario.png` | 图7 | `hourly_demand.csv` | Dashboard「不同天气的日平均需求」（px.bar，Set2） |
| `fig07_model_metrics.png` | 图8 | 原始指标（见下文数据约定） | Dashboard「模型误差指标对比」（分组 px.bar） |
| `fig08_prediction_comparison.png` | 图9 | `predictions.csv` | Dashboard 预测对比曲线（go.Scatter） |
| `fig14_error_distribution.png` | 图10 | `predictions.csv` | Dashboard「预测误差分布」（px.histogram） |
| `fig09_station_rmse_box.png` | 图11 | `station_model_metrics.csv` | reporting.py「站点净需求 RMSE」（px.box） |
| `fig12_station_example.png` | 图12 | `station_predictions.csv` | Dashboard 单站曲线（go.Scatter） |
| `fig10_station_clusters.png` | 图13 | `station_clusters.csv` | Dashboard「站点画像聚类」（px.scatter） |
| `fig11_station_map.png` | 图14 | `station_hourly.csv` | Dashboard 站点热力图（scatter_map，OSM 底图） |

## 导出报告 PDF

```bash
pandoc docs/project_report.md --pdf-engine=xelatex --resource-path=docs -o docs/project_report.pdf
```
