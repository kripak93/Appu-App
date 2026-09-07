"""
FastAPI backend for the Bass Diffusion Model application.
"""

import csv
import io
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional

from model import (
    ModelParameters,
    PeriodInputs,
    run_simulation,
    estimate_parameters,
    PRICE_MAP,
)

app = FastAPI(title="Bass Diffusion Model API", version="1.0.0")

# Allow frontend to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Request/Response schemas ---

class PeriodInput(BaseModel):
    price_level: str = Field(
        description="One of: very_adv, adv, parity, disadv, very_disadv"
    )
    restrictions: float = Field(ge=0, le=1, description="0 = no restrictions, 1 = full restrictions")
    push: float = Field(ge=0, le=1, description="0 = no marketing, 1 = maximum effort")


class SimulationRequest(BaseModel):
    # Model parameters
    p: float = Field(default=0.03, description="Coefficient of innovation")
    q: float = Field(default=0.38, description="Coefficient of imitation")
    M: float = Field(default=1000000, description="Market potential")
    beta1: float = Field(default=-0.5, description="Price sensitivity (should be < 0)")
    beta2: float = Field(default=-0.3, description="Restrictions sensitivity (should be < 0)")
    beta3: float = Field(default=1.5, description="Marketing push sensitivity (> 0)")
    r: float = Field(default=0.05, description="Replacement rate")

    # Decision variables per period
    period_inputs: List[PeriodInput]


class SimulationResponse(BaseModel):
    periods: List[int]
    cumulative_adoption: List[float]
    new_adopters: List[float]
    replacement_sales: List[float]
    total_sales: List[float]
    cumulative_sales: List[float]


# --- Endpoints ---

@app.get("/")
def root():
    return {"message": "Bass Diffusion Model API", "version": "1.0.0"}


@app.get("/price-levels")
def get_price_levels():
    """Return available price levels and their numeric mappings."""
    return {
        "levels": [
            {"key": "very_adv", "label": "Very Advantageous", "value": 0.6},
            {"key": "adv", "label": "Advantageous", "value": 0.8},
            {"key": "parity", "label": "Parity", "value": 1.0},
            {"key": "disadv", "label": "Disadvantageous", "value": 1.2},
            {"key": "very_disadv", "label": "Very Disadvantageous", "value": 1.4},
        ]
    }


@app.get("/defaults")
def get_defaults():
    """Return default parameter values for the UI."""
    return {
        "p": 0.03,
        "q": 0.38,
        "M": 1000000,
        "beta1": -0.5,
        "beta2": -0.3,
        "beta3": 1.5,
        "r": 0.05,
        "n_periods": 20,
        "default_period": {
            "price_level": "parity",
            "restrictions": 0.1,
            "push": 0.5,
        },
    }


@app.post("/simulate", response_model=SimulationResponse)
def simulate(request: SimulationRequest):
    """Run the Bass diffusion simulation."""
    params = ModelParameters(
        p=request.p,
        q=request.q,
        M=request.M,
        beta1=request.beta1,
        beta2=request.beta2,
        beta3=request.beta3,
        r=request.r,
    )

    period_inputs = [
        PeriodInputs(
            price_level=pi.price_level,
            restrictions=pi.restrictions,
            push=pi.push,
        )
        for pi in request.period_inputs
    ]

    result = run_simulation(params, period_inputs)

    return SimulationResponse(
        periods=result.periods,
        cumulative_adoption=result.F,
        new_adopters=result.new_adopters,
        replacement_sales=result.replacement_sales,
        total_sales=result.total_sales,
        cumulative_sales=result.cumulative_sales,
    )


# --- Parameter Estimation ---

class EstimationRequest(BaseModel):
    sales_data: List[float] = Field(description="List of sales per period (period 1, 2, 3, ...)")


class EstimationResponse(BaseModel):
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


@app.post("/estimate", response_model=EstimationResponse)
def estimate_from_json(request: EstimationRequest):
    """Estimate p, q, M from historical sales data (JSON input)."""
    result = estimate_parameters(request.sales_data)
    return EstimationResponse(
        p=result.p,
        q=result.q,
        M=result.M,
        sse=result.sse,
        mse=result.mse,
        rmse=result.rmse,
        mae=result.mae,
        mape=result.mape,
        r_squared=result.r_squared,
        predicted_sales=result.predicted_sales,
        observed_sales=result.observed_sales,
        periods=result.periods,
    )


@app.post("/estimate/csv", response_model=EstimationResponse)
async def estimate_from_csv(file: UploadFile = File(...)):
    """
    Estimate p, q, M from a CSV file.
    CSV should have a 'sales' column, or be a single column of sales values.
    """
    content = await file.read()
    text = content.decode("utf-8")
    reader = csv.reader(io.StringIO(text))

    sales_data: List[float] = []
    header_row = True

    for row in reader:
        if not row:
            continue
        # Try to detect header
        if header_row:
            try:
                float(row[-1])
                header_row = False
            except ValueError:
                # This is a header row, skip it
                header_row = False
                continue

        # Take the last column as sales (handles "period, sales" format)
        try:
            sales_data.append(float(row[-1].strip()))
        except ValueError:
            continue

    if len(sales_data) < 3:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="Need at least 3 periods of sales data")

    result = estimate_parameters(sales_data)
    return EstimationResponse(
        p=result.p,
        q=result.q,
        M=result.M,
        sse=result.sse,
        mse=result.mse,
        rmse=result.rmse,
        mae=result.mae,
        mape=result.mape,
        r_squared=result.r_squared,
        predicted_sales=result.predicted_sales,
        observed_sales=result.observed_sales,
        periods=result.periods,
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
