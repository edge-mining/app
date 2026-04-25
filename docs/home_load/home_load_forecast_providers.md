# Home Load Forecast Providers

This document describes all available **Energy Load Forecast Providers** in
EdgeMining. Each provider implements `EnergyLoadForecastProviderPort` and
produces a `LoadEnergyConsumption` forecast for a configurable time horizon.

Providers are selected per-device via the `EnergyLoadForecastProviderAdapter`
enum and configured through a corresponding dataclass.

---

## Provider Summary

| Adapter Enum | Provider Class | Category | Dependencies | Pre-trained Model |
|---|---|---|---|---|
| `DUMMY` | `DummyEnergyLoadForecastProvider` | Testing | None | No |
| `NAIVE_LAST_HOUR` | `NaiveLastHourForecastProvider` | Baseline | None | No |
| `NAIVE_PERSISTENCE` | `NaivePersistenceForecastProvider` | Baseline | None | No |
| `SEASONAL_BASELINE` | `SeasonalBaselineForecastProvider` | Statistical | None | No |
| `TYPICAL_PROFILE` | `TypicalProfileForecastProvider` | Statistical | None | No |
| `STATSMODELS` | `StatsmodelsForecastProvider` | ML | `statsmodels` | Yes |
| `XGBOOST` | `XGBoostForecastProvider` | ML | `xgboost` | Yes |
| `SKFORECAST` | `SkforecastForecastProvider` | ML | `skforecast`, `scikit-learn` | Yes |

---

## Baseline Providers

### DUMMY

**Purpose**: development and testing only. Generates random power values so
that the rest of the pipeline can run without real sensor data.

**Algorithm**: if history is available, takes the last interval's average power
as baseline; otherwise picks a random value in `[200, load_power_max]`. Each
forecast hour applies small random noise.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `load_power_max` | `float` | `500.0` | Upper bound for generated power (W) |

| Property | Value |
|---|---|
| Min required history | 0 hours |
| Forecast horizon | N/A (config-driven) |
| File | `adapters/domain/home_load/forecast_providers/dummy.py` |

---

### NAIVE_LAST_HOUR

**Purpose**: simplest real-world baseline. Repeats the most recent measured
power into the future — useful as a short-horizon fallback when no other
provider is available.

**Algorithm**: computes the average power over the last 1 hour of history and
projects that flat value for every forecast hour. Falls back to the overall
history average if the last hour has no data.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `hours_ahead` | `int` | `3` | Forecast horizon in hours |

| Property | Value |
|---|---|
| Min required history | 1 hour |
| Best for | Very short horizons (1–3 h), instant fallback |
| File | `adapters/domain/home_load/forecast_providers/naive_last_hour.py` |

---

### NAIVE_PERSISTENCE

**Purpose**: strong intra-day baseline that assumes tomorrow looks like
yesterday.

**Algorithm**: builds an `hour → power` map from the same calendar date
`delta_days` ago, then replays that 24 h profile forward. Missing hours fall
back to the global history average.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `hours_ahead` | `int` | `24` | Forecast horizon in hours |
| `delta_days` | `int` | `1` | How many days back to look (1 = yesterday) |

| Property | Value |
|---|---|
| Min required history | `delta_days × 24` hours (default 24) |
| Best for | Devices with regular daily patterns; ML-free fallback |
| File | `adapters/domain/home_load/forecast_providers/naive_persistence.py` |

---

## Statistical Providers

### SEASONAL_BASELINE

**Purpose**: lightweight statistical forecast that captures weekly
seasonality without any ML dependency.

**Algorithm**: groups all history by `(day_of_week, hour_of_day)` and averages
each slot. For each forecast hour, looks up the matching `(dow, hod)` bucket.
Falls back to the global average across all slots.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `hours_ahead` | `int` | `3` | Forecast horizon in hours |
| `weeks_lookback` | `int` | `4` | Weeks of history to consider |

| Property | Value |
|---|---|
| Min required history | 0 hours (degrades gracefully) |
| Best for | Quick start with ≥1 week of data |
| File | `adapters/domain/home_load/forecast_providers/seasonal_baseline.py` |

