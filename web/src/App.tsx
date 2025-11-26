import { BrowserRouter, Routes, Route } from 'react-router-dom'
import LandingPage from './pages/LandingPage'
import PricingPage from './pages/PricingPage'
import Playground from './pages/Playground'

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<LandingPage />} />
        <Route path="/pricing" element={<PricingPage />} />
        <Route path="/playground" element={<Playground />} />
      </Routes>
    </BrowserRouter>
  )
}

export default App
