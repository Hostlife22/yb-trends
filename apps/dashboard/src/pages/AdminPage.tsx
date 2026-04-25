import AlertsList from '@/components/admin/AlertsList';
import HealthStatus from '@/components/admin/HealthStatus';
import SyncForm from '@/components/admin/SyncForm';
import SyncRunsTable from '@/components/admin/SyncRunsTable';

export default function AdminPage() {
  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-semibold text-gray-100">Admin</h1>
        <p className="mt-1 text-sm text-gray-500">
          System management and operational controls
        </p>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <HealthStatus />
        <SyncForm />
      </div>

      <AlertsList />
      <SyncRunsTable />
    </div>
  );
}