---

### TYPICAL_PROFILE

**Purpose**: more refined statistical forecast that adds **monthly** grouping
on top of weekly seasonality. Captures how consumption changes across seasons
(e.g. heating in winter vs. cooling in summer).

**Algorithm**: two-level profile lookup:
1. **Primary**: `(month, day_of_week, hour_of_day)` — average power for this
   exact month + weekday + hour combination.
2. **Fallback**: `(day_of_week, hour_of_day)` — ignores month, same as
   `SEASONAL_BASELINE` logic.
3. **Global**: overall average if both levels miss.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `hours_ahead` | `int` | `24` | Forecast horizon in hours |
| `weeks_lookback` | `int` | `8` | Weeks of history to consider |

| Property | Value |
|---|---|
| Min required history | `weeks_lookback × 168` hours (default 1 344 h ≈ 8 weeks) |
| Best for | Devices with seasonal patterns; new installations with ≥2 months of data |
| File | `adapters/domain/home_load/forecast_providers/typical_profile.py` |

---

## ML Providers

All ML providers share these traits:

- **Lazy imports**: heavy dependencies (`statsmodels`, `xgboost`, `skforecast`)
  are imported at runtime. If a library is missing, the provider gracefully
  returns `None` (except `STATSMODELS` which raises).
- **Pre-trained model support**: each looks for an active `LoadConsumptionModel`
  in the model repository. If found, the serialised model is loaded via
  `pickle`. Otherwise, the provider fits on-the-fly from history.
- **Nightly training**: `LoadForecastModelTrainingService.train_all()` trains
  all ML providers (HW, XGBoost, skforecast), evaluates on a 24 h holdout,
  and promotes the best model (lowest MAE) to active.

### STATSMODELS

**Purpose**: Holt-Winters exponential smoothing — a classical time-series
method that captures trend and daily seasonality (period = 24 h).

**Algorithm**: `ExponentialSmoothing(trend="add", seasonal="add",
seasonal_periods=24)` from `statsmodels`. Fits on hourly power series derived
from history intervals. Forecast calls `fitted.forecast(hours_ahead)`.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `hours_ahead` | `int` | `3` | Forecast horizon in hours |
| `weeks_lookback` | `int` | `8` | Weeks of history for training |
| `method` | `str` | `"hw"` | Model family (`"hw"` = Holt-Winters; `"sarima"` reserved) |
| `seasonal_periods` | `int` | `24` | Seasonal cycle length in hours |

| Property | Value |
|---|---|
| Min required history | `seasonal_periods × 2` hours (default 48) |
| Best for | Smooth loads with clear 24 h seasonality (e.g. household aggregate) |
| File | `adapters/domain/home_load/forecast_providers/statsmodels_hw.py` |

---

### XGBOOST

**Purpose**: gradient-boosted trees using hand-crafted calendar + lag features
with iterative 1-step-ahead prediction.

**Algorithm**: trains an `XGBRegressor` on a supervised dataset built from:
- **Calendar features**: `hour_of_day`, `day_of_week`, `is_weekend`, `month`.
- **Lag features**: power at `t-1h`, `t-2h`, `t-3h`, `t-24h`, `t-168h`.

Prediction iterates 1 step at a time, appending the previous prediction as
the next lag input.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `hours_ahead` | `int` | `3` | Forecast horizon in hours |
| `weeks_lookback` | `int` | `8` | Weeks of history for training |
| `n_estimators` | `int` | `100` | Number of boosting rounds |
| `max_depth` | `int` | `6` | Maximum tree depth |
| `learning_rate` | `float` | `0.1` | Boosting learning rate |

| Property | Value |
|---|---|
| Min required history | `168 + 48 + hours_ahead` hours (default 219) |
| Best for | Non-linear patterns, devices with strong weekly periodicity |
| File | `adapters/domain/home_load/forecast_providers/xgboost_provider.py` |

---

### SKFORECAST

