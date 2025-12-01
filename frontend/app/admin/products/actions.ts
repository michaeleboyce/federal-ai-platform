'use server';

import { revalidatePath } from 'next/cache';
import { checkAdminSession } from '@/lib/admin-auth';
import {
  getAllProductsWithAnalysis,
  getProductStats,
  updateProductAnalysis,
  getProductsByFilter,
  type ProductWithAnalysis,
  type ProductStats,
  type ProductFilter,
} from '@/lib/products-admin-db';

// ========================================
// DATA FETCHING ACTIONS
// ========================================

export async function getProductsAction(): Promise<ProductWithAnalysis[]> {
  const isAuth = await checkAdminSession();
  if (!isAuth) {
    throw new Error('Unauthorized');
  }
  return await getAllProductsWithAnalysis();
}

export async function getProductStatsAction(): Promise<ProductStats> {
  const isAuth = await checkAdminSession();
  if (!isAuth) {
    throw new Error('Unauthorized');
  }
  return await getProductStats();
}

export async function getFilteredProductsAction(
  filter: ProductFilter
): Promise<ProductWithAnalysis[]> {
  const isAuth = await checkAdminSession();
  if (!isAuth) {
    throw new Error('Unauthorized');
  }
  return await getProductsByFilter(filter);
}

// ========================================
// UPDATE ACTIONS
// ========================================

export async function updateProductAnalysisAction(
  id: number,
  data: Partial<{
    // Original AI flags
    hasAi: boolean;
    hasGenai: boolean;
    hasLlm: boolean;
    relevantExcerpt: string | null;
    // Expanded capabilities
    hasChatbot: boolean;
    hasCodingAssistant: boolean;
    hasImageGeneration: boolean;
    hasDocumentAnalysis: boolean;
    hasSpeechToText: boolean;
    hasTranslation: boolean;
    hasAiSearch: boolean;
    // Admin metadata
    adminNotes: string | null;
    customDescription: string | null;
  }>
): Promise<{ success: boolean; error?: string }> {
  const isAuth = await checkAdminSession();
  if (!isAuth) {
    return { success: false, error: 'Unauthorized' };
  }

  try {
    await updateProductAnalysis(id, data);
    revalidatePath('/admin/products');
    revalidatePath('/products');
    return { success: true };
  } catch (error) {
    console.error('Error updating product analysis:', error);
    return { success: false, error: 'Failed to update product analysis' };
  }
}
