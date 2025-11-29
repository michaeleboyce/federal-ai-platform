import { checkAdminSession } from '@/lib/admin-auth';
import { getProfilesWithTools, getToolStats } from '@/lib/agency-tools-db';
import AdminLoginForm from './AdminLoginForm';
import AdminPanel from './AdminPanel';

export const dynamic = 'force-dynamic';

export default async function AdminPage() {
  const isAuthenticated = await checkAdminSession();

  if (!isAuthenticated) {
    return <AdminLoginForm />;
  }

  const [profiles, stats] = await Promise.all([
    getProfilesWithTools(),
    getToolStats(),
  ]);

  return <AdminPanel initialProfiles={profiles} initialStats={stats} />;
}
