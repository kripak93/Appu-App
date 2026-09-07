import { useState, useRef } from 'react'
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts'
import { estimateFromData, estimateFromCSV, EstimationResponse } from '../api'

interface Props {
  onUseParameters: (p: number, q: number, M: number) => void
}

function EstimationPanel({ onUseParameters }: Props) {
  const [textInput, setTextInput] = useState(
    '20000\n50000\n120000\n250000\n600000\n1750000\n3000000\n3500000\n2750000'
  )
  const [result, setResult] = useState<EstimationResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const handleEstimateFromText = async () => {
    setLoading(true)
    setError(null)
    try {
      const lines = textInput.trim().split('\n')
      const salesData = lines
        .map((line) => {
          // Handle "period, sales" or just "sales" format
          const parts = line.split(',')
          const val = parts[parts.length - 1].trim()
          return parseFloat(val)
        })
        .filter((n) => !isNaN(n))

      if (salesData.length < 3) {
        setError('Need at least 3 periods of sales data')
        return
      }

      const data = await estimateFromData(salesData)
      setResult(data)
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Estimation failed'
      setError(message)
    } finally {
      setLoading(false)
    }
  }

  const handleCSVUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return

    setLoading(true)
    setError(null)
    try {
      const data = await estimateFromCSV(file)
      setResult(data)
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'CSV upload failed'
      setError(message)
    } finally {
      setLoading(false)
    }
  }

  const chartData = result
    ? result.periods.map((period, i) => ({
        period,
        observed: Math.round(result.observed_sales[i]),
        predicted: Math.round(result.predicted_sales[i]),
      }))
    : []

  return (
    <div className="estimation-panel">
      {/* Formula Reference */}
      <div className="card" style={{ marginBottom: '1rem' }}>
        <h2>Bass Diffusion Model</h2>
        <div className="formula-section">
          <div className="formula-block">
            <div className="formula-label">Cumulative Adoption Fraction</div>
            <div className="formula">
              F(t) = [1 − e<sup>−(p+q)·t</sup>] / [1 + (q/p)·e<sup>−(p+q)·t</sup>]
            </div>
          </div>
          <div className="formula-block">
            <div className="formula-label">Period Sales</div>
            <div className="formula">
              S(t) = M · [F(t) − F(t−1)]
            </div>
          </div>
          <div className="formula-block">
            <div className="formula-label">Estimation Objective</div>
            <div className="formula">
              min SSE = Σ [S<sub>observed</sub>(t) − S<sub>predicted</sub>(t)]²
            </div>
          </div>
          <div className="formula-params">
            <div><strong>p</strong> = coefficient of innovation (external influence)</div>
            <div><strong>q</strong> = coefficient of imitation (word of mouth)</div>
            <div><strong>M</strong> = market potential (total eventual adopters)</div>
          </div>
        </div>
      </div>

      <div className="card">
        <h2>Estimate Parameters</h2>
        <p style={{ fontSize: '0.85rem', color: '#666', marginBottom: '1rem' }}>
          Upload or paste historical sales data to estimate p, q, and M.
        </p>

        {/* Text input */}
        <div className="param-group">
          <label style={{ fontSize: '0.85rem', fontWeight: 500, color: '#555' }}>
            Sales per period (one value per line, or "period, sales")
          </label>
          <textarea
            value={textInput}
            onChange={(e) => setTextInput(e.target.value)}
            rows={8}
            style={{
              width: '100%',
              padding: '0.5rem',
              border: '1px solid #ddd',
              borderRadius: '6px',
              fontFamily: 'monospace',
              fontSize: '0.85rem',
              resize: 'vertical',
            }}
          />
        </div>

        <div style={{ display: 'flex', gap: '0.5rem', marginTop: '0.75rem' }}>
          <button
            className="btn-simulate"
            onClick={handleEstimateFromText}
            disabled={loading}
            style={{ flex: 1 }}
          >
            {loading ? 'Estimating...' : 'Estimate from Text'}
          </button>
          <button
            className="btn-simulate"
            onClick={() => fileInputRef.current?.click()}
            disabled={loading}
            style={{ flex: 1, background: '#6b7280' }}
          >
            Upload CSV
          </button>
          <input
            ref={fileInputRef}
            type="file"
            accept=".csv"
            style={{ display: 'none' }}
            onChange={handleCSVUpload}
          />
        </div>

        {error && (
          <p style={{ color: '#e74c3c', marginTop: '0.75rem', fontSize: '0.85rem' }}>
            {error}
          </p>
        )}
      </div>

      {/* Loading indicator */}
      {loading && (
        <div className="card loading-card" style={{ marginTop: '1rem' }}>
          <div className="loading-spinner" />
          <div>
            <div style={{ fontWeight: 600, color: '#4a6cf7' }}>Estimating parameters...</div>
            <div style={{ fontSize: '0.8rem', color: '#888', marginTop: '0.25rem' }}>
              Minimizing SSE using nonlinear least squares to find optimal p, q, M
            </div>
          </div>
        </div>
      )}

      {/* Results */}
      {result && (
        <>
          <div className="card" style={{ marginTop: '1rem' }}>
            <h2>Estimated Parameters</h2>
            <div
              style={{
                display: 'grid',
                gridTemplateColumns: '1fr 1fr 1fr',
                gap: '1rem',
                marginTop: '0.75rem',
              }}
            >
              <div style={{ textAlign: 'center' }}>
                <div style={{ fontSize: '1.5rem', fontWeight: 700, color: '#4a6cf7' }}>
                  {result.p.toFixed(4)}
                </div>
                <div style={{ fontSize: '0.8rem', color: '#666' }}>p (innovation)</div>
              </div>
              <div style={{ textAlign: 'center' }}>
                <div style={{ fontSize: '1.5rem', fontWeight: 700, color: '#10b981' }}>
                  {result.q.toFixed(4)}
                </div>
                <div style={{ fontSize: '0.8rem', color: '#666' }}>q (imitation)</div>
              </div>
              <div style={{ textAlign: 'center' }}>
                <div style={{ fontSize: '1.5rem', fontWeight: 700, color: '#f59e0b' }}>
                  {(result.M / 1e6).toFixed(2)}M
                </div>
                <div style={{ fontSize: '0.8rem', color: '#666' }}>M (market potential)</div>
              </div>
            </div>

            <div className="metrics-grid" style={{ marginTop: '1rem' }}>
            <div className="metric-card metric-good">
              <div className="metric-value">{result.r_squared.toFixed(4)}</div>
              <div className="metric-label">R²</div>
              <div className="metric-desc">Variance explained</div>
            </div>
            <div className="metric-card">
              <div className="metric-value">{result.mape.toFixed(1)}%</div>
              <div className="metric-label">MAPE</div>
              <div className="metric-desc">Mean abs % error</div>
            </div>
            <div className="metric-card">
              <div className="metric-value">{result.rmse.toLocaleString(undefined, { maximumFractionDigits: 0 })}</div>
              <div className="metric-label">RMSE</div>
              <div className="metric-desc">Root mean sq. error</div>
            </div>
            <div className="metric-card">
              <div className="metric-value">{result.mae.toLocaleString(undefined, { maximumFractionDigits: 0 })}</div>
              <div className="metric-label">MAE</div>
              <div className="metric-desc">Mean abs error</div>
            </div>
            <div className="metric-card">
              <div className="metric-value">{result.mse.toExponential(2)}</div>
              <div className="metric-label">MSE</div>
              <div className="metric-desc">Mean sq. error</div>
            </div>
            <div className="metric-card">
              <div className="metric-value">{result.sse.toExponential(2)}</div>
              <div className="metric-label">SSE</div>
              <div className="metric-desc">Sum sq. errors</div>
            </div>
          </div>

            <button
              className="btn-simulate"
              style={{ marginTop: '1rem', background: '#10b981' }}
              onClick={() => onUseParameters(result.p, result.q, result.M)}
            >
              Use These Parameters in Forecast →
            </button>
          </div>

          {/* Fit Chart */}
          <div className="chart-card" style={{ marginTop: '1rem' }}>
            <h3>Model Fit: Observed vs Predicted</h3>
            <ResponsiveContainer width="100%" height={280}>
              <LineChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#eee" />
                <XAxis
                  dataKey="period"
                  label={{ value: 'Period', position: 'bottom', offset: -5 }}
                />
                <YAxis />
                <Tooltip formatter={(value: number) => value.toLocaleString()} />
                <Legend />
                <Line
                  type="monotone"
                  dataKey="observed"
                  stroke="#4a6cf7"
                  strokeWidth={2}
                  dot={{ r: 4 }}
                  name="Observed Sales"
                />
                <Line
                  type="monotone"
                  dataKey="predicted"
                  stroke="#e74c3c"
                  strokeWidth={2}
                  strokeDasharray="5 5"
                  dot={false}
                  name="Predicted (Bass)"
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </>
      )}
    </div>
  )
}

export default EstimationPanel
