import { createBrowserRouter, Navigate } from 'react-router-dom';
import { AppLayout } from '@/components/layout/AppLayout';

// Features (Placeholders for now)
import Dashboard from '@/features/dashboard/Dashboard';
import Assistant from '@/features/assistant/Assistant';
import Knowledge from '@/features/knowledge/Knowledge';
import Vision from '@/features/vision/Vision';
import Coding from '@/features/coding/Coding';
import Security from '@/features/security/Security';
import Audit from '@/features/audit/Audit';

export const router = createBrowserRouter([
  {
    path: '/',
    element: <AppLayout />,
    children: [
      { index: true, element: <Navigate to="/dashboard" replace /> },
      { path: 'dashboard', element: <Dashboard /> },
      { path: 'assistant', element: <Assistant /> },
      { path: 'knowledge', element: <Knowledge /> },
      { path: 'vision', element: <Vision /> },
      { path: 'coding', element: <Coding /> },
      { path: 'security', element: <Security /> },
      { path: 'audit', element: <Audit /> },
    ],
  },
]);
