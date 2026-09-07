"""
Bass Diffusion Model - Streamlit App
Phase 1: Estimate p, q, M from historical data
Phase 2: Forecast with GBM decision variables
"""

import io
import csv
import numpy as np
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from backend.model import (
    estimate_parameters,
    run_simulation,
    ModelParameters,
    PeriodInputs,
    PRICE_MAP,
)

# ─────────────────────────────────────────────
# Page config
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="Bass Diffusion Model",
    page_icon="📈",
    layout="wide",
)

st.title("📈 Bass Diffusion Model")
st.caption("Generalized Bass Model with Decision Variables")

# ─────────────────────────────────────────────
# Tabs
# ─────────────────────────────────────────────
tab1, tab2 = st.tabs(["Phase 1 — Estimate Parameters", "Phase 2 — Forecast"])


# ═════════════════════════════════════════════
# PHASE 1: ESTIMATION
# ═════════════════════════════════════════════
with tab1:

    # Formula reference
    with st.expander("📐 Model Equations", expanded=True):
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown("**Cumulative Adoption**")
            st.latex(r"F(t) = \frac{1 - e^{-(p+q)t}}{1 + \frac{q}{p}e^{-(p+q)t}}")
        with col2:
            st.markdown("**Period Sales**")
            st.latex(r"S(t) = M \cdot [F(t) - F(t-1)]")
        with col3:
            st.markdown("**Estimation Objective**")
            st.latex(r"\min \; SSE = \sum [S_{obs}(t) - S_{pred}(t)]^2")

        st.markdown("""
        | Parameter | Description |
        |---|---|
        | **p** | Coefficient of innovation (external influence) |
        | **q** | Coefficient of imitation (word of mouth) |
        | **M** | Market potential (total eventual adopters) |
        """)

    st.divider()

    # Data input
    col_left, col_right = st.columns([1, 1])

    with col_left:
        st.subheader("Input Historical Sales Data")

        input_method = st.radio(
            "Input method", ["Paste data", "Upload CSV"], horizontal=True
        )

        sales_data = None

        if input_method == "Paste data":
            default_data = "20000\n50000\n120000\n250000\n600000\n1750000\n3000000\n3500000\n2750000"
            raw = st.text_area(
                "Sales per period (one value per line, or 'period, sales')",
                value=default_data,
                height=220,
            )
            if st.button("Estimate Parameters", type="primary", use_container_width=True):
                lines = [l.strip() for l in raw.strip().split("\n") if l.strip()]
                parsed = []
                for line in lines:
                    parts = line.split(",")
                    try:
                        parsed.append(float(parts[-1].strip()))
                    except ValueError:
                        pass
                if len(parsed) < 3:
                    st.error("Need at least 3 periods of data.")
                else:
                    sales_data = parsed

        else:
            uploaded = st.file_uploader("Upload CSV", type=["csv"])
            if uploaded:
                text = uploaded.read().decode("utf-8")
                reader = csv.reader(io.StringIO(text))
                parsed = []
                header_skipped = False
                for row in reader:
                    if not row:
                        continue
                    if not header_skipped:
                        try:
                            float(row[-1])
                            header_skipped = True
                        except ValueError:
                            header_skipped = True
                            continue
                    try:
                        parsed.append(float(row[-1].strip()))
                    except ValueError:
                        continue
                if len(parsed) < 3:
                    st.error("Need at least 3 periods of data in the CSV.")
                else:
                    sales_data = parsed

    # Run estimation
    if sales_data:
        with st.spinner("Estimating parameters... minimizing SSE via nonlinear least squares"):
            result = estimate_parameters(sales_data)

        # Store in session state so Phase 2 can use them
        st.session_state["est_p"] = result.p
        st.session_state["est_q"] = result.q
        st.session_state["est_M"] = result.M

        with col_right:
            st.subheader("Estimated Parameters")
            c1, c2, c3 = st.columns(3)
            c1.metric("p (innovation)", f"{result.p:.4f}")
            c2.metric("q (imitation)", f"{result.q:.4f}")
            c3.metric("M (market potential)", f"{result.M:,.0f}")

        st.divider()

        # Validation metrics
        st.subheader("Validation Metrics")
        m1, m2, m3, m4, m5, m6 = st.columns(6)
        m1.metric("R²", f"{result.r_squared:.4f}", help="Proportion of variance explained. Closer to 1 is better.")
        m2.metric("MAPE", f"{result.mape:.1f}%", help="Mean Absolute Percentage Error. Scale-independent.")
        m3.metric("RMSE", f"{result.rmse:,.0f}", help="Root Mean Squared Error. Same units as sales.")
        m4.metric("MAE", f"{result.mae:,.0f}", help="Mean Absolute Error. Average miss per period.")
        m5.metric("MSE", f"{result.mse:.2e}", help="Mean Squared Error.")
        m6.metric("SSE", f"{result.sse:.2e}", help="Sum of Squared Errors. Minimized during estimation.")

        st.divider()

        # Fit chart
        st.subheader("Model Fit: Observed vs Predicted")
        df_fit = pd.DataFrame({
            "Period": result.periods,
            "Observed": result.observed_sales,
            "Predicted": result.predicted_sales,
        })

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df_fit["Period"], y=df_fit["Observed"],
            mode="lines+markers", name="Observed",
            line=dict(color="#4a6cf7", width=2),
            marker=dict(size=7),
        ))
        fig.add_trace(go.Scatter(
            x=df_fit["Period"], y=df_fit["Predicted"],
            mode="lines", name="Predicted (Bass)",
            line=dict(color="#e74c3c", width=2, dash="dash"),
        ))
        fig.update_layout(
            xaxis_title="Period",
            yaxis_title="Sales",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            height=350,
            margin=dict(t=30),
        )
        st.plotly_chart(fig, use_container_width=True)

        if st.button("Use These Parameters in Phase 2 →", type="primary"):
            st.success(f"Parameters set: p={result.p:.4f}, q={result.q:.4f}, M={result.M:,.0f}. Switch to the Phase 2 tab.")


