import { PageShell } from '../components/ui/PageShell';
import { ProfileSection } from '../components/settings/ProfileSection';
import { ApiKeySection } from '../components/settings/ApiKeySection';
import { BodyweightSection } from '../components/settings/BodyweightSection';
import { AccountSection } from '../components/settings/AccountSection';

export default function SettingsPage() {
  return (
    <PageShell>
      <div>
        <h1 className="text-2xl font-bold text-chalk">Settings</h1>
        <p className="text-steel text-sm mt-1">Manage your account and preferences</p>
      </div>

      <div className="card mt-6 p-0 px-4">
        <ProfileSection />
        <BodyweightSection />
        <ApiKeySection />
        <AccountSection />
      </div>
    </PageShell>
  );
}
