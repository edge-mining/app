<script setup lang="ts">
import { computed, ref, watch } from "vue";
import { PhInfo, PhX } from "@phosphor-icons/vue";

const props = defineProps<{
  adapterType: string;
}>();

const open = defineModel<boolean>("open", { default: false });
const activeTab = ref<"overview" | "technical">("overview");

watch([() => props.adapterType, open], () => {
  activeTab.value = "overview";
});

interface ParamInfo {
  name: string;
  type: string;
  default: string;
  description: string;
  values?: string[];
}

interface ProviderInfo {
  name: string;
  category: string;
  categoryColor: string;
  summary: string;
  description: string;
  algorithm: string;
  minHistory: string;
  bestFor: string;
  requiresModel: boolean;
  params: ParamInfo[];
}

const providersInfo: Record<string, ProviderInfo> = {
  dummy: {
    name: "Dummy",
    category: "Testing",
    categoryColor: "badge-neutral",
    summary: "Generates random power values for testing. Use it to verify the pipeline works without real data.",
    description: "Development and testing only. Generates random power values so the pipeline can run without real sensor data.",
    algorithm: "Uses last interval's average power as baseline (or random value in [200, load_power_max]). Each forecast hour applies small random noise.",
    minHistory: "0 hours",
    bestFor: "Testing & development",
    requiresModel: false,
    params: [
      { name: "load_power_max", type: "float", default: "500.0", description: "Upper bound for generated power (W)" },
    ],
  },
  naive_last_hour: {
    name: "Naive Last Hour",
    category: "Baseline",
    categoryColor: "badge-info",
    summary: "Repeats the last measured power into the future. The simplest real-world baseline — no history needed beyond 1 hour.",
    description: "Simplest real-world baseline. Repeats the most recent measured power into the future.",
    algorithm: "Computes average power over the last 1 hour and projects that flat value for every forecast hour. Falls back to overall history average.",
    minHistory: "1 hour",
    bestFor: "Very short horizons (1–3 h), instant fallback",
    requiresModel: false,
    params: [
      { name: "hours_ahead", type: "int", default: "3", description: "Forecast horizon in hours" },
    ],
  },
  naive_persistence: {
    name: "Naive Persistence",
    category: "Baseline",
    categoryColor: "badge-info",
    summary: "Assumes tomorrow looks like yesterday. Replays the same day's profile shifted forward — strong baseline for regular routines.",
    description: "Strong intra-day baseline that assumes tomorrow looks like yesterday.",
    algorithm: "Builds an hour→power map from the same calendar date delta_days ago, then replays that 24h profile forward. Missing hours fall back to global average.",
    minHistory: "delta_days × 24 hours (default 24)",
    bestFor: "Devices with regular daily patterns; ML-free fallback",
    requiresModel: false,
    params: [
      { name: "hours_ahead", type: "int", default: "24", description: "Forecast horizon in hours" },
      { name: "delta_days", type: "int", default: "1", description: "How many days back to look (1 = yesterday)" },
    ],
  },
  seasonal_baseline: {
    name: "Seasonal Baseline",
    category: "Statistical",
    categoryColor: "badge-warning",
    summary: "Averages consumption by weekday and hour. Captures weekly patterns without any ML — works well with just 1 week of data.",
    description: "Lightweight statistical forecast that captures weekly seasonality without any ML dependency.",
    algorithm: "Groups history by (day_of_week, hour_of_day) and averages each slot. For each forecast hour, looks up the matching bucket.",
    minHistory: "0 hours (degrades gracefully)",
    bestFor: "Quick start with ≥1 week of data",
    requiresModel: false,
    params: [
      { name: "hours_ahead", type: "int", default: "3", description: "Forecast horizon in hours" },
      { name: "weeks_lookback", type: "int", default: "4", description: "Weeks of history to consider" },
    ],
  },
  typical_profile: {
    name: "Typical Profile",
    category: "Statistical",
    categoryColor: "badge-warning",
    summary: "Like Seasonal Baseline but adds monthly grouping. Captures how consumption changes across seasons (heating vs. cooling).",
    description: "Refined statistical forecast with monthly grouping on top of weekly seasonality. Captures seasonal consumption changes (e.g. heating in winter vs. cooling in summer).",
    algorithm: "Two-level profile lookup: (1) month + day_of_week + hour_of_day, (2) fallback to day_of_week + hour_of_day, (3) global average.",
    minHistory: "weeks_lookback × 168 hours (default 1344 h ≈ 8 weeks)",
    bestFor: "Devices with seasonal patterns; ≥2 months of data",
    requiresModel: false,
    params: [
      { name: "hours_ahead", type: "int", default: "24", description: "Forecast horizon in hours" },
      { name: "weeks_lookback", type: "int", default: "8", description: "Weeks of history to consider" },
    ],
  },
  statsmodels: {
    name: "Statsmodels (Holt-Winters)",
    category: "ML",
    categoryColor: "badge-secondary",
    summary: "Classical exponential smoothing that captures trend and 24h seasonality. Good for smooth, periodic loads like household aggregates.",
    description: "Holt-Winters exponential smoothing — a classical time-series method that captures trend and daily seasonality (period = 24h).",
    algorithm: "ExponentialSmoothing(trend='add', seasonal='add', seasonal_periods=24). Fits on hourly power series. Forecast calls fitted.forecast(hours_ahead).",
    minHistory: "seasonal_periods × 2 hours (default 48)",
    bestFor: "Smooth loads with clear 24h seasonality (e.g. household aggregate)",
    requiresModel: true,
    params: [
      { name: "hours_ahead", type: "int", default: "3", description: "Forecast horizon in hours" },
      { name: "weeks_lookback", type: "int", default: "8", description: "Weeks of history for training" },
      { name: "method", type: "str", default: "hw", description: "Model family", values: ["hw", "sarima"] },
      { name: "seasonal_periods", type: "int", default: "24", description: "Seasonal cycle length in hours" },
    ],
  },
  xgboost: {
    name: "XGBoost",
    category: "ML",
    categoryColor: "badge-secondary",
    summary: "Gradient-boosted trees with calendar and lag features. Excels at non-linear patterns and strong weekly periodicity.",
    description: "Gradient-boosted trees using calendar + lag features with iterative 1-step-ahead prediction.",
    algorithm: "XGBRegressor trained on: hour_of_day, day_of_week, is_weekend, month, plus lags at t-1h, t-2h, t-3h, t-24h, t-168h. Predicts iteratively.",
    minHistory: "168 + 48 + hours_ahead hours (default 219)",
    bestFor: "Non-linear patterns, devices with strong weekly periodicity",
    requiresModel: true,
    params: [
      { name: "hours_ahead", type: "int", default: "3", description: "Forecast horizon in hours" },
      { name: "weeks_lookback", type: "int", default: "8", description: "Weeks of history for training" },
      { name: "n_estimators", type: "int", default: "100", description: "Number of boosting rounds" },
      { name: "max_depth", type: "int", default: "6", description: "Maximum tree depth" },
      { name: "learning_rate", type: "float", default: "0.1", description: "Boosting learning rate" },
    ],
  },
  skforecast: {
    name: "Skforecast",
    category: "ML",
    categoryColor: "badge-secondary",
    summary: "Auto-regressive multi-step forecasting with any scikit-learn model. Supports Bayesian hyperparameter tuning and backtesting — best overall accuracy.",
    description: "Auto-regressive multi-step forecasting wrapping any scikit-learn regressor. Native multi-step forecasts without manual lag iteration.",
    algorithm: "ForecasterRecursive(estimator=<sklearn model>, lags=num_lags). Fits on hourly power series. Supports Optuna Bayesian tuning and rolling-window backtesting.",
    minHistory: "num_lags + 48 + hours_ahead hours (default 144)",
    bestFor: "General-purpose ML forecasting with model competition",
    requiresModel: true,
    params: [
      { name: "hours_ahead", type: "int", default: "24", description: "Forecast horizon in hours" },
      { name: "weeks_lookback", type: "int", default: "8", description: "Weeks of history for training" },
      {
        name: "sklearn_model",
        type: "str",
        default: "RandomForestRegressor",
        description: "Name of the sklearn regressor class",
        values: [
          "RandomForestRegressor",
          "GradientBoostingRegressor",
          "ExtraTreesRegressor",
          "KNeighborsRegressor",
          "Ridge",
          "Lasso",
          "ElasticNet",
          "AdaBoostRegressor",
          "MLPRegressor",
          "SVR",
        ],
      },
      { name: "num_lags", type: "int", default: "72", description: "Number of lag observations used as features" },
    ],
  },
};

