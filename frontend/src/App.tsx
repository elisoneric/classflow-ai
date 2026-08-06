import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import LoginPage from './features/auth/LoginPage';
import DashboardPage from './features/dashboard/DashboardPage';

import CoursesPage from './features/courses/CoursesPage';
import LecturersPage from './features/lecturers/LecturersPage';
import TimetablePage from './features/timetable/TimetablePage';

const ProtectedRoute = ({ children }: { children: React.ReactNode }) => {
    const token = localStorage.getItem('token');
    if (!token) {
        return <Navigate to="/login" replace />;
    }
    return <>{children}</>;
};

function App() {
    return (
        <Router>
            <Routes>
                <Route path="/login" element={<LoginPage />} />
                <Route path="/" element={<ProtectedRoute><DashboardPage /></ProtectedRoute>} />
                <Route path="/courses" element={<ProtectedRoute><CoursesPage /></ProtectedRoute>} />
                <Route path="/lecturers" element={<ProtectedRoute><LecturersPage /></ProtectedRoute>} />
                <Route path="/timetable" element={<ProtectedRoute><TimetablePage /></ProtectedRoute>} />
            </Routes>
        </Router>
    );
}

export default App;
