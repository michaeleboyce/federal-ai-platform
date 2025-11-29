import Link from 'next/link';
import { getProfilesWithTools, getToolStats, getDepartmentStats } from '@/lib/agency-tools-db';
import ToolsHierarchyView from './ToolsHierarchyView';
import Breadcrumbs from '@/components/Breadcrumbs';

export const dynamic = 'force-dynamic';

export default async function AgencyAIUsagePage() {
  const [profiles, stats, deptStats] = await Promise.all([
    getProfilesWithTools(),
    getToolStats(),
    getDepartmentStats(),
  ]);

  return (
    <div className="min-h-screen bg-cream">
      <header className="bg-charcoal-800 py-6 border-b-4 border-ifp-purple">
        <div className="container mx-auto px-4">
          <Breadcrumbs
            items={[
              { label: 'AI Adoption', href: undefined },
            ]}
          />
          <h1 className="font-serif text-3xl font-medium text-white">
            Federal Agency AI Adoption
          </h1>
          <p className="text-charcoal-300 mt-2">
            Tracking generative AI tools adopted by federal agencies - chatbots, coding assistants, and document automation
          </p>
        </div>
      </header>

      <main className="container mx-auto px-4 py-8">
        {/* Statistics Dashboard */}
        <div className="bg-white rounded-lg border border-charcoal-200 p-6 mb-6">
          <h2 className="font-serif text-xl font-medium text-charcoal mb-4">
            AI Adoption Statistics
          </h2>
          <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-4">
            <div className="bg-white p-4 rounded-lg border-l-4 border-charcoal-600">
              <div className="text-2xl font-semibold text-charcoal">{profiles.length}</div>
              <div className="text-sm text-charcoal-500">Agencies Tracked</div>
            </div>
            <div className="bg-white p-4 rounded-lg border-l-4 border-ifp-purple">
              <div className="text-2xl font-semibold text-charcoal">{stats.staffChatbot}</div>
              <div className="text-sm text-charcoal-500">Staff Chatbots</div>
            </div>
            <div className="bg-white p-4 rounded-lg border-l-4 border-ifp-orange">
              <div className="text-2xl font-semibold text-charcoal">{stats.codingAssistant}</div>
              <div className="text-sm text-charcoal-500">Coding Assistants</div>
            </div>
            <div className="bg-white p-4 rounded-lg border-l-4 border-green-600">
              <div className="text-2xl font-semibold text-charcoal">{stats.documentAutomation}</div>
              <div className="text-sm text-charcoal-500">Doc Automation</div>
            </div>
            <div className="bg-white p-4 rounded-lg border-l-4 border-status-success">
              <div className="text-2xl font-semibold text-charcoal">{stats.agenciesWithTools}</div>
              <div className="text-sm text-charcoal-500">With Tools</div>
            </div>
            <div className="bg-white p-4 rounded-lg border-l-4 border-charcoal-400">
              <div className="text-2xl font-semibold text-charcoal">{stats.agenciesWithoutTools}</div>
              <div className="text-sm text-charcoal-500">No Public Tool</div>
            </div>
            <div className="bg-white p-4 rounded-lg border-l-4 border-charcoal-300">
              <div className="text-2xl font-semibold text-charcoal">{stats.total}</div>
              <div className="text-sm text-charcoal-500">Total Tools</div>
            </div>
          </div>
        </div>

        {/* Info Panel */}
        <div className="bg-cream-200 border border-charcoal-200 rounded-lg p-4 mb-6">
          <h3 className="text-sm font-semibold text-charcoal mb-2">About This Data</h3>
          <p className="text-sm text-charcoal-600 mb-2">
            This dashboard tracks publicly announced generative AI tools adopted by federal agencies for internal use:
          </p>
          <div className="flex flex-wrap gap-2 mt-3">
            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-ifp-purple-light text-ifp-purple-dark border border-ifp-purple">
              Staff Chatbots (e.g., StateChat, ChatCDC, NASA-GPT)
            </span>
            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-ifp-orange-light text-ifp-orange-dark border border-ifp-orange">
              Coding Assistants (e.g., GitHub Copilot)
            </span>
            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-700 border border-green-600">
              Document Automation (e.g., Ask Sage, Agentforce)
            </span>
          </div>
          <p className="text-xs text-charcoal-500 mt-3">
            Data compiled from public agency announcements, press releases, and AI inventories. Last updated: November 2025
          </p>
        </div>

        {/* Link to FedRAMP AI Services */}
        <Link
          href="/ai-services"
          className="block bg-white border-2 border-charcoal-300 rounded-lg p-6 mb-6 hover:border-ifp-purple hover:shadow-md transition-all"
        >
          <div className="flex items-center justify-between">
            <div>
              <h2 className="font-serif text-2xl font-medium text-charcoal mb-2">
                FedRAMP AI Services
              </h2>
              <p className="text-charcoal-500">
                View the FedRAMP-authorized AI services available to agencies
              </p>
            </div>
            <div className="text-right">
              <div className="text-sm font-semibold text-ifp-purple">View AI Services →</div>
            </div>
          </div>
        </Link>

        {/* Tools Hierarchy View */}
        <ToolsHierarchyView profiles={profiles} stats={stats} />
      </main>

      <footer className="bg-charcoal-900 text-cream py-6 mt-12 border-t-4 border-ifp-purple">
        <div className="container mx-auto px-4 text-center text-sm">
          <p>
            Data compiled from public sources including agency press releases, news articles, and government reports
          </p>
          <p className="mt-2 text-charcoal-400">
            Sources include Nextgov, FedScoop, Defense One, and agency announcements
          </p>
        </div>
      </footer>
    </div>
  );
}
