import { useState, useCallback } from 'react'
import { analyze } from '../services/api'

export const STEP = {
  IDLE:      'idle',
  FETCHING:  'fetching',   // OANDA + news running on backend
  ANALYZING: 'analyzing',  // Claude AI running on backend
  DONE:      'done',
  ERROR:     'error',
}

export function useAnalysis() {
  const [step,    setStep]    = useState(STEP.IDLE)
  const [data,    setData]    = useState(null)   // full AnalyzeResponse
  const [error,   setError]   = useState(null)
  const [lastRun, setLastRun] = useState(null)

  const run = useCallback(async (balance) => {
    setStep(STEP.FETCHING)
    setError(null)
    setData(null)

    try {
      // Backend runs market + news concurrently, then calls Claude
      // Frontend just shows a loading state during all of this
      setStep(STEP.ANALYZING)
      const result = await analyze(balance)
      setData(result)
      setLastRun(new Date())
      setStep(STEP.DONE)
      return result
    } catch (e) {
      setError(e.message)
      setStep(STEP.ERROR)
      return null
    }
  }, [])

  const reset = useCallback(() => {
    setStep(STEP.IDLE)
    setData(null)
    setError(null)
  }, [])

  return {
    run, reset, step, data, error, lastRun,
    isLoading: step === STEP.FETCHING || step === STEP.ANALYZING,
    market: data?.market   || null,
    news:   data?.news     || null,
    signal: data?.signal   || null,
  }
}
