import { ProfileCard } from '../components/settings/ProfileCard';
import { ApiKeyCard } from '../components/settings/ApiKeyCard';
import { DangerZone } from '../components/settings/DangerZone';

export default function SettingsPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-text-primary">Settings</h1>
        <p className="text-text-secondary text-sm mt-1">Manage your account and preferences</p>
      </div>

      <ProfileCard />
      <ApiKeyCard />
      <DangerZone />
    </div>
  );
}
