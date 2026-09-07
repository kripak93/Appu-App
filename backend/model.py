"""
Generalized Bass Diffusion Model (GBM)

F(t) = [1 - e^(-(p+q)*Z(t))] / [1 + (q/p) * e^(-(p+q)*Z(t))]

Where:
    Z(t) = t + beta1 * ln(Pr(t)/Pr(0)) + beta2 * ln(res(t)/res(0))

    p_eff = p * (1 + beta3 * Push)

Sales:
    S(t) = [F(t) - F(t-1)] * M + replacement
    replacement = r * F(t-1) * M

Estimation:
    Given historical sales data, estimate p, q, M by minimizing SSE
    using the standard Bass model (no decision variables).
"""

import numpy as np
from scipy.optimize import least_squares
from dataclasses import dataclass
from typing import List, Tuple


# Price categorical mapping (relative price index)
# Lower value = cheaper relative to competition = faster adoption
PRICE_MAP = {
    "very_adv": 0.6,
    "adv": 0.8,
    "parity": 1.0,
    "disadv": 1.2,
    "very_disadv": 1.4,
}


@dataclass
class ModelParameters:
    p: float  # coefficient of innovation
    q: float  # coefficient of imitation (word of mouth)
    M: float  # market potential
    beta1: float  # price sensitivity (< 0)
    beta2: float  # restrictions sensitivity (< 0)
    beta3: float  # marketing push sensitivity (> 0)
    r: float  # replacement rate (fraction of installed base per period)


@dataclass
class PeriodInputs:
    """Decision variables for a single period."""
    price_level: str  # one of PRICE_MAP keys
    restrictions: float  # 0 to 1
    push: float  # 0 to 1 (launch marketing effort)


@dataclass
class SimulationResult:
    periods: List[int]
    F: List[float]  # cumulative adoption fraction
    new_adopters: List[float]  # new adopters per period
    replacement_sales: List[float]  # replacement purchases per period
    total_sales: List[float]  # total sales per period
    cumulative_sales: List[float]  # running total of all sales


def compute_Z(t: int, price_ratio: float, restrictions_ratio: float,
              beta1: float, beta2: float) -> float:
    """
    Compute effective time Z(t).
    Z(t) = t + beta1 * ln(Pr(t)/Pr(0)) + beta2 * ln(res(t)/res(0))
    """
    ln_price = np.log(price_ratio) if price_ratio > 0 else 0.0
    ln_res = np.log(restrictions_ratio) if restrictions_ratio > 0 else 0.0
    return t + beta1 * ln_price + beta2 * ln_res


def compute_F(p_eff: float, q: float, Z: float) -> float:
    """
    Compute cumulative adoption fraction F(t).
    F(t) = [1 - e^(-(p_eff+q)*Z)] / [1 + (q/p_eff) * e^(-(p_eff+q)*Z)]
    """
    if Z <= 0:
        return 0.0
    exponent = -(p_eff + q) * Z
    exp_val = np.exp(exponent)
    numerator = 1 - exp_val
    denominator = 1 + (q / p_eff) * exp_val
    return float(np.clip(numerator / denominator, 0.0, 1.0))


