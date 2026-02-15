import { ApiKeySettings } from '../components/ApiKeySettings';
import { useAuth } from '../contexts/AuthContext';

export default function SettingsPage() {
  const { user, logout } = useAuth();

  return (
    <div className="animate-fadeIn space-y-4">
      <div>
        <h2 className="text-lg font-bold text-text-primary">Settings</h2>
        <p className="text-text-secondary text-sm mt-0.5">Manage your account and preferences</p>
      </div>

      {/* Profile */}
      <div className="card">
        <h3 className="text-sm font-bold text-text-primary mb-3">Profile</h3>
        <div className="flex items-center gap-3">
          {user?.picture_url ? (
            <img
              src={user.picture_url}
              alt=""
              className="w-10 h-10 rounded-full"
              referrerPolicy="no-referrer"
            />
          ) : (
            <div className="w-10 h-10 rounded-full bg-surface-light border border-border flex items-center justify-center text-text-secondary text-sm font-bold">
              {user?.name?.[0]?.toUpperCase() || '?'}
            </div>
          )}
          <div>
            <p className="text-text-primary text-sm font-medium">{user?.name}</p>
            <p className="text-text-secondary text-xs">{user?.email}</p>
          </div>
        </div>
      </div>

      {/* API Key */}
      <div className="card">
        <h3 className="text-sm font-bold text-text-primary mb-3">AI Coach API Key</h3>
        <ApiKeySettings />
      </div>

      {/* Sign out */}
      <div className="card">
        <h3 className="text-sm font-bold text-text-primary mb-1">Account</h3>
        <p className="text-text-secondary text-xs mb-3">Sign out of your account on this device.</p>
        <button className="btn btn-danger" onClick={logout}>
          Sign Out
        </button>
      </div>
    </div>
  );
}
