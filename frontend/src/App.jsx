import React, { useState, useEffect, useCallback } from 'react';
import { BrowserRouter, Routes, Route, useLocation } from 'react-router-dom';
import Header from './components/Header';
import LandingPage from './pages/LandingPage';
import PreparePage from './pages/PreparePage';
import ConsolePage from './pages/ConsolePage';
import OutputPage from './pages/OutputPage';
import StagePage from './pages/StagePage';
import CloseoutPage from './pages/CloseoutPage';

function AppLayout({ plan, setPlan, streamStatus, setStreamStatus, isHydrating }) {
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
                isHydrating={isHydrating}
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
            element={<CloseoutPage plan={plan} isHydrating={isHydrating} />}
          />
        </Routes>
      </main>
    </>
  );
}

export default function App() {
  const [plan, setPlanState] = useState(null);
  const [streamStatus, setStreamStatus] = useState('draft');
  const [isHydrating, setIsHydrating] = useState(true);

  const setPlan = useCallback((p) => {
    setPlanState(p);
    try {
      if (p?.id) {
        localStorage.setItem('selah_plan_id', p.id);
      }
    } catch (e) {
      console.warn('Could not save plan ID to localStorage:', e);
    }
  }, []);

  useEffect(() => {
    let id;
    try {
      id = localStorage.getItem('selah_plan_id');
    } catch (e) {
      console.warn('Could not read plan ID from localStorage:', e);
    }

    if (!id) {
      setIsHydrating(false);
      return;
    }

    let cancelled = false;
    fetch(`/api/plan/${id}`)
      .then((r) => (r.ok ? r.json() : null))
      .then((d) => {
        if (cancelled) return;
        if (d?.plan) {
          setPlanState(d.plan);
          setStreamStatus(d.plan.status || 'draft');
        } else {
          try {
            localStorage.removeItem('selah_plan_id');
          } catch {}
        }
      })
      .catch((err) => {
        console.error('Plan rehydration error:', err);
      })
      .finally(() => {
        if (!cancelled) setIsHydrating(false);
      });

    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <BrowserRouter>
      <AppLayout
        plan={plan}
        setPlan={setPlan}
        streamStatus={streamStatus}
        setStreamStatus={setStreamStatus}
        isHydrating={isHydrating}
      />
    </BrowserRouter>
  );
}