const info = computed(() => providersInfo[props.adapterType] ?? null);
</script>

<template>
  <!-- Info trigger button -->
  <button
    v-if="info"
    type="button"
    class="btn btn-ghost btn-xs btn-circle"
    title="Provider info"
    @click.stop.prevent="open = true"
  >
    <PhInfo :size="16" class="text-info" />
  </button>

  <!-- Info modal -->
  <Teleport to="body">
    <div v-if="open && info" class="fixed inset-0 z-[9999] flex items-center justify-center">
      <div class="fixed inset-0 bg-black/50" @click="open = false"></div>
      <div class="relative z-10 bg-base-100 rounded-2xl shadow-xl max-w-lg w-full mx-4 p-6 max-h-[80vh] overflow-y-auto">
        <button type="button" class="btn btn-sm btn-circle btn-ghost absolute right-3 top-3" @click="open = false">
          <PhX :size="16" />
        </button>

        <!-- Header -->
        <h3 class="font-bold text-lg flex items-center gap-2 pr-8">
          {{ info.name }}
          <span class="badge badge-sm" :class="info.categoryColor">{{ info.category }}</span>
          <span v-if="info.requiresModel" class="badge badge-sm badge-accent">Requires Training</span>
        </h3>

        <!-- Tabs -->
        <div class="tabs tabs-bordered mt-3">
          <button
            type="button"
            class="tab"
            :class="{ 'tab-active': activeTab === 'overview' }"
            @click="activeTab = 'overview'"
          >
            Overview
          </button>
          <button
            type="button"
            class="tab"
            :class="{ 'tab-active': activeTab === 'technical' }"
            @click="activeTab = 'technical'"
          >
            Technical Details
          </button>
        </div>

        <!-- Overview Tab -->
        <div v-if="activeTab === 'overview'" class="mt-3 space-y-3">
          <p class="text-sm text-base-content/80 leading-relaxed">{{ info.summary }}</p>

          <div class="grid grid-cols-2 gap-2">
            <div class="bg-base-200/50 rounded-lg px-3 py-2">
              <div class="text-[10px] uppercase tracking-wider text-base-content/40">Min History</div>
              <div class="text-sm font-medium">{{ info.minHistory }}</div>
            </div>
            <div class="bg-base-200/50 rounded-lg px-3 py-2">
              <div class="text-[10px] uppercase tracking-wider text-base-content/40">Best For</div>
              <div class="text-sm font-medium">{{ info.bestFor }}</div>
            </div>
          </div>
        </div>

        <!-- Technical Details Tab -->
        <div v-if="activeTab === 'technical'" class="mt-3 space-y-3">
          <!-- Algorithm -->
          <div>
            <div class="text-xs font-semibold text-base-content/50 uppercase tracking-wider mb-1">Algorithm</div>
            <p class="text-sm text-base-content/60 bg-base-200/30 rounded-lg px-3 py-2">{{ info.algorithm }}</p>
          </div>

          <!-- Parameters -->
          <div v-if="info.params.length > 0">
            <div class="text-xs font-semibold text-base-content/50 uppercase tracking-wider mb-1">Parameters</div>
            <div class="overflow-x-auto">
              <table class="table table-xs w-full">
                <thead>
                  <tr class="text-base-content/50">
                    <th>Name</th>
                    <th>Type</th>
                    <th>Default</th>
                    <th>Description</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="p in info.params" :key="p.name">
                    <td class="font-mono text-xs">{{ p.name }}</td>
                    <td class="text-xs opacity-60">{{ p.type }}</td>
                    <td class="font-mono text-xs">{{ p.default }}</td>
                    <td class="text-xs">
                      {{ p.description }}
                      <div v-if="p.values" class="mt-1 flex flex-wrap gap-1">
                        <span
                          v-for="v in p.values"
                          :key="v"
                          class="badge badge-xs badge-outline font-mono"
                        >{{ v }}</span>
                      </div>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>

        <div class="mt-4 flex justify-end">
          <button type="button" class="btn btn-sm" @click="open = false">Close</button>
        </div>
      </div>
    </div>
  </Teleport>
</template>
