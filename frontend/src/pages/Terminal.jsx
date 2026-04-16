import { useState, useRef, useEffect } from 'react'
import { agentApi } from '../services/api'
import styles from './Terminal.module.css'

const TOOL_COLORS = {
  calculator: 'amber',
  weather: 'blue',
  web_search: 'teal',
  summarizer: 'purple',
}

const TOOL_ICONS = {
  calculator: '∑',
  weather: '◎',
  web_search: '⊕',
  summarizer: '≋',
}

function ToolBadge({ name }) {
  const color = TOOL_COLORS[name] || 'gray'
  const icon = TOOL_ICONS[name] || '▸'
  return (
    <span className={`${styles.badge} ${styles[`badge_${color}`]}`}>
      {icon} {name}
    </span>
  )
}

function Step({ step, index }) {
  const [open, setOpen] = useState(true)
  return (
    <div className={styles.step} style={{ animationDelay: `${index * 60}ms` }}>
      <div className={styles.stepHeader} onClick={() => setOpen(o => !o)}>
        <span className={styles.stepNum}>step_{String(index + 1).padStart(2, '0')}</span>
        {step.action && <ToolBadge name={step.action} />}
        <span className={styles.stepToggle}>{open ? '▾' : '▸'}</span>
      </div>
      {open && (
        <div className={styles.stepBody}>
          {step.thought && (
            <div className={styles.stepSection}>
              <span className={styles.sectionLabel}>thought</span>
              <p className={styles.sectionText}>{step.thought}</p>
            </div>
          )}
          {step.action && (
            <div className={styles.stepSection}>
              <span className={styles.sectionLabel}>action_input</span>
              <code className={styles.sectionCode}>{step.action_input}</code>
            </div>
          )}
          {step.observation && (
            <div className={styles.stepSection}>
              <span className={styles.sectionLabel}>observation</span>
              <p className={styles.sectionText}>{step.observation}</p>
            </div>
          )}
          {step.final_answer && (
            <div className={styles.stepSection}>
              <span className={`${styles.sectionLabel} ${styles.labelFinal}`}>final_answer</span>
              <p className={`${styles.sectionText} ${styles.finalText}`}>{step.final_answer}</p>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

function SessionResult({ result }) {
  return (
    <div className={styles.result}>
      <div className={styles.resultHeader}>
        <span className={styles.resultId}>session #{result.session_id}</span>
        <span className={`${styles.statusBadge} ${result.status === 'completed' ? styles.statusOk : styles.statusFail}`}>
          {result.status === 'completed' ? '✓' : '✗'} {result.status}
        </span>
        {result.tools_used?.length > 0 && (
          <div className={styles.toolsUsed}>
            {result.tools_used.map(t => <ToolBadge key={t} name={t} />)}
          </div>
        )}
      </div>
{/*
      <div className={styles.steps}>
        {result.steps?.map((step, i) => (
          <Step key={i} step={step} index={i} />
        ))}
      </div>*/}

      {result.final_answer && (
        <div className={styles.finalAnswer}>
          <span className={styles.finalLabel}>▸ final answer</span>
          <p>{result.final_answer}</p>
        </div>
      )}
    </div>
  )
}

export default function Terminal() {
  const [task, setTask] = useState('')
  const [maxSteps, setMaxSteps] = useState(8)
  const [loading, setLoading] = useState(false)
  const [results, setResults] = useState([])
  const [error, setError] = useState('')
  const textareaRef = useRef(null)
  const bottomRef = useRef(null)

  useEffect(() => {
    if (results.length > 0) {
      bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
    }
  }, [results])

  const run = async (e) => {
    e.preventDefault()
    if (!task.trim()) return
    setError('')
    setLoading(true)
    try {
      const { data } = await agentApi.run({ task: task.trim(), max_steps: maxSteps })
      setResults(prev => [data, ...prev])
      setTask('')
    } catch (err) {
      setError(err.response?.data?.detail || 'Agent run failed')
    } finally {
      setLoading(false)
    }
  }

  const handleKey = (e) => {
    if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) run(e)
  }

  return (
    <div className={styles.page}>
      <div className={styles.header}>
        <div className={styles.headerLeft}>
          <span className={styles.dot} />
          <span className={styles.title}>agent_terminal</span>
        </div>
        <div className={styles.headerRight}>
          <span className={styles.hint}>ctrl+enter to run</span>
        </div>
      </div>

      <div className={styles.inputSection}>
        <div className={styles.prompt}>
          <span className={styles.promptSymbol}>$</span>
          <textarea
            ref={textareaRef}
            className={styles.textarea}
            value={task}
            onChange={e => setTask(e.target.value)}
            onKeyDown={handleKey}
            placeholder="Describe the task for the agent... e.g. 'What's the weather in Paris and calculate 12 * 7 + 15?'"
            rows={3}
            disabled={loading}
          />
        </div>
        <div className={styles.controls}>
          <label className={styles.stepsLabel}>
            max_steps:
            <select
              className={styles.stepsSelect}
              value={maxSteps}
              onChange={e => setMaxSteps(Number(e.target.value))}
              disabled={loading}
            >
              {[3,5,8,10,15].map(n => (
                <option key={n} value={n}>{n}</option>
              ))}
            </select>
          </label>
          <button
            className={styles.runBtn}
            onClick={run}
            disabled={loading || !task.trim()}
          >
            {loading ? (
              <>
                <span className={styles.spinner} />
                running...
              </>
            ) : '▸ run agent'}
          </button>
        </div>
        {error && <div className={styles.error}>✗ {error}</div>}
      </div>

      {loading && (
        <div className={styles.runningBar}>
          <span className={styles.runningDot} />
          agent is reasoning...
        </div>
      )}

      <div className={styles.feed}>
        {results.length === 0 && !loading && (
          <div className={styles.empty}>
            <span className={styles.emptyCursor}>_</span>
            <p>No runs yet. Type a task and press run.</p>
            <div className={styles.examples}>
              {[
                "What's the weather in Paris?",
                "Calculate (144 / 12) * 7 + 100",
                "Search for latest news about AI agents",
                "Summarize: Machine learning is a branch of AI...",
              ].map(ex => (
                <button
                  key={ex}
                  className={styles.exampleBtn}
                  onClick={() => setTask(ex)}
                >
                  {ex}
                </button>
              ))}
            </div>
          </div>
        )}
        {results.map((r, i) => (
          <SessionResult key={r.session_id || i} result={r} />
        ))}
        <div ref={bottomRef} />
      </div>
    </div>
  )
}
