interface Params {
  p: number
  q: number
  M: number
  beta1: number
  beta2: number
  beta3: number
  r: number
}

interface PeriodInput {
  price_level: string
  restrictions: number
  push: number
}

interface Props {
  params: Params
  setParams: (p: Params) => void
  nPeriods: number
  setNPeriods: (n: number) => void
  periodInput: PeriodInput
  setPeriodInput: (p: PeriodInput) => void
  onSimulate: () => void
  loading: boolean
}

const PRICE_LEVELS = [
  { key: 'very_adv', label: 'Very Advantageous' },
  { key: 'adv', label: 'Advantageous' },
  { key: 'parity', label: 'Parity' },
  { key: 'disadv', label: 'Disadvantageous' },
  { key: 'very_disadv', label: 'Very Disadvantageous' },
]

function ControlsPanel({ params, setParams, nPeriods, setNPeriods, periodInput, setPeriodInput, onSimulate, loading }: Props) {
  return (
    <div className="controls-panel">
      {/* Model Parameters */}
      <div className="card">
        <h2>Model Parameters</h2>
        <div className="param-group">
          <div className="param-row">
            <label>p (innovation)</label>
            <input
              type="number"
              step="0.001"
              value={params.p}
              onChange={(e) => setParams({ ...params, p: parseFloat(e.target.value) || 0 })}
            />
          </div>
          <div className="param-row">
            <label>q (imitation)</label>
            <input
              type="number"
              step="0.01"
              value={params.q}
              onChange={(e) => setParams({ ...params, q: parseFloat(e.target.value) || 0 })}
            />
          </div>
          <div className="param-row">
            <label>M (market)</label>
            <input
              type="number"
              step="10000"
              value={params.M}
              onChange={(e) => setParams({ ...params, M: parseFloat(e.target.value) || 0 })}
            />
          </div>
          <div className="param-row">
            <label>β₁ (price)</label>
            <input
              type="number"
              step="0.1"
              value={params.beta1}
              onChange={(e) => setParams({ ...params, beta1: parseFloat(e.target.value) || 0 })}
            />
          </div>
          <div className="param-row">
            <label>β₂ (restrict.)</label>
            <input
              type="number"
              step="0.1"
              value={params.beta2}
              onChange={(e) => setParams({ ...params, beta2: parseFloat(e.target.value) || 0 })}
            />
          </div>
          <div className="param-row">
            <label>β₃ (push)</label>
            <input
              type="number"
              step="0.1"
              value={params.beta3}
              onChange={(e) => setParams({ ...params, beta3: parseFloat(e.target.value) || 0 })}
            />
          </div>
          <div className="param-row">
            <label>r (replacement)</label>
            <input
              type="number"
              step="0.01"
              value={params.r}
              onChange={(e) => setParams({ ...params, r: parseFloat(e.target.value) || 0 })}
            />
          </div>
          <hr className="divider" />
          <div className="param-row">
            <label>Periods</label>
            <input
              type="number"
              step="1"
              min="1"
              max="100"
              value={nPeriods}
              onChange={(e) => setNPeriods(parseInt(e.target.value) || 1)}
            />
          </div>
        </div>
      </div>

      {/* Decision Variables */}
      <div className="card">
        <h2>Decision Variables</h2>
        <p className="period-note">Applied uniformly across all periods</p>
        <div className="param-group" style={{ marginTop: '0.75rem' }}>
          {/* Price Level */}
          <div className="slider-row">
            <label>Price Position</label>
            <select
              value={periodInput.price_level}
              onChange={(e) => setPeriodInput({ ...periodInput, price_level: e.target.value })}
            >
              {PRICE_LEVELS.map((pl) => (
                <option key={pl.key} value={pl.key}>{pl.label}</option>
              ))}
            </select>
          </div>

          {/* Restrictions */}
          <div className="slider-row">
            <div className="slider-header">
              <label>Restrictions</label>
              <span className="slider-value">{periodInput.restrictions.toFixed(2)}</span>
            </div>
            <input
              type="range"
              min="0"
              max="1"
              step="0.05"
              value={periodInput.restrictions}
              onChange={(e) => setPeriodInput({ ...periodInput, restrictions: parseFloat(e.target.value) })}
            />
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.7rem', color: '#999' }}>
              <span>No restrictions</span>
              <span>Full restrictions</span>
            </div>
          </div>

          {/* Marketing Push */}
          <div className="slider-row">
            <div className="slider-header">
              <label>Launch Marketing Effort</label>
              <span className="slider-value">{periodInput.push.toFixed(2)}</span>
            </div>
            <input
              type="range"
              min="0"
              max="1"
              step="0.05"
              value={periodInput.push}
              onChange={(e) => setPeriodInput({ ...periodInput, push: parseFloat(e.target.value) })}
            />
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.7rem', color: '#999' }}>
              <span>No effort</span>
              <span>Maximum effort</span>
            </div>
          </div>
        </div>
      </div>

      {/* Run Button */}
      <button className="btn-simulate" onClick={onSimulate} disabled={loading}>
        {loading ? 'Running...' : 'Run Simulation'}
      </button>
    </div>
  )
}

export default ControlsPanel
