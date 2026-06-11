# 共享单车需求预测与调度分析

Capital Bikeshare 三年多源增强项目：融合 2023-2025 官方骑行记录、Open-Meteo 历史天气和美国联邦节假日特征，完成小时级需求预测、模型对比、站点聚类、Top 20 站点预测、调度分析和 Streamlit Dashboard。

## 项目亮点

- 多源数据融合：Capital Bikeshare trip history + Open-Meteo hourly weather。
- 三年时间线：默认处理 `202301-202512`，支持跨年趋势和泛化分析。
- 节假日增强：加入美国联邦节假日、节前、节后特征。
- 六类模型对比：Seasonal Naive、Ridge、Random Forest、HistGradientBoosting、XGBoost、PyTorch LSTM。
- 时间切分评估：前 80% 训练、后 20% 测试，避免时间泄漏。
- 调度分析：按站点小时级 pickup/dropoff/net demand 给出补车/清车建议。
- 站点增强：Top 站点聚类画像 + Top 20 站点净需求预测。
- 可交互展示：Streamlit 五页签 Dashboard，适合课堂演示和报告截图。

## 运行步骤

```powershell
python -m pip install -r requirements.txt
python -m bikeshare.pipeline
streamlit run app/dashboard.py
```

## 输出文件

- `data/processed/hourly_demand.csv`：融合天气后的小时级总体需求表。
- `data/processed/model_features.csv`：训练用特征表。
- `data/processed/station_hourly.csv`：Top 站点小时级 pickup/dropoff/net demand。
- `models/*.joblib`：训练后的模型与 LSTM 权重包。
- `models/metrics.json`：模型评估指标。
- `models/training_info.json`：训练划分、LSTM 设备和参数信息。
- `models/predictions.csv`：测试集预测结果。
- `models/station_predictions.csv`：Top 20 站点测试集净需求预测结果。
- `reports/tables/dispatch_recommendations.csv`：调度建议表。
- `reports/tables/station_clusters.csv`：站点聚类画像。
- `reports/tables/station_model_metrics.csv`：Top 20 站点预测指标。
- `reports/project_summary.md`：报告可直接引用的项目摘要。

## 数据来源

- Capital Bikeshare System Data: https://capitalbikeshare.com/system-data
- Open-Meteo Historical Weather API: https://open-meteo.com/en/docs/historical-weather-api

## LSTM 与 GPU

LSTM 使用 PyTorch 实现，默认用过去 24 小时的连续特征预测下一小时需求。训练时会自动选择 `cuda`，如果当前 PyTorch 是 CPU 版本或没有可用 CUDA，则回退到 `cpu`。可用设备会写入 `models/training_info.json`。

如果数据和天气已经生成，只想重训模型：

```powershell
@'
import pandas as pd
from bikeshare.modeling import train_models
features = pd.read_csv("data/processed/model_features.csv", parse_dates=["timestamp"])
train_models(features, include_lstm=True)
'@ | .\.venv312\Scripts\python.exe -
```
