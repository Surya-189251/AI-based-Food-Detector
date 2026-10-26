import React, { useState } from 'react'
import { NavLink } from 'react-router-dom'

export default function Navbar() {
  const [open, setOpen] = useState(false)

  return (
    <nav className="navbar">
      <div className="navbar-inner">
        <NavLink to="/" className="navbar-brand" onClick={() => setOpen(false)}>
          <span className="brand-icon">🍎</span>
          FreshCheck AI
        </NavLink>

        <button
          className="hamburger"
          aria-label="Toggle menu"
          aria-expanded={open}
          onClick={() => setOpen(o => !o)}
        >
          {open ? '✕' : '☰'}
        </button>

        <ul className={`navbar-links${open ? ' open' : ''}`}>
          {[
            { to: '/',        label: 'Home'    },
            { to: '/scan',    label: '🔍 Scan'  },
            { to: '/history', label: 'History' },
            { to: '/about',   label: 'About'   },
          ].map(({ to, label }) => (
            <li key={to}>
              <NavLink
                to={to}
                end={to === '/'}
                className={({ isActive }) => isActive ? 'active' : ''}
                onClick={() => setOpen(false)}
              >
                {label}
              </NavLink>
            </li>
          ))}
        </ul>
      </div>
    </nav>
  )
}
