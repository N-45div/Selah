import React, { useState } from 'react';
import { BrowserRouter, Routes, Route, useLocation } from 'react-router-dom';
import Header from './components/Header';
import PreparePage from './pages/PreparePage';
import ConsolePage from './pages/ConsolePage';
import OutputPage from './pages/OutputPage';
import CloseoutPage from './pages/CloseoutPage';

function AppLayout({ plan, setPlan, streamStatus, setStreamStatus }) {
  const location = useLocation();
  const isOutputScreen = location.pathname === '/output';

  return (
    <>
      {/* Hide header on the clean full-screen OBS output projection page */}
      {!isOutputScreen && <Header currentPlan={plan} streamStatus={streamStatus} />}

      <main>
        <Routes>
          <Route
            path="/"
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