def run_simulation(params: ModelParameters,
                   period_inputs: List[PeriodInputs]) -> SimulationResult:
    """
    Run the GBM simulation over all periods.
    """
    n_periods = len(period_inputs)

    # Reference values (period 0 / launch conditions)
    price_0 = PRICE_MAP[period_inputs[0].price_level]
    # Use small baseline if restrictions at launch is 0
    res_0 = max(period_inputs[0].restrictions, 0.01)

    # Effective p with marketing push (use first period push for p_eff)
    push_0 = period_inputs[0].push
    p_eff = params.p * (1 + params.beta3 * push_0)

    periods = list(range(n_periods))
    F_values = [0.0] * n_periods
    new_adopters = [0.0] * n_periods
    replacement_sales = [0.0] * n_periods
    total_sales = [0.0] * n_periods
    cumulative_sales = [0.0] * n_periods

    for t in range(n_periods):
        inputs = period_inputs[t]
        price_t = PRICE_MAP[inputs.price_level]
        res_t = max(inputs.restrictions, 0.01)

        # Compute ratios
        price_ratio = price_t / price_0
        restrictions_ratio = res_t / res_0

        # Compute effective time
        Z = compute_Z(t, price_ratio, restrictions_ratio,
                      params.beta1, params.beta2)

        # Compute cumulative adoption
        F_values[t] = compute_F(p_eff, params.q, Z)

        # Compute period sales
        F_prev = F_values[t - 1] if t > 0 else 0.0
        new_adopters[t] = max(0, (F_values[t] - F_prev) * params.M)

        # Replacement: fraction of installed base
        replacement_sales[t] = params.r * F_prev * params.M

        # Total sales
        total_sales[t] = new_adopters[t] + replacement_sales[t]

        # Cumulative
        cumulative_sales[t] = (
            (cumulative_sales[t - 1] if t > 0 else 0.0) + total_sales[t]
        )

    return SimulationResult(
        periods=periods,
        F=F_values,
        new_adopters=new_adopters,
        replacement_sales=replacement_sales,
        total_sales=total_sales,
        cumulative_sales=cumulative_sales,
    )


# --- Parameter Estimation ---

@dataclass
class EstimationResult:
    p: float
    q: float
    M: float
    sse: float
    mse: float
    rmse: float
    mae: float
    mape: float
    r_squared: float
    predicted_sales: List[float]
    observed_sales: List[float]
    periods: List[int]


def bass_F(t: float, p: float, q: float) -> float:
    """Standard Bass cumulative adoption fraction at time t."""
    if t <= 0:
        return 0.0
    exponent = -(p + q) * t
    exp_val = np.exp(exponent)
    numerator = 1 - exp_val
    denominator = 1 + (q / p) * exp_val
    return float(np.clip(numerator / denominator, 0.0, 1.0))


def bass_sales_predicted(params: Tuple[float, float, float],
                         periods: List[int]) -> np.ndarray:
    """
    Predict sales for each period using standard Bass model.
    S(t) = M * [F(t) - F(t-1)]
    At t=1, F(t-1) = F(0) = 0
    """
    p, q, M = params
    predicted = []
    for t in periods:
        F_t = bass_F(t, p, q)
        F_t_minus_1 = bass_F(t - 1, p, q)
        s_t = M * (F_t - F_t_minus_1)
        predicted.append(s_t)
    return np.array(predicted)


def estimate_parameters(observed_sales: List[float]) -> EstimationResult:
    """
    Estimate p, q, M from historical period sales data by minimizing SSE.
    Uses scipy least_squares with bounds.
    """
    n = len(observed_sales)
    periods = list(range(1, n + 1))
    observed = np.array(observed_sales, dtype=float)

    # Initial guess: p=0.03, q=0.38, M = sum of sales * 1.5
    M_init = float(np.sum(observed)) * 1.5
    x0 = [0.03, 0.38, M_init]

    # Bounds: p in (0.0001, 0.5), q in (0.0001, 2.0), M in (max(observed), M_init * 10)
    lower = [0.0001, 0.0001, max(observed)]
    upper = [0.5, 2.0, M_init * 10]

    def residuals(params):
        predicted = bass_sales_predicted(params, periods)
        return predicted - observed

    result = least_squares(residuals, x0, bounds=(lower, upper), method='trf')

    p_est, q_est, M_est = result.x
    predicted = bass_sales_predicted(result.x, periods)

    # Compute metrics
    sse = float(np.sum((predicted - observed) ** 2))
    mse = sse / n
    rmse = float(np.sqrt(mse))
    mae = float(np.mean(np.abs(predicted - observed)))
    mape = float(np.mean(np.abs((observed - predicted) / np.where(observed != 0, observed, 1))) * 100)
    ss_total = float(np.sum((observed - np.mean(observed)) ** 2))
    r_squared = 1.0 - (sse / ss_total) if ss_total > 0 else 0.0

    return EstimationResult(
        p=float(p_est),
        q=float(q_est),
        M=float(M_est),
        sse=sse,
        mse=mse,
        rmse=rmse,
        mae=mae,
        mape=mape,
        r_squared=r_squared,
        predicted_sales=[float(x) for x in predicted],
        observed_sales=observed_sales,
        periods=periods,
    )
