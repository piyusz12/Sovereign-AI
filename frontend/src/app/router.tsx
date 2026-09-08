/**
 * Sovereign Command Deck — Router
 *
 * Simplified routing: The three-panel layout IS the app.
 * The center panel switches content based on appStore.ui.activeView.
 */

import { createBrowserRouter } from 'react-router-dom';
import { AppLayout } from '@/components/layout/AppLayout';

export const router = createBrowserRouter([
  {
    path: '/',
    element: <AppLayout />,
  },
  {
    path: '*',
    element: <AppLayout />,
  },
]);
