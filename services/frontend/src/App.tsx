import { Routes, Route } from 'react-router-dom';
import { useAuth } from './contexts/AuthContext';
import LoginPage from './components/auth/LoginPage';
import { Layout } from './components/layout/Layout';
import { LoadingSpinner } from './components/LoadingSpinner';
import DashboardPage from './pages/DashboardPage';
import CoachPage from './pages/CoachPage';
import SettingsPage from './pages/SettingsPage';

export default function App() {
  const { loading, isAuthenticated } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <LoadingSpinner message="Checking authentication..." />
      </div>
    );
  }

  if (!isAuthenticated) {
    return <LoginPage />;
  }

  return (
    <Routes>
      <Route element={<Layout />}>
        <Route index element={<DashboardPage />} />
        <Route path="coach" element={<CoachPage />} />
        <Route path="settings" element={<SettingsPage />} />
      </Route>
    </Routes>
  );
}
