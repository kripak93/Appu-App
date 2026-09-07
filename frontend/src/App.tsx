import { useState } from 'react'
import { runSimulation, SimulationRequest, SimulationResponse } from './api'
import ControlsPanel from './components/ControlsPanel'
import ChartsPanel from './components/ChartsPanel'
import EstimationPanel from './components/EstimationPanel'

const DEFAULT_PARAMS = {
  p: 0.03,
  q: 0.38,
  M: 1000000,
  beta1: -0.5,
  beta2: -0.3,
  beta3: 1.5,
  r: 0.05,
}

const DEFAULT_PERIOD = {
  price_level: 'parity' as string,
  restrictions: 0.1,
  push: 0.5,
}

function App() {
  const [activeTab, setActiveTab] = useState<'estimate' | 'forecast'>('estimate')
  const [params, setParams] = useState(DEFAULT_PARAMS)
  const [nPeriods, setNPeriods] = useState(20)
  const [periodInput, setPeriodInput] = useState(DEFAULT_PERIOD)
  const [results, setResults] = useState<SimulationResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleSimulate = async () => {
    setLoading(true)
    setError(null)
    try {
      const period_inputs = Array.from({ length: nPeriods }, () => ({
        price_level: periodInput.price_level,
        restrictions: periodInput.restrictions,
        push: periodInput.push,
      }))

      const request: SimulationRequest = {
        ...params,
        period_inputs,
      }

      const data = await runSimulation(request)
      setResults(data)
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Failed to run simulation'
      setError(message)
    } finally {
      setLoading(false)
    }
  }

  const handleUseEstimatedParams = (p: number, q: number, M: number) => {
    setParams((prev) => ({ ...prev, p, q, M }))
    setActiveTab('forecast')
  }

  return (
    <div className="app-container">
      <div className="header">
        <h1>Bass Diffusion Model</h1>
        <p>Generalized Bass Model with Decision Variables</p>
      </div>

      {/* Tab Navigation */}
      <div className="tab-nav">
        <button
          className={`tab-btn ${activeTab === 'estimate' ? 'active' : ''}`}
          onClick={() => setActiveTab('estimate')}
        >
          Phase 1: Estimate Parameters
        </button>
        <button
          className={`tab-btn ${activeTab === 'forecast' ? 'active' : ''}`}
          onClick={() => setActiveTab('forecast')}
        >
          Phase 2: Forecast
        </button>
      </div>

      {/* Phase 1: Estimation */}
      {activeTab === 'estimate' && (
        <EstimationPanel onUseParameters={handleUseEstimatedParams} />
      )}

      {/* Phase 2: Forecast */}
      {activeTab === 'forecast' && (
        <div className="panels">
          <ControlsPanel
            params={params}
            setParams={setParams}
            nPeriods={nPeriods}
            setNPeriods={setNPeriods}
            periodInput={periodInput}
            setPeriodInput={setPeriodInput}
            onSimulate={handleSimulate}
            loading={loading}
          />
          <ChartsPanel results={results} error={error} />
        </div>
      )}
    </div>
  )
}

export default App
