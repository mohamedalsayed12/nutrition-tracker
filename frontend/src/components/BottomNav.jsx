import { NavLink } from 'react-router-dom'

export default function BottomNav() {
  return (
    <nav className="bottom-nav" aria-label="Primary">
      <NavLink to="/app" end className={({ isActive }) => `nav-item ${isActive ? 'is-active' : ''}`}>
        <span className="nav-icon" aria-hidden="true">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
            <circle cx="12" cy="12" r="8" />
            <path d="M12 8v4l2.5 1.5" />
          </svg>
        </span>
        <span>Today</span>
      </NavLink>
      <NavLink to="/app/weekly" className={({ isActive }) => `nav-item ${isActive ? 'is-active' : ''}`}>
        <span className="nav-icon" aria-hidden="true">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
            <path d="M5 19V10M12 19V5M19 19v-7" />
          </svg>
        </span>
        <span>Weekly</span>
      </NavLink>
      <NavLink to="/app/add" className={({ isActive }) => `nav-fab ${isActive ? 'is-active' : ''}`} aria-label="Add food">
        <span aria-hidden="true">+</span>
      </NavLink>
      <NavLink to="/app/goals" className={({ isActive }) => `nav-item ${isActive ? 'is-active' : ''}`}>
        <span className="nav-icon" aria-hidden="true">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
            <circle cx="12" cy="12" r="8" />
            <circle cx="12" cy="12" r="4" />
            <circle cx="12" cy="12" r="1.2" fill="currentColor" />
          </svg>
        </span>
        <span>Goals</span>
      </NavLink>
    </nav>
  )
}
