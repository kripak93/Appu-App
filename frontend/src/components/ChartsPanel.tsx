import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  AreaChart,
  Area,
} from 'recharts'
import { SimulationResponse } from '../api'

interface Props {
  results: SimulationResponse | null
  error: string | null
}

function ChartsPanel({ results, error }: Props) {
  if (error) {
    return (
      <div className="charts-panel">
        <div className="chart-card" style={{ color: '#e74c3c' }}>
          <h3>Error</h3>
          <p>{error}</p>
          <p style={{ marginTop: '0.5rem', fontSize: '0.85rem', color: '#888' }}>
            Make sure the backend is running at http://localhost:8000
          </p>
        </div>
      </div>
    )
  }

  if (!results) {
    return (
      <div className="charts-panel">
        <div className="chart-card" style={{ textAlign: 'center', padding: '4rem 2rem', color: '#888' }}>
          <h3 style={{ color: '#aaa' }}>No Results Yet</h3>
          <p>Configure the parameters and click "Run Simulation" to see the diffusion curves.</p>
        </div>
      </div>
    )
  }

  // Transform data for charts
  const chartData = results.periods.map((period, i) => ({
    period: period + 1,
    cumulative_adoption: parseFloat((results.cumulative_adoption[i] * 100).toFixed(2)),
    new_adopters: Math.round(results.new_adopters[i]),
    replacement_sales: Math.round(results.replacement_sales[i]),
    total_sales: Math.round(results.total_sales[i]),
    cumulative_sales: Math.round(results.cumulative_sales[i]),
  }))

  return (
    <div className="charts-panel">
      {/* Cumulative Adoption (S-curve) */}
      <div className="chart-card">
        <h3>Cumulative Adoption (% of Market)</h3>
        <ResponsiveContainer width="100%" height={250}>
          <AreaChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#eee" />
            <XAxis dataKey="period" label={{ value: 'Period', position: 'bottom', offset: -5 }} />
            <YAxis unit="%" />
            <Tooltip formatter={(value: number) => [`${value}%`, 'Adoption']} />
            <Area
              type="monotone"
              dataKey="cumulative_adoption"
              stroke="#4a6cf7"
              fill="#4a6cf7"
              fillOpacity={0.15}
              strokeWidth={2}
              name="Cumulative Adoption"
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>

      {/* Sales Breakdown */}
      <div className="chart-card">
        <h3>Sales Per Period</h3>
        <ResponsiveContainer width="100%" height={250}>
          <LineChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#eee" />
            <XAxis dataKey="period" label={{ value: 'Period', position: 'bottom', offset: -5 }} />
            <YAxis />
            <Tooltip />
            <Legend />
            <Line
              type="monotone"
              dataKey="new_adopters"
              stroke="#4a6cf7"
              strokeWidth={2}
              dot={false}
              name="New Adopters"
            />
            <Line
              type="monotone"
              dataKey="replacement_sales"
              stroke="#f59e0b"
              strokeWidth={2}
              dot={false}
              name="Replacement"
            />
            <Line
              type="monotone"
              dataKey="total_sales"
              stroke="#10b981"
              strokeWidth={2}
              dot={false}
              name="Total Sales"
            />
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* Cumulative Sales */}
      <div className="chart-card">
        <h3>Cumulative Sales</h3>
        <ResponsiveContainer width="100%" height={250}>
          <AreaChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#eee" />
            <XAxis dataKey="period" label={{ value: 'Period', position: 'bottom', offset: -5 }} />
            <YAxis />
            <Tooltip />
            <Area
              type="monotone"
              dataKey="cumulative_sales"
              stroke="#10b981"
              fill="#10b981"
              fillOpacity={0.15}
              strokeWidth={2}
              name="Cumulative Sales"
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}

export default ChartsPanel
