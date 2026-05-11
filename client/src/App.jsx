import React from 'react'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import PlayerPage from './pages/PlayerPage'
import StaffPage from './pages/StaffPage'

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<PlayerPage />} />
        <Route path="/staff" element={<StaffPage />} />
      </Routes>
    </BrowserRouter>
  )
}
