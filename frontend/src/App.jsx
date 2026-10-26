import React from 'react'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Navbar from './components/Navbar'
import Footer from './components/Footer'
import HomePage from './pages/HomePage'
import ScanPage from './pages/ScanPage'
import HistoryPage from './pages/HistoryPage'
import AboutPage from './pages/AboutPage'

export default function App() {
  return (
    <BrowserRouter>
      <Navbar />
      <main>
        <Routes>
          <Route path="/"        element={<HomePage />} />
          <Route path="/scan"    element={<ScanPage />} />
          <Route path="/history" element={<HistoryPage />} />
          <Route path="/about"   element={<AboutPage />} />
        </Routes>
      </main>
      <Footer />
    </BrowserRouter>
  )
}
