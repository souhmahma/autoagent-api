import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import styles from './Auth.module.css'

export default function Auth() {
  const [mode, setMode] = useState('login')
  const [form, setForm] = useState({ email: '', username: '', password: '' })
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const { login, register } = useAuth()
  const navigate = useNavigate()

  const handle = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      if (mode === 'login') {
        await login(form.email, form.password)
      } else {
        await register(form.email, form.username, form.password)
      }
      navigate('/')
    } catch (err) {
      setError(err.response?.data?.detail || 'Something went wrong')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className={styles.page}>
      <div className={styles.grid} />
      <div className={styles.card}>
        <div className={styles.logo}>
          <span className={styles.logoIcon}>◈</span>
          <span className={styles.logoText}>AutoAgent</span>
        </div>
        <div className={styles.tabs}>
          <button
            className={mode === 'login' ? styles.tabActive : styles.tab}
            onClick={() => setMode('login')}
            type="button"
          >
            login
          </button>
          <button
            className={mode === 'register' ? styles.tabActive : styles.tab}
            onClick={() => setMode('register')}
            type="button"
          >
            register
          </button>
        </div>
        <form onSubmit={handle} className={styles.form}>
          <div className={styles.field}>
            <label className={styles.label}>email</label>
            <input
              type="email"
              className={styles.input}
              value={form.email}
              onChange={e => setForm(f => ({ ...f, email: e.target.value }))}
              placeholder="you@example.com"
              required
            />
          </div>
          {mode === 'register' && (
            <div className={styles.field}>
              <label className={styles.label}>username</label>
              <input
                type="text"
                className={styles.input}
                value={form.username}
                onChange={e => setForm(f => ({ ...f, username: e.target.value }))}
                placeholder="souhail"
                required
              />
            </div>
          )}
          <div className={styles.field}>
            <label className={styles.label}>password</label>
            <input
              type="password"
              className={styles.input}
              value={form.password}
              onChange={e => setForm(f => ({ ...f, password: e.target.value }))}
              placeholder="••••••••"
              required
            />
          </div>
          {error && <div className={styles.error}>✗ {error}</div>}
          <button type="submit" className={styles.submit} disabled={loading}>
            {loading ? <span className={styles.spinner} /> : null}
            {loading ? 'processing...' : mode === 'login' ? '→ sign in' : '→ create account'}
          </button>
        </form>
        <p className={styles.hint}>
          {mode === 'login' ? 'Powered by Gemini ReAct Agent' : 'Your sessions are saved automatically'}
        </p>
      </div>
    </div>
  )
}
