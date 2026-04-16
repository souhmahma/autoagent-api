import { useState, useEffect } from 'react'
import { adminApi } from '../services/api'
import styles from './Admin.module.css'

function StatCard({ label, value, color }) {
  return (
    <div className={styles.stat}>
      <span className={styles.statLabel}>{label}</span>
      <span className={styles.statValue} style={{ color: color || 'var(--text)' }}>{value}</span>
    </div>
  )
}

function UserRow({ user, onUpdate, onDelete }) {
  const [loading, setLoading] = useState(false)

  const toggleActive = async () => {
    setLoading(true)
    try {
      const { data } = await adminApi.updateUser(user.id, { is_active: !user.is_active })
      onUpdate(data)
    } finally { setLoading(false) }
  }

  const toggleRole = async () => {
    const newRole = user.role === 'admin' ? 'user' : 'admin'
    if (!confirm(`Change ${user.username} to ${newRole}?`)) return
    setLoading(true)
    try {
      const { data } = await adminApi.updateUser(user.id, { role: newRole })
      onUpdate(data)
    } finally { setLoading(false) }
  }

  const handleDelete = async () => {
    if (!confirm(`Delete user ${user.username}? This is irreversible.`)) return
    setLoading(true)
    try {
      await adminApi.deleteUser(user.id)
      onDelete(user.id)
    } catch (e) {
      alert(e.response?.data?.detail || 'Delete failed')
      setLoading(false)
    }
  }

  return (
    <div className={`${styles.userRow} ${!user.is_active ? styles.userInactive : ''}`}>
      <div className={styles.userAvatar}>
        {user.username[0].toUpperCase()}
      </div>
      <div className={styles.userInfo}>
        <span className={styles.userName}>{user.username}</span>
        <span className={styles.userEmail}>{user.email}</span>
      </div>
      <div className={styles.userMeta}>
        <span className={styles.userDate}>
          {new Date(user.created_at).toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' })}
        </span>
      </div>
      <div className={styles.userActions}>
        <span
          className={`${styles.roleBadge} ${user.role === 'admin' ? styles.roleAdmin : styles.roleUser}`}
          onClick={toggleRole}
          title="Click to toggle role"
          style={{ cursor: loading ? 'default' : 'pointer' }}
        >
          {user.role}
        </span>
        <button
          className={`${styles.actionBtn} ${user.is_active ? styles.btnDeactivate : styles.btnActivate}`}
          onClick={toggleActive}
          disabled={loading}
        >
          {user.is_active ? 'deactivate' : 'activate'}
        </button>
        <button
          className={`${styles.actionBtn} ${styles.btnDelete}`}
          onClick={handleDelete}
          disabled={loading}
        >
          delete
        </button>
      </div>
    </div>
  )
}

function SessionRow({ session }) {
  const [open, setOpen] = useState(false)
  return (
    <div className={styles.sRow}>
      <div className={styles.sRowHead} onClick={() => setOpen(o => !o)}>
        <span className={styles.sId}>#{session.id}</span>
        <span className={styles.sUser}>user_{session.user_id}</span>
        <p className={styles.sTask}>{session.task}</p>
        <span className={`${styles.sDot} ${session.status === 'completed' ? styles.dotOk : styles.dotFail}`} />
        <span className={styles.sDate}>
          {new Date(session.created_at).toLocaleDateString('en-GB')}
        </span>
        <span className={styles.toggle}>{open ? '▾' : '▸'}</span>
      </div>
      {open && session.final_answer && (
        <div className={styles.sAnswer}>
          <span className={styles.sAnswerLabel}>final_answer</span>
          <p>{session.final_answer}</p>
        </div>
      )}
    </div>
  )
}

export default function Admin() {
  const [tab, setTab] = useState('overview')
  const [stats, setStats] = useState(null)
  const [users, setUsers] = useState([])
  const [sessions, setSessions] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([
      adminApi.getStats(),
      adminApi.getUsers(),
      adminApi.getAllSessions(),
    ]).then(([s, u, sess]) => {
      setStats(s.data)
      setUsers(u.data)
      setSessions(sess.data)
    }).catch(() => {}).finally(() => setLoading(false))
  }, [])

  if (loading) return (
    <div className={styles.loading}>
      <span className={styles.spinner} /> loading admin panel...
    </div>
  )

  return (
    <div className={styles.page}>
      <div className={styles.header}>
        <span className={styles.title}>admin_panel</span>
        <div className={styles.tabs}>
          {['overview', 'users', 'sessions'].map(t => (
            <button
              key={t}
              className={tab === t ? `${styles.tab} ${styles.tabActive}` : styles.tab}
              onClick={() => setTab(t)}
            >
              {t}
            </button>
          ))}
        </div>
      </div>

      <div className={styles.body}>
        {tab === 'overview' && stats && (
          <div className={styles.overview}>
            <div className={styles.statsGrid}>
              <StatCard label="total_users" value={stats.total_users} color="var(--blue)" />
              <StatCard label="total_sessions" value={stats.total_sessions} color="var(--text)" />
              <StatCard label="completed" value={stats.completed_sessions} color="var(--accent)" />
              <StatCard label="failed" value={stats.failed_sessions} color="var(--red)" />
              <StatCard label="success_rate" value={`${stats.success_rate}%`} color="var(--amber)" />
            </div>
            <div className={styles.section}>
              <span className={styles.sectionTitle}>recent_sessions</span>
              <div className={styles.recentList}>
                {sessions.slice(0, 5).map(s => (
                  <div key={s.id} className={styles.recentRow}>
                    <span className={styles.recentId}>#{s.id}</span>
                    <p className={styles.recentTask}>{s.task}</p>
                    <span className={`${styles.sDot} ${s.status === 'completed' ? styles.dotOk : styles.dotFail}`} />
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {tab === 'users' && (
          <div className={styles.section}>
            <div className={styles.sectionHeader}>
              <span className={styles.sectionTitle}>users</span>
              <span className={styles.sectionCount}>{users.length} total</span>
            </div>
            <div className={styles.userList}>
              {users.map(u => (
                <UserRow
                  key={u.id}
                  user={u}
                  onUpdate={updated => setUsers(prev => prev.map(x => x.id === updated.id ? updated : x))}
                  onDelete={id => setUsers(prev => prev.filter(x => x.id !== id))}
                />
              ))}
            </div>
          </div>
        )}

        {tab === 'sessions' && (
          <div className={styles.section}>
            <div className={styles.sectionHeader}>
              <span className={styles.sectionTitle}>all_sessions</span>
              <span className={styles.sectionCount}>{sessions.length} total</span>
            </div>
            <div className={styles.sessionList}>
              {sessions.map(s => <SessionRow key={s.id} session={s} />)}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
