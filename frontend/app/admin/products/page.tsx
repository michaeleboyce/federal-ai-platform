import { checkAdminSession } from '@/lib/admin-auth';
import { getAllProductsWithAnalysis, getProductStats } from '@/lib/products-admin-db';
import AdminLoginForm from '../AdminLoginForm';
import ProductsAdminPanel from './ProductsAdminPanel';

export const dynamic = 'force-dynamic';

export default async function ProductsAdminPage() {
  const isAuthenticated = await checkAdminSession();

  if (!isAuthenticated) {
    return <AdminLoginForm />;
  }

  const [products, stats] = await Promise.all([
    getAllProductsWithAnalysis(),
    getProductStats(),
  ]);

  return (
    <ProductsAdminPanel
      initialProducts={products}
      initialStats={stats}
    />
  );
}
