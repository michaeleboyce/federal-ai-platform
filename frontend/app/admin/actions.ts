'use server';

import { revalidatePath } from 'next/cache';
import {
  verifyAdminPassword,
  setAdminSession,
  clearAdminSession,
  checkAdminSession,
} from '@/lib/admin-auth';
import {
  getProfilesWithTools,
  getToolStats,
  createProfile,
  updateProfile,
  deleteProfile,
  createTool,
  updateTool,
  deleteTool,
  type AgencyProfileWithTools,
  type ToolStats,
} from '@/lib/agency-tools-db';
import type { ProductType } from '@/lib/db/schema';

// ========================================
// AUTH ACTIONS
// ========================================

export async function loginAction(
  password: string
): Promise<{ success: boolean; error?: string }> {
  const isValid = await verifyAdminPassword(password);

  if (isValid) {
    await setAdminSession();
    return { success: true };
  }

  return { success: false, error: 'Invalid password' };
}

export async function logoutAction(): Promise<void> {
  await clearAdminSession();
}

export async function isAuthenticatedAction(): Promise<boolean> {
  return await checkAdminSession();
}

// ========================================
// DATA FETCHING ACTIONS
// ========================================

export async function getProfilesAction(): Promise<AgencyProfileWithTools[]> {
  const isAuth = await checkAdminSession();
  if (!isAuth) {
    throw new Error('Unauthorized');
  }
  return await getProfilesWithTools();
}

export async function getStatsAction(): Promise<ToolStats> {
  const isAuth = await checkAdminSession();
  if (!isAuth) {
    throw new Error('Unauthorized');
  }
  return await getToolStats();
}

// ========================================
// PROFILE CRUD ACTIONS
// ========================================

export async function createProfileAction(data: {
  agencyName: string;
  abbreviation?: string;
  slug: string;
  departmentLevelName?: string;
  parentAbbreviation?: string;
  deploymentStatus?: 'all_staff' | 'pilot_or_limited' | 'no_public_internal_assistant';
}): Promise<{ success: boolean; error?: string }> {
  const isAuth = await checkAdminSession();
  if (!isAuth) {
    return { success: false, error: 'Unauthorized' };
  }

  try {
    await createProfile(data);
    revalidatePath('/admin');
    revalidatePath('/agency-ai-usage');
    return { success: true };
  } catch (error) {
    console.error('Error creating profile:', error);
    return { success: false, error: 'Failed to create profile' };
  }
}

export async function updateProfileAction(
  id: number,
  data: Partial<{
    agencyName: string;
    abbreviation: string | null;
    departmentLevelName: string | null;
    parentAbbreviation: string | null;
    deploymentStatus: 'all_staff' | 'pilot_or_limited' | 'no_public_internal_assistant';
  }>
): Promise<{ success: boolean; error?: string }> {
  const isAuth = await checkAdminSession();
  if (!isAuth) {
    return { success: false, error: 'Unauthorized' };
  }

  try {
    await updateProfile(id, data);
    revalidatePath('/admin');
    revalidatePath('/agency-ai-usage');
    return { success: true };
  } catch (error) {
    console.error('Error updating profile:', error);
    return { success: false, error: 'Failed to update profile' };
  }
}

export async function deleteProfileAction(
  id: number
): Promise<{ success: boolean; error?: string }> {
  const isAuth = await checkAdminSession();
  if (!isAuth) {
    return { success: false, error: 'Unauthorized' };
  }

  try {
    await deleteProfile(id);
    revalidatePath('/admin');
    revalidatePath('/agency-ai-usage');
    return { success: true };
  } catch (error) {
    console.error('Error deleting profile:', error);
    return { success: false, error: 'Failed to delete profile' };
  }
}

// ========================================
// TOOL CRUD ACTIONS
// ========================================

export async function createToolAction(data: {
  agencyProfileId: number;
  productName: string;
  productType: ProductType;
  slug: string;
  availableToAllStaff?: string;
  isPilotOrLimited?: boolean;
  codingAssistantFlag?: string;
  internalOrSensitiveData?: string;
  citationChicago?: string;
  citationAccessedDate?: string;
  citationUrl?: string;
}): Promise<{ success: boolean; error?: string }> {
  const isAuth = await checkAdminSession();
  if (!isAuth) {
    return { success: false, error: 'Unauthorized' };
  }

  try {
    await createTool(data);
    revalidatePath('/admin');
    revalidatePath('/agency-ai-usage');
    return { success: true };
  } catch (error) {
    console.error('Error creating tool:', error);
    return { success: false, error: 'Failed to create tool' };
  }
}

export async function updateToolAction(
  id: number,
  data: Partial<{
    productName: string;
    productType: ProductType;
    availableToAllStaff: string | null;
    isPilotOrLimited: boolean;
    codingAssistantFlag: string | null;
    internalOrSensitiveData: string | null;
    citationChicago: string | null;
    citationAccessedDate: string | null;
    citationUrl: string | null;
  }>
): Promise<{ success: boolean; error?: string }> {
  const isAuth = await checkAdminSession();
  if (!isAuth) {
    return { success: false, error: 'Unauthorized' };
  }

  try {
    await updateTool(id, data);
    revalidatePath('/admin');
    revalidatePath('/agency-ai-usage');
    return { success: true };
  } catch (error) {
    console.error('Error updating tool:', error);
    return { success: false, error: 'Failed to update tool' };
  }
}

export async function deleteToolAction(
  id: number
): Promise<{ success: boolean; error?: string }> {
  const isAuth = await checkAdminSession();
  if (!isAuth) {
    return { success: false, error: 'Unauthorized' };
  }

  try {
    await deleteTool(id);
    revalidatePath('/admin');
    revalidatePath('/agency-ai-usage');
    return { success: true };
  } catch (error) {
    console.error('Error deleting tool:', error);
    return { success: false, error: 'Failed to delete tool' };
  }
}
