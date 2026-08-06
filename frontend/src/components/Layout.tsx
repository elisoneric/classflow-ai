import { useNavigate, useLocation, Link } from 'react-router-dom';
import { Calendar, Users, BookOpen, LogOut, LayoutDashboard } from 'lucide-react';

export default function Layout({ children }: { children: React.ReactNode }) {
    const navigate = useNavigate();
    const location = useLocation();

    const handleLogout = () => {
        localStorage.removeItem('token');
        navigate('/login');
    };

    const navItems = [
        { path: '/', label: 'Dashboard', icon: <LayoutDashboard size={20} /> },
        { path: '/courses', label: 'Courses', icon: <BookOpen size={20} /> },
        { path: '/lecturers', label: 'Lecturers', icon: <Users size={20} /> },
        { path: '/timetable', label: 'Timetable', icon: <Calendar size={20} /> },
    ];

    return (
        <div className="flex h-screen bg-slate-50">
            {/* Sidebar */}
            <aside className="w-64 bg-white border-r border-slate-200 flex flex-col">
                <div className="p-6 border-b border-slate-200">
                    <h2 className="text-2xl font-bold text-primary-600 font-heading">ClassFlow AI</h2>
                </div>
                <nav className="flex-1 p-4 space-y-2">
                    {navItems.map((item) => {
                        const isActive = location.pathname === item.path;
                        return (
                            <Link
                                key={item.path}
                                to={item.path}
                                className={`flex items-center gap-3 px-4 py-3 rounded-lg font-medium transition-colors ${
                                    isActive 
                                        ? 'bg-primary-50 text-primary-600' 
                                        : 'text-slate-600 hover:bg-slate-50'
                                }`}
                            >
                                {item.icon} {item.label}
                            </Link>
                        );
                    })}
                </nav>
                <div className="p-4 border-t border-slate-200">
                    <button 
                        onClick={handleLogout}
                        className="flex items-center gap-3 px-4 py-3 w-full text-slate-600 hover:bg-red-50 hover:text-red-600 rounded-lg font-medium transition-colors cursor-pointer"
                    >
                        <LogOut size={20} /> Logout
                    </button>
                </div>
            </aside>

            {/* Main Content */}
            <main className="flex-1 overflow-y-auto p-8">
                {children}
            </main>
        </div>
    );
}
