import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Calendar, Users, BookOpen, LogOut, LayoutDashboard } from 'lucide-react';

export default function DashboardPage() {
    const navigate = useNavigate();

    const handleLogout = () => {
        localStorage.removeItem('token');
        navigate('/login');
    };

    return (
        <div className="flex h-screen bg-slate-50">
            {/* Sidebar */}
            <aside className="w-64 bg-white border-r border-slate-200 flex flex-col">
                <div className="p-6 border-b border-slate-200">
                    <h2 className="text-2xl font-bold text-primary-600 font-heading">ClassFlow AI</h2>
                </div>
                <nav className="flex-1 p-4 space-y-2">
                    <a href="#" className="flex items-center gap-3 px-4 py-3 bg-primary-50 text-primary-600 rounded-lg font-medium transition-colors">
                        <LayoutDashboard size={20} /> Dashboard
                    </a>
                    <a href="#" className="flex items-center gap-3 px-4 py-3 text-slate-600 hover:bg-slate-50 rounded-lg font-medium transition-colors">
                        <BookOpen size={20} /> Courses
                    </a>
                    <a href="#" className="flex items-center gap-3 px-4 py-3 text-slate-600 hover:bg-slate-50 rounded-lg font-medium transition-colors">
                        <Users size={20} /> Lecturers
                    </a>
                    <a href="#" className="flex items-center gap-3 px-4 py-3 text-slate-600 hover:bg-slate-50 rounded-lg font-medium transition-colors">
                        <Calendar size={20} /> Timetable
                    </a>
                </nav>
                <div className="p-4 border-t border-slate-200">
                    <button 
                        onClick={handleLogout}
                        className="flex items-center gap-3 px-4 py-3 w-full text-slate-600 hover:bg-red-50 hover:text-red-600 rounded-lg font-medium transition-colors"
                    >
                        <LogOut size={20} /> Logout
                    </button>
                </div>
            </aside>

            {/* Main Content */}
            <main className="flex-1 overflow-y-auto p-8">
                <header className="mb-8 flex justify-between items-center">
                    <div>
                        <h1 className="text-3xl font-bold text-slate-900 font-heading">Dashboard</h1>
                        <p className="text-slate-500 mt-1">Today's Class Schedule & Status</p>
                    </div>
                </header>

                {/* Dashboard Stats */}
                <div className="grid grid-cols-3 gap-6 mb-8">
                    <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm">
                        <h3 className="text-slate-500 font-medium mb-1">Total Courses</h3>
                        <p className="text-3xl font-bold text-slate-900">4</p>
                    </div>
                    <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm">
                        <h3 className="text-slate-500 font-medium mb-1">Today's Classes</h3>
                        <p className="text-3xl font-bold text-primary-600">2</p>
                    </div>
                    <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm">
                        <h3 className="text-slate-500 font-medium mb-1">Announcements Sent</h3>
                        <p className="text-3xl font-bold text-emerald-600">12</p>
                    </div>
                </div>

                {/* Timeline / Classes */}
                <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6">
                    <h2 className="text-xl font-bold text-slate-900 mb-4 font-heading">Today's Sessions</h2>
                    
                    <div className="space-y-4">
                        <div className="flex items-center justify-between p-4 border border-slate-100 rounded-xl bg-slate-50/50">
                            <div className="flex items-center gap-4">
                                <div className="w-2 h-12 bg-emerald-500 rounded-full"></div>
                                <div>
                                    <h4 className="font-bold text-slate-900 text-lg">CSC 803</h4>
                                    <p className="text-slate-500 text-sm">Prof. Smith • 10:00 AM - 12:00 PM • Lab 2</p>
                                </div>
                            </div>
                            <div className="flex items-center gap-4">
                                <span className="px-3 py-1 bg-emerald-100 text-emerald-700 rounded-full text-sm font-semibold">
                                    CONFIRMED
                                </span>
                            </div>
                        </div>

                        <div className="flex items-center justify-between p-4 border border-slate-100 rounded-xl bg-slate-50/50">
                            <div className="flex items-center gap-4">
                                <div className="w-2 h-12 bg-amber-500 rounded-full"></div>
                                <div>
                                    <h4 className="font-bold text-slate-900 text-lg">SEN 807</h4>
                                    <p className="text-slate-500 text-sm">Dr. Johnson • 2:00 PM - 4:00 PM • E125</p>
                                </div>
                            </div>
                            <div className="flex items-center gap-4">
                                <span className="px-3 py-1 bg-amber-100 text-amber-700 rounded-full text-sm font-semibold">
                                    WAITING
                                </span>
                            </div>
                        </div>
                    </div>
                </div>
            </main>
        </div>
    );
}
