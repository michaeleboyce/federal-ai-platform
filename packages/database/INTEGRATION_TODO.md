# AI Use Case Integration - Remaining Steps

## ✅ Completed Steps

1. **Data Loading** - Successfully loaded 2,049 use cases from CSV into PostgreSQL
2. **Data Verification** - Verified data integrity:
   - 2,049 use cases with details
   - 325 GenAI use cases
   - 73 LLM use cases
   - 143 chatbot use cases
   - 42 unique agencies
   - Top domain: Document Intelligence (1,258 use cases)

3. **Matching Script Created** - Built intelligent matching system at `match-use-cases-to-fedramp.ts`

---

## 🔄 Remaining Steps

### Phase 1: Run the Matching System

**Location:** `/Users/michaelboyce/Documents/Programming/ifp/ai-use-case-inventory/packages/database`

```bash
npx tsx match-use-cases-to-fedramp.ts
```

This will:
- Match use cases to FedRAMP services based on:
  - Provider names (high confidence)
  - Commercial products mentioned (high confidence)
  - AI capabilities - GenAI/LLM (medium confidence)
  - Chatbot + GenAI compatibility (low confidence)
- Populate the `use_case_fedramp_matches` table

Expected output: ~100-500 matches with varying confidence levels

---

### Phase 2: Enhance UseCaseRepository

**File:** `packages/database/src/repositories/UseCaseRepository.ts`

Add these methods to the `UseCaseRepository` class:

```typescript
// Get use cases with filtering
async getUseCasesWithFilters(filters: {
  agency?: string;
  domain?: string;
  stage?: string;
  hasGenai?: boolean;
  hasLlm?: boolean;
  hasChatbot?: boolean;
  limit?: number;
  offset?: number;
}): Promise<AIUseCaseRecord[]> {
  let query = db.select().from(aiUseCases);

  if (filters.agency) {
    query = query.where(eq(aiUseCases.agency, filters.agency));
  }
  if (filters.domain) {
    query = query.where(eq(aiUseCases.domainCategory, filters.domain));
  }
  if (filters.stage) {
    query = query.where(eq(aiUseCases.stageOfDevelopment, filters.stage));
  }
  if (filters.hasGenai) {
    query = query.where(eq(aiUseCases.genaiFlag, true));
  }
  if (filters.hasLlm) {
    query = query.where(eq(aiUseCases.hasLlm, true));
  }
  if (filters.hasChatbot) {
    query = query.where(eq(aiUseCases.hasChatbot, true));
  }

  if (filters.limit) {
    query = query.limit(filters.limit);
  }
  if (filters.offset) {
    query = query.offset(filters.offset);
  }

  return await query;
}

// Search use cases
async searchUseCases(searchTerm: string): Promise<AIUseCaseRecord[]> {
  return await db.select()
    .from(aiUseCases)
    .where(
      or(
        like(aiUseCases.useCaseName, `%${searchTerm}%`),
        like(aiUseCases.agency, `%${searchTerm}%`),
        like(aiUseCases.intendedPurpose, `%${searchTerm}%`)
      )
    )
    .limit(100);
}

// Get FedRAMP matches for a use case
async getFedRAMPMatchesForUseCase(useCaseId: number): Promise<UseCaseFedrampMatchRecord[]> {
  return await db.select()
    .from(useCaseFedrampMatches)
    .where(eq(useCaseFedrampMatches.useCaseId, useCaseId))
    .orderBy(desc(useCaseFedrampMatches.confidence));
}

// Get use cases for a FedRAMP product
async getUseCasesForProduct(productId: string): Promise<any[]> {
  return await db.select({
    useCase: aiUseCases,
    match: useCaseFedrampMatches
  })
  .from(useCaseFedrampMatches)
  .innerJoin(aiUseCases, eq(useCaseFedrampMatches.useCaseId, aiUseCases.id))
  .where(eq(useCaseFedrampMatches.productId, productId))
  .orderBy(desc(useCaseFedrampMatches.confidence));
}
```

After adding, rebuild the package:
```bash
cd packages/database
pnpm build
```