**Purpose**: auto-regressive multi-step forecasting via `skforecast`'s
`ForecasterRecursive`, wrapping **any** scikit-learn regressor. The forecaster
feeds its own predictions back as input for subsequent steps, producing native
multi-step forecasts without manual lag iteration.

**Algorithm**: `ForecasterRecursive(estimator=<sklearn model>, lags=num_lags)`
fits on hourly power series. Prediction calls `forecaster.predict(steps=N)`.

**Supported sklearn backends** (selected via `sklearn_model` config string):

| Backend | Strengths | Best for |
|---|---|---|
| `RandomForestRegressor` | Robust to outlier, feature importance | Medium-large datasets |
| `GradientBoostingRegressor` | High accuracy, handles non-linearity | Production |
| `ExtraTreesRegressor` | Fast training, good trade-off | Quick screening |
| `KNeighborsRegressor` | No heavy training, adaptive | Regular profiles |
| `Ridge` | Interpretable, very fast | Linear relationships |
| `Lasso` | Sparse features, fast | Feature selection |
| `ElasticNet` | Mix of Ridge + Lasso | Balanced regularisation |
| `AdaBoostRegressor` | Adaptive boosting | Bias reduction |
| `MLPRegressor` | Captures complex patterns | Large datasets |
| `SVR` | Good on small datasets | Low-data scenarios |

| Parameter | Type | Default | Description |
|---|---|---|---|
| `hours_ahead` | `int` | `24` | Forecast horizon in hours |
| `weeks_lookback` | `int` | `8` | Weeks of history for training |
| `sklearn_model` | `str` | `"RandomForestRegressor"` | Name of the sklearn regressor class |
| `num_lags` | `int` | `72` | Number of lag observations used as features |

| Property | Value |
|---|---|
| Min required history | `num_lags + 48 + hours_ahead` hours (default 144) |
| Best for | General-purpose ML forecasting with model competition |
| File | `adapters/domain/home_load/forecast_providers/skforecast_provider.py` |

#### Optuna Bayesian Tuning (F6)

The `SkforecastForecastProvider.tune()` static method runs Bayesian
hyperparameter optimisation via `optuna` + `bayesian_search_forecaster`.
It searches:

- **Lag count**: categorical over `[24, 48, 72]`
- **Model hyperparameters**: per-model search spaces (e.g. `n_estimators`,
  `max_depth`, `learning_rate`, `alpha`, `n_neighbors`)

The training service calls `tune()` automatically during nightly training
(configurable via `perform_tuning` / `tuning_trials` parameters). Best
parameters are stored in `LoadConsumptionModel.tuning_params`.

#### Rolling-Window Backtesting (F7)

The `SkforecastForecastProvider.backtest()` static method evaluates a fitted
forecaster on the full training set using `backtesting_forecaster` with
`TimeSeriesFold`. Returns:

- `backtest_mae` — MAE across all folds
- `backtest_rmse` — RMSE across all folds
- `backtest_folds` — number of evaluation windows

Backtesting runs automatically after training. Results are stored on the
`LoadConsumptionModel` entity alongside the holdout metrics.

---

## Choosing a Provider

```
Is this for development/testing?
  └─ Yes → DUMMY

Do you have < 1 hour of history?
  └─ Yes → NAIVE_LAST_HOUR (flat repeat of last reading)

Do you have ~ 1 day of history?
  └─ Yes → NAIVE_PERSISTENCE (yesterday's profile)

Do you have 1–4 weeks of history?
  └─ Yes → SEASONAL_BASELINE (weekly pattern average)

Do you have 2+ months of history?
  └─ Yes → TYPICAL_PROFILE (monthly + weekly pattern)

Do you have 1+ week and want ML?
  └─ Yes → STATSMODELS (Holt-Winters) or XGBOOST

Do you have 1+ week, want best accuracy, and can install skforecast?
  └─ Yes → SKFORECAST (auto-regressive multi-model with tuning)
```

In production, **SKFORECAST** is recommended as the primary provider. The
nightly training service automatically competes Holt-Winters, XGBoost, and
skforecast models, promoting the best one. The simpler providers
(`NAIVE_PERSISTENCE`, `SEASONAL_BASELINE`) serve as robust fallbacks.

