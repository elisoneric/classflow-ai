import { createBrowserRouter } from "react-router-dom";
import { ProtectedRoute } from "@/components/ProtectedRoute";
import { Layout } from "@/components/Layout";
import { LoginPage } from "@/features/auth/LoginPage";
import { DashboardPage } from "@/features/dashboard/DashboardPage";
import { PendingReviewPage } from "@/features/dashboard/PendingReviewPage";
import { CoursesPage } from "@/features/courses/CoursesPage";
import { LecturersPage } from "@/features/lecturers/LecturersPage";
import { SessionHistoryPage } from "@/features/audit-log/SessionHistoryPage";
import { SettingsPage } from "@/features/settings/SettingsPage";

export const router = createBrowserRouter([
  { path: "/login", element: <LoginPage /> },
  {
    element: <ProtectedRoute />,
    children: [
      {
        element: <Layout />,
        children: [
          { path: "/", element: <DashboardPage /> },
          { path: "/pending-review", element: <PendingReviewPage /> },
          { path: "/courses", element: <CoursesPage /> },
          { path: "/lecturers", element: <LecturersPage /> },
          { path: "/sessions", element: <SessionHistoryPage /> },
          { path: "/settings", element: <SettingsPage /> },
        ],
      },
    ],
  },
]);