---

### Phase 3: Update Frontend Use Case Page

**File:** `frontend/app/use-cases/UseCaseTable.tsx`

This is a client component. Add filtering functionality:

```typescript
'use client';

import { useState, useMemo } from 'react';
import Link from 'next/link';
import type { UseCase } from '@/lib/use-case-db';

export default function UseCaseTable({
  useCases,
  domains,
  agencies,
  stages
}: {
  useCases: UseCase[];
  domains: string[];
  agencies: string[];
  stages: string[];
}) {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedDomain, setSelectedDomain] = useState('');
  const [selectedAgency, setSelectedAgency] = useState('');
  const [selectedStage, setSelectedStage] = useState('');
  const [showGenaiOnly, setShowGenaiOnly] = useState(false);
  const [showLlmOnly, setShowLlmOnly] = useState(false);

  const filteredUseCases = useMemo(() => {
    return useCases.filter(uc => {
      // Search filter
      if (searchTerm && !uc.use_case_name.toLowerCase().includes(searchTerm.toLowerCase()) &&
          !uc.agency.toLowerCase().includes(searchTerm.toLowerCase())) {
        return false;
      }

      // Domain filter
      if (selectedDomain && uc.domain_category !== selectedDomain) {
        return false;
      }

      // Agency filter
      if (selectedAgency && uc.agency !== selectedAgency) {
        return false;
      }

      // Stage filter
      if (selectedStage && uc.stage_of_development !== selectedStage) {
        return false;
      }

      // GenAI filter
      if (showGenaiOnly && !uc.genai_flag) {
        return false;
      }

      // LLM filter
      if (showLlmOnly && !uc.has_llm) {
        return false;
      }

      return true;
    });
  }, [useCases, searchTerm, selectedDomain, selectedAgency, selectedStage, showGenaiOnly, showLlmOnly]);

  return (
    <div className="bg-white rounded-lg border border-gov-slate-200 p-6">
      {/* Filters */}
      <div className="mb-6 space-y-4">
        <input
          type="text"
          placeholder="Search use cases..."
          className="w-full px-4 py-2 border border-gov-slate-300 rounded-md"
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
        />

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <select
            className="px-4 py-2 border border-gov-slate-300 rounded-md"
            value={selectedDomain}
            onChange={(e) => setSelectedDomain(e.target.value)}
          >
            <option value="">All Domains</option>
            {domains.map(d => <option key={d} value={d}>{d}</option>)}
          </select>

          <select
            className="px-4 py-2 border border-gov-slate-300 rounded-md"
            value={selectedAgency}
            onChange={(e) => setSelectedAgency(e.target.value)}
          >
            <option value="">All Agencies</option>
            {agencies.map(a => <option key={a} value={a}>{a}</option>)}
          </select>

          <select
            className="px-4 py-2 border border-gov-slate-300 rounded-md"
            value={selectedStage}
            onChange={(e) => setSelectedStage(e.target.value)}
          >
            <option value="">All Stages</option>
            {stages.map(s => <option key={s} value={s}>{s}</option>)}
          </select>
        </div>

        <div className="flex gap-4">
          <label className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={showGenaiOnly}
              onChange={(e) => setShowGenaiOnly(e.target.checked)}
            />
            GenAI Only
          </label>

          <label className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={showLlmOnly}
              onChange={(e) => setShowLlmOnly(e.target.checked)}
            />
            LLM Only
          </label>
        </div>
      </div>

      <p className="text-sm text-gov-slate-600 mb-4">
        Showing {filteredUseCases.length} of {useCases.length} use cases
      </p>

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="min-w-full">
          <thead className="bg-gov-slate-50">
            <tr>
              <th className="px-4 py-3 text-left text-sm font-semibold">Use Case</th>
              <th className="px-4 py-3 text-left text-sm font-semibold">Agency</th>
              <th className="px-4 py-3 text-left text-sm font-semibold">Domain</th>
              <th className="px-4 py-3 text-left text-sm font-semibold">AI Type</th>
              <th className="px-4 py-3 text-left text-sm font-semibold">Stage</th>
            </tr>
          </thead>
          <tbody>
            {filteredUseCases.map((uc) => (
              <tr key={uc.id} className="border-t hover:bg-gov-slate-50">
                <td className="px-4 py-3">
                  <Link href={`/use-cases/${uc.slug}`} className="text-gov-navy-600 hover:underline">
                    {uc.use_case_name}
                  </Link>
                </td>
                <td className="px-4 py-3 text-sm">{uc.agency}</td>
                <td className="px-4 py-3 text-sm">{uc.domain_category || 'N/A'}</td>
                <td className="px-4 py-3">
                  <div className="flex gap-1">
                    {uc.genai_flag && <span className="px-2 py-1 text-xs bg-ai-teal text-white rounded">GenAI</span>}
                    {uc.has_llm && <span className="px-2 py-1 text-xs bg-ai-indigo text-white rounded">LLM</span>}
                    {uc.has_chatbot && <span className="px-2 py-1 text-xs bg-ai-blue text-white rounded">Chatbot</span>}
                  </div>
                </td>
                <td className="px-4 py-3 text-sm">{uc.stage_of_development}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
```