---

## Architecture

### Port & Adapter Pattern

```
Domain                          Adapters
┌──────────────────┐           ┌───────────────────────────┐
│ EnergyLoadFore-  │           │ DummyProvider             │
│ castProviderPort │◄──────────│ NaiveLastHourProvider     │
│                  │           │ NaivePersistenceProvider  │
│  + adapter_type  │           │ SeasonalBaselineProvider  │
│  + min_history   │           │ TypicalProfileProvider    │
│  + get_forecast()│           │ StatsmodelsProvider       │
│                  │           │ XGBoostProvider           │
│                  │           │ SkforecastProvider        │
└──────────────────┘           └───────────────────────────┘
```

Each provider has:

1. **Enum value** in `EnergyLoadForecastProviderAdapter` (domain layer)
2. **Config dataclass** in `shared/adapter_configs/home_load.py`
3. **Factory class** implementing `EnergyLoadForecastAdapterFactory`
4. **Schema class** in `adapters/domain/home_load/schemas.py`
5. **Wiring** in `AdapterService` factory dispatch + `adapter_maps`

### Shared Feature Engineering

ML providers share helper functions from
`adapters/domain/home_load/forecast_providers/features.py`:

| Function | Used by | Description |
|---|---|---|
| `intervals_to_hourly_series()` | HW, XGB, Skforecast | Converts `LoadEnergyConsumption` intervals to `[(timestamp, power)]` |
| `fill_missing_hours()` | HW, XGB, Skforecast | Forward-fills gaps in hourly series |
| `build_calendar_features()` | XGB | Extracts `[hour, dow, is_weekend, month]` |
| `build_lag_features()` | XGB | Creates lag columns `[1h, 2h, 3h, 24h, 168h]` |
| `prepare_supervised_dataset()` | XGB | Combines calendar + lag features into `(X, y)` |

### Model Lifecycle

```
Nightly Training (04:00)
  │
  ├─ For each enabled device:
  │   ├─ Fetch 8 weeks of history
  │   ├─ Split: train (all - 24h) / holdout (last 24h)
  │   │
  │   ├─ _train_hw()         → LoadConsumptionModel (STATSMODELS)
  │   ├─ _train_xgb()        → LoadConsumptionModel (XGBOOST)
  │   └─ _train_skforecast() → LoadConsumptionModel (SKFORECAST)
  │       ├─ Optuna tuning (optional, default ON)
  │       └─ Rolling-window backtesting
  │
  │   Compare MAE → promote best → is_active = True
  │   Persist all models to LoadConsumptionModelRepository
  │
  └─ Done

Forecast (every 5s optimisation loop)
  │
  ├─ Provider checks model_repo for active model
  ├─ If found → pickle.loads() → predict
  └─ If not   → fit on-the-fly from history → predict
```

---

## LoadConsumptionModel Entity

The `LoadConsumptionModel` entity stores trained model metadata and weights:

| Field | Type | Description |
|---|---|---|
| `device_id` | `Optional[EntityId]` | Device this model was trained for (`None` = aggregate) |
| `adapter_type` | `EnergyLoadForecastProviderAdapter` | Which ML provider created it |
| `trained_at` | `Optional[datetime]` | Training timestamp |
| `mae` | `Optional[float]` | Mean Absolute Error on 24 h holdout |
| `rmse` | `Optional[float]` | Root Mean Squared Error on 24 h holdout |
| `samples_used` | `int` | Number of training data points |
| `is_active` | `bool` | Whether this model is the current production model |
| `model_bytes` | `Optional[bytes]` | Serialised model (pickle) |
| `tuning_params` | `Optional[dict]` | Best hyperparameters from Optuna tuning |
| `backtest_mae` | `Optional[float]` | MAE from rolling-window backtesting |
| `backtest_rmse` | `Optional[float]` | RMSE from rolling-window backtesting |
| `backtest_folds` | `int` | Number of backtesting evaluation folds |
