import React, { useState } from 'react';
import { BrowserRouter, Routes, Route, useLocation } from 'react-router-dom';
import Header from './components/Header';
import LandingPage from './pages/LandingPage';
import PreparePage from './pages/PreparePage';
import ConsolePage from './pages/ConsolePage';
import OutputPage from './pages/OutputPage';
import StagePage from './pages/StagePage';
import CloseoutPage from './pages/CloseoutPage';

function AppLayout({ plan, setPlan, streamStatus, setStreamStatus }) {
  const location = useLocation();
  const isDedicatedScreen = location.pathname === '/output' || location.pathname === '/stage';

  return (
    <>
      {/* Hide header on dedicated full-screen OBS projection and stage monitor pages */}
      {!isDedicatedScreen && <Header currentPlan={plan} streamStatus={streamStatus} />}

      <main>
        <Routes>
          <Route
            path="/"
            element={<LandingPage setPlan={setPlan} />}
          />
          <Route
            path="/prepare"
            element={<PreparePage plan={plan} setPlan={setPlan} />}
          />
          <Route
            path="/console"
            element={
              <ConsolePage
                plan={plan}
                setPlan={setPlan}
                setStreamStatus={setStreamStatus}
              />
            }
          />
          <Route
            path="/output"
            element={<OutputPage plan={plan} />}
          />
          <Route
            path="/stage"
            element={<StagePage plan={plan} />}
          />
          <Route
            path="/closeout"
            element={<CloseoutPage plan={plan} />}
          />
        </Routes>
      </main>
    </>
  );
}

export default function App() {
  const [plan, setPlan] = useState(null);
  const [streamStatus, setStreamStatus] = useState('draft');

  return (
    <BrowserRouter>
      <AppLayout
        plan={plan}
        setPlan={setPlan}
        streamStatus={streamStatus}
        setStreamStatus={setStreamStatus}
      />
    </BrowserRouter>
  );
}