---

### Phase 4: Add FedRAMP Matches to Use Case Detail Pages

**File:** `frontend/app/use-cases/[slug]/page.tsx`

Update to fetch and display FedRAMP matches:

```typescript
import { getUseCaseBySlug, getUseCaseDetails } from '@/lib/use-case-db';
import { db } from '@/lib/db/client';
import { useCaseFedRampMatches } from '@/lib/db/schema';
import { eq } from 'drizzle-orm';

export default async function UseCaseDetailPage({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  const useCase = await getUseCaseBySlug(slug);

  if (!useCase) {
    return <div>Use case not found</div>;
  }

  const details = await getUseCaseDetails(useCase.id);

  // Get FedRAMP matches
  const fedRampMatches = await db.select()
    .from(useCaseFedRampMatches)
    .where(eq(useCaseFedRampMatches.useCaseId, useCase.id))
    .orderBy(desc(useCaseFedRampMatches.confidence));

  return (
    <div>
      {/* Existing use case details... */}

      {/* Add FedRAMP Matches Section */}
      {fedRampMatches.length > 0 && (
        <div className="bg-white rounded-lg border border-gov-slate-200 p-6 mt-6">
          <h2 className="text-xl font-semibold mb-4">Potential FedRAMP Services</h2>
          <p className="text-sm text-gov-slate-600 mb-4">
            These FedRAMP-authorized services may support this use case based on provider and capability matching.
          </p>

          <div className="space-y-3">
            {fedRampMatches.map((match) => (
              <div key={match.id} className="border border-gov-slate-200 rounded-lg p-4">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <Link
                      href={`/product/${match.productId}`}
                      className="font-semibold text-gov-navy-600 hover:underline"
                    >
                      {match.productName}
                    </Link>
                    <p className="text-sm text-gov-slate-600">{match.providerName}</p>
                    {match.matchReason && (
                      <p className="text-xs text-gov-slate-500 mt-2">{match.matchReason}</p>
                    )}
                  </div>
                  <span className={`
                    px-3 py-1 text-xs font-semibold rounded
                    ${match.confidence === 'high' ? 'bg-status-success text-white' : ''}
                    ${match.confidence === 'medium' ? 'bg-status-warning text-white' : ''}
                    ${match.confidence === 'low' ? 'bg-status-info text-white' : ''}
                  `}>
                    {match.confidence} confidence
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
```

---

### Phase 5: Add Cross-Linking from FedRAMP Product Pages

**File:** `frontend/app/product/[id]/page.tsx`

Add a section showing use cases that might use this product:

```typescript
import { db } from '@/lib/db/client';
import { useCaseFedRampMatches, aiUseCases } from '@/lib/db/schema';
import { eq } from 'drizzle-orm';

// In the page component, after fetching product details:

const relatedUseCases = await db.select({
  useCase: aiUseCases,
  match: useCaseFedRampMatches
})
.from(useCaseFedRampMatches)
.innerJoin(aiUseCases, eq(useCaseFedRampMatches.useCaseId, aiUseCases.id))
.where(eq(useCaseFedRampMatches.productId, id))
.orderBy(desc(useCaseFedRampMatches.confidence))
.limit(10);

// Then in the JSX:

{relatedUseCases.length > 0 && (
  <div className="bg-white rounded-lg border border-gov-slate-200 p-6 mt-6">
    <h2 className="text-xl font-semibold mb-4">Federal Use Cases</h2>
    <p className="text-sm text-gov-slate-600 mb-4">
      Federal agencies using or potentially using this service for:
    </p>

    <div className="space-y-2">
      {relatedUseCases.map(({ useCase, match }) => (
        <div key={useCase.id} className="border-l-4 border-gov-navy-600 pl-4 py-2">
          <Link
            href={`/use-cases/${useCase.slug}`}
            className="font-semibold text-gov-navy-600 hover:underline"
          >
            {useCase.useCaseName}
          </Link>
          <p className="text-sm text-gov-slate-600">{useCase.agency}</p>
        </div>
      ))}
    </div>
  </div>
)}
```

---

### Phase 6: Testing

Run these commands to test everything:

```bash
# 1. Test the frontend
cd frontend
pnpm dev

# Visit these URLs:
# - http://localhost:3002/use-cases (should show 2,049 use cases with filters)
# - Click on a use case detail page (should show FedRAMP matches if any)
# - http://localhost:3002/products (should show products)
# - Click on a product with AI (should show related use cases if any)

# 2. Verify database counts
cd packages/database
npx tsx verify-import.ts

# 3. Check matches
npx tsx -e "
import { neon } from '@neondatabase/serverless';
import * as dotenv from 'dotenv';
dotenv.config({ path: '../../frontend/.env.local' });
const sql = neon(process.env.DATABASE_URL);
const matches = await sql\`SELECT confidence, COUNT(*) FROM use_case_fedramp_matches GROUP BY confidence\`;
console.log(matches);
"
```

---

### Phase 7: Build and Deploy

```bash
# Build the database package
cd packages/database
pnpm build

# Build the frontend
cd ../../frontend
pnpm build

# If successful, ready to deploy to Vercel!
```

---

## 📋 Quick Command Reference

```bash
# Run matching (from packages/database)
npx tsx match-use-cases-to-fedramp.ts

# Verify data
npx tsx verify-import.ts

# Start dev server
cd frontend && pnpm dev

# Build everything
cd packages/database && pnpm build
cd ../../frontend && pnpm build
```

---

## 🎯 Expected Outcomes

- ✅ 2,049 use cases loaded and browsable
- ✅ Intelligent matching between use cases and FedRAMP services
- ✅ Advanced filtering on use cases page (domain, agency, stage, AI type)
- ✅ Search functionality across use cases
- ✅ FedRAMP service recommendations on use case detail pages
- ✅ Related use cases shown on FedRAMP product pages
- ✅ Full cross-linking between all data types

---

## 📝 Notes

- The matching system uses 3 confidence levels:
  - **High**: Direct provider/product name matches
  - **Medium**: AI capability matches (GenAI, LLM)
  - **Low**: Compatible capabilities (chatbot + GenAI)

- Some use cases may have no matches if they don't use commercial AI products
- The 84 duplicate slugs during import are expected (same agency + similar names)
- Performance is optimized with database indexes already defined in schema

---

## 🐛 Troubleshooting

If use cases page is empty:
```bash
# Check database connection
npx tsx -e "import { db } from './src/db-connection'; console.log('Connected');"

# Check record count
npx tsx verify-import.ts
```

If matches aren't showing:
```bash
# Run the matching script
npx tsx match-use-cases-to-fedramp.ts

# Verify matches were created
npx tsx -e "/* check matches query */"
```

If frontend won't build:
```bash
# Rebuild database package first
cd packages/database && pnpm build

# Then try frontend
cd ../../frontend && pnpm build
```
