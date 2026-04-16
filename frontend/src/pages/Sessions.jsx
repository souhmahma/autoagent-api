import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { agentApi } from '../services/api'
import styles from './Sessions.module.css'

const TOOL_COLORS = {
  calculator: 'amber', weather: 'blue', web_search: 'teal', summarizer: 'purple',
}
const TOOL_ICONS = {
  calculator: '∑', weather: '◎', web_search: '⊕', summarizer: '≋',
}

function ToolBadge({ name }) {
  const color = TOOL_COLORS[name] || 'gray'
  const icon = TOOL_ICONS[name] || '▸'
  return <span className={`${styles.badge} ${styles[`badge_${color}`]}`}>{icon} {name}</span>
}

function formatDate(str) {
  return new Date(str).toLocaleString('en-GB', {
    day: '2-digit', month: 'short', year: 'numeric',
    hour: '2-digit', minute: '2-digit',
  })
}

function SessionRow({ session, onDelete, onClick }) {
  const [deleting, setDeleting] = useState(false)

  const handleDelete = async (e) => {
    e.stopPropagation()
    if (!confirm('Delete this session?')) return
    setDeleting(true)
    try {
      await agentApi.deleteSession(session.id)
      onDelete(session.id)
    } catch {
      setDeleting(false)
    }
  }

  return (
    <div className={styles.row} onClick={() => onClick(session)}>
      <div className={styles.rowLeft}>
        <span className={styles.rowId}>#{session.id}</span>
        <div className={styles.rowContent}>
          <p className={styles.rowTask}>{session.task}</p>
          <div className={styles.rowMeta}>
            <span className={`${styles.statusDot} ${session.status === 'completed' ? styles.dotOk : styles.dotFail}`} />
            <span className={styles.rowStatus}>{session.status}</span>
            <span className={styles.rowDate}>{formatDate(session.created_at)}</span>
            <span className={styles.rowSteps}>{session.steps?.length || 0} steps</span>
          </div>
        </div>
      </div>
      <div className={styles.rowRight}>
        <div className={styles.rowTools}>
          {session.tools_used?.map(t => <ToolBadge key={t} name={t} />)}
        </div>
        <button
          className={styles.deleteBtn}
          onClick={handleDelete}
          disabled={deleting}
        >
          {deleting ? '...' : '✕'}
        </button>
      </div>
    </div>
  )
}

function SessionModal({ session, onClose }) {
  if (!session) return null
  return (
    <div className={styles.overlay} onClick={onClose}>
      <div className={styles.modal} onClick={e => e.stopPropagation()}>
        <div className={styles.modalHeader}>
          <div>
            <span className={styles.modalId}>session #{session.id}</span>
            <p className={styles.modalTask}>{session.task}</p>
          </div>
          <button className={styles.closeBtn} onClick={onClose}>✕</button>
        </div>
        <div className={styles.modalBody}>
          {session.steps?.map((step, i) => (
            <div key={i} className={styles.modalStep}>
              <div className={styles.modalStepHead}>
                <span className={styles.modalStepNum}>step_{String(i+1).padStart(2,'0')}</span>
                {step.action && <ToolBadge name={step.action} />}
              </div>
              {step.thought && (
                <div className={styles.modalField}>
                  <span className={styles.fieldLabel}>thought</span>
                  <p className={styles.fieldText}>{step.thought}</p>
                </div>
              )}
              {step.action_input && (
                <div className={styles.modalField}>
                  <span className={styles.fieldLabel}>action_input</span>
                  <code className={styles.fieldCode}>{step.action_input}</code>
                </div>
              )}
              {step.observation && (
                <div className={styles.modalField}>
                  <span className={styles.fieldLabel}>observation</span>
                  <p className={styles.fieldText}>{step.observation}</p>
                </div>
              )}
            </div>
          ))}
          {session.final_answer && (
            <div className={styles.modalFinal}>
              <span className={styles.finalLabel}>▸ final answer</span>
              <p>{session.final_answer}</p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default function Sessions() {
  const [sessions, setSessions] = useState([])
  const [loading, setLoading] = useState(true)
  const [selected, setSelected] = useState(null)
  const [filter, setFilter] = useState('all')
  const navigate = useNavigate()

  useEffect(() => {
    agentApi.getSessions()
      .then(({ data }) => setSessions(data.reverse()))
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [])

  const filtered = filter === 'all' ? sessions : sessions.filter(s => s.status === filter)

  return (
    <div className={styles.page}>
      <div className={styles.header}>
        <div className={styles.headerLeft}>
          <span className={styles.title}>session_history</span>
          <span className={styles.count}>{sessions.length} total</span>
        </div>
        <div className={styles.filters}>
          {['all', 'completed', 'failed'].map(f => (
            <button
              key={f}
              className={filter === f ? `${styles.filter} ${styles.filterActive}` : styles.filter}
              onClick={() => setFilter(f)}
            >
              {f}
            </button>
          ))}
        </div>
        <button className={styles.newBtn} onClick={() => navigate('/')}>
          + new run
        </button>
      </div>

      <div className={styles.body}>
        {loading && (
          <div className={styles.loading}>
            <span className={styles.spinner} />
            loading sessions...
          </div>
        )}

        {!loading && filtered.length === 0 && (
          <div className={styles.empty}>
            <span className={styles.emptyIcon}>≡</span>
            <p>No sessions found</p>
            <button className={styles.emptyBtn} onClick={() => navigate('/')}>
              Run your first agent task →
            </button>
          </div>
        )}

        {!loading && filtered.map(s => (
          <SessionRow
            key={s.id}
            session={s}
            onDelete={id => setSessions(prev => prev.filter(s => s.id !== id))}
            onClick={setSelected}
          />
        ))}
      </div>

      {selected && <SessionModal session={selected} onClose={() => setSelected(null)} />}
    </div>
  )
}