# ═════════════════════════════════════════════
# PHASE 2: FORECAST
# ═════════════════════════════════════════════
with tab2:

    st.subheader("GBM Forecast")

    # GBM formula reference
    with st.expander("📐 GBM Equations", expanded=False):
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Generalized Bass Model**")
            st.latex(r"F(t) = \frac{1 - e^{-(p+q) \cdot Z(t)}}{1 + \frac{q}{p} e^{-(p+q) \cdot Z(t)}}")
            st.latex(r"Z(t) = t + \beta_1 \ln\!\frac{Pr(t)}{Pr(0)} + \beta_2 \ln\!\frac{res(t)}{res(0)}")
        with col2:
            st.markdown("**Effective Innovation Rate**")
            st.latex(r"p_{eff} = p \cdot (1 + \beta_3 \cdot Push)")
            st.markdown("**Period Sales with Replacement**")
            st.latex(r"S(t) = [F(t) - F(t-1)] \cdot M + r \cdot F(t-1) \cdot M")
            st.markdown("""
            | | |
            |---|---|
            | β₁ < 0 | Price disadvantage slows adoption |
            | β₂ < 0 | Restrictions slow adoption |
            | β₃ > 0 | Marketing push accelerates adoption |
            """)

    st.divider()

    col_params, col_decision = st.columns([1, 1])

    # Pull estimated values from session state if available
    default_p = st.session_state.get("est_p", 0.03)
    default_q = st.session_state.get("est_q", 0.38)
    default_M = st.session_state.get("est_M", 1_000_000.0)

    with col_params:
        st.markdown("**Model Parameters**")
        p = st.number_input("p (innovation)", value=float(f"{default_p:.4f}"), min_value=0.0001, max_value=0.5, step=0.001, format="%.4f")
        q = st.number_input("q (imitation)", value=float(f"{default_q:.4f}"), min_value=0.0001, max_value=2.0, step=0.01, format="%.4f")
        M = st.number_input("M (market potential)", value=float(f"{default_M:.0f}"), min_value=1.0, step=10000.0, format="%.0f")
        st.divider()
        beta1 = st.number_input("β₁ (price sensitivity)", value=-0.5, step=0.1, format="%.2f", help="Should be < 0")
        beta2 = st.number_input("β₂ (restrictions sensitivity)", value=-0.3, step=0.1, format="%.2f", help="Should be < 0")
        beta3 = st.number_input("β₃ (marketing push sensitivity)", value=1.5, step=0.1, format="%.2f", help="Should be > 0")
        r = st.number_input("r (replacement rate)", value=0.05, min_value=0.0, max_value=1.0, step=0.01, format="%.2f")
        n_periods = st.slider("Number of periods", min_value=5, max_value=100, value=20)

    with col_decision:
        st.markdown("**Decision Variables**")
        st.caption("Applied uniformly across all periods")

        price_options = {
            "Very Advantageous": "very_adv",
            "Advantageous": "adv",
            "Parity": "parity",
            "Disadvantageous": "disadv",
            "Very Disadvantageous": "very_disadv",
        }
        price_label = st.selectbox("Price Position", list(price_options.keys()), index=2)
        price_level = price_options[price_label]

        restrictions = st.slider(
            "Restrictions (0 = none, 1 = full)",
            min_value=0.0, max_value=1.0, value=0.1, step=0.05
        )
        push = st.slider(
            "Launch Marketing Effort (0 = none, 1 = maximum)",
            min_value=0.0, max_value=1.0, value=0.5, step=0.05
        )

        st.divider()
        st.markdown("**Price Index Reference**")
        price_df = pd.DataFrame({
            "Level": list(price_options.keys()),
            "Price Index": [PRICE_MAP[v] for v in price_options.values()],
        })
        st.dataframe(price_df, hide_index=True, use_container_width=True)

    st.divider()

    if st.button("Run Simulation", type="primary", use_container_width=True):
        params = ModelParameters(
            p=p, q=q, M=M,
            beta1=beta1, beta2=beta2, beta3=beta3,
            r=r,
        )
        period_inputs = [
            PeriodInputs(price_level=price_level, restrictions=restrictions, push=push)
            for _ in range(n_periods)
        ]

        with st.spinner("Running simulation..."):
            sim = run_simulation(params, period_inputs)

        df = pd.DataFrame({
            "Period": [t + 1 for t in sim.periods],
            "Cumulative Adoption (%)": [round(f * 100, 2) for f in sim.F],
            "New Adopters": [round(x) for x in sim.new_adopters],
            "Replacement Sales": [round(x) for x in sim.replacement_sales],
            "Total Sales": [round(x) for x in sim.total_sales],
            "Cumulative Sales": [round(x) for x in sim.cumulative_sales],
        })

        # Summary metrics
        peak_period = int(df.loc[df["Total Sales"].idxmax(), "Period"])
        peak_sales = int(df["Total Sales"].max())
        final_adoption = df["Cumulative Adoption (%)"].iloc[-1]
        total_sales = int(df["Cumulative Sales"].iloc[-1])

        s1, s2, s3, s4 = st.columns(4)
        s1.metric("Peak Sales Period", peak_period)
        s2.metric("Peak Period Sales", f"{peak_sales:,}")
        s3.metric("Final Adoption", f"{final_adoption:.1f}%")
        s4.metric("Total Cumulative Sales", f"{total_sales:,}")

        st.divider()

        # Charts
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=(
                "Cumulative Adoption (S-Curve)",
                "Sales Per Period",
                "Cumulative Sales",
                "Adopters vs Replacement",
            ),
        )

        # S-curve
        fig.add_trace(go.Scatter(
            x=df["Period"], y=df["Cumulative Adoption (%)"],
            fill="tozeroy", fillcolor="rgba(74,108,247,0.1)",
            line=dict(color="#4a6cf7", width=2), name="Adoption %",
        ), row=1, col=1)

        # Total sales
        fig.add_trace(go.Scatter(
            x=df["Period"], y=df["Total Sales"],
            line=dict(color="#10b981", width=2), name="Total Sales",
        ), row=1, col=2)

        # Cumulative sales
        fig.add_trace(go.Scatter(
            x=df["Period"], y=df["Cumulative Sales"],
            fill="tozeroy", fillcolor="rgba(16,185,129,0.1)",
            line=dict(color="#10b981", width=2), name="Cumulative Sales",
        ), row=2, col=1)

        # Adopters vs Replacement stacked
        fig.add_trace(go.Bar(
            x=df["Period"], y=df["New Adopters"],
            name="New Adopters", marker_color="#4a6cf7",
        ), row=2, col=2)
        fig.add_trace(go.Bar(
            x=df["Period"], y=df["Replacement Sales"],
            name="Replacement", marker_color="#f59e0b",
        ), row=2, col=2)

        fig.update_layout(
            height=650,
            barmode="stack",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            margin=dict(t=50),
        )
        fig.update_xaxes(title_text="Period")

        st.plotly_chart(fig, use_container_width=True)

        # Raw data table
        with st.expander("View Raw Data"):
            st.dataframe(df, use_container_width=True, hide_index=True)
            csv_out = df.to_csv(index=False)
            st.download_button(
                "Download CSV",
                data=csv_out,
                file_name="bass_simulation_results.csv",
                mime="text/csv",
            )
