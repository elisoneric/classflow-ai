import { useQuery } from '@tanstack/react-query';
import api from '../../lib/api';
import Layout from '../../components/Layout';

interface DashboardStats {
    total_courses: number;
    todays_classes: number;
    announcements_sent: number;
}

interface ClassSession {
    id: number;
    date: string;
    status: string;
    actual_time?: string;
    actual_venue?: string;
    timetable: {
        id: number;
        start_time: string;
        end_time: string;
        venue: string;
        course: {
            code: string;
            name: string;
        };
    };
}

export default function DashboardPage() {
    const { data: stats, isLoading: isLoadingStats } = useQuery<DashboardStats>({
        queryKey: ['dashboard-stats'],
        queryFn: async () => {
            const res = await api.get('/sessions/stats');
            return res.data;
        },
    });

    const { data: sessions, isLoading: isLoadingSessions } = useQuery<ClassSession[]>({
        queryKey: ['todays-sessions'],
        queryFn: async () => {
            const res = await api.get('/sessions/today');
            return res.data;
        },
    });

    const getStatusColor = (status: string) => {
        switch (status) {
            case 'CONFIRMED': return 'bg-emerald-100 text-emerald-700 border-emerald-200';
            case 'CANCELLED': return 'bg-red-100 text-red-700 border-red-200';
            case 'DELAYED': return 'bg-amber-100 text-amber-700 border-amber-200';
            default: return 'bg-slate-100 text-slate-700 border-slate-200';
        }
    };

    const getStatusIndicatorColor = (status: string) => {
        switch (status) {
            case 'CONFIRMED': return 'bg-emerald-500';
            case 'CANCELLED': return 'bg-red-500';
            case 'DELAYED': return 'bg-amber-500';
            default: return 'bg-slate-500';
        }
    };

    return (
        <Layout>
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
                    <p className="text-3xl font-bold text-slate-900">
                        {isLoadingStats ? '...' : stats?.total_courses || 0}
                    </p>
                </div>
                <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm">
                    <h3 className="text-slate-500 font-medium mb-1">Today's Classes</h3>
                    <p className="text-3xl font-bold text-primary-600">
                        {isLoadingStats ? '...' : stats?.todays_classes || 0}
                    </p>
                </div>
                <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm">
                    <h3 className="text-slate-500 font-medium mb-1">Announcements Sent</h3>
                    <p className="text-3xl font-bold text-emerald-600">
                        {isLoadingStats ? '...' : stats?.announcements_sent || 0}
                    </p>
                </div>
            </div>

            {/* Timeline / Classes */}
            <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6">
                <h2 className="text-xl font-bold text-slate-900 mb-4 font-heading">Today's Sessions</h2>
                
                <div className="space-y-4">
                    {isLoadingSessions ? (
                        <p className="text-slate-500">Loading sessions...</p>
                    ) : sessions?.length === 0 ? (
                        <p className="text-slate-500 text-center py-8">No classes scheduled for today.</p>
                    ) : (
                        sessions?.map((session) => (
                            <div key={session.id} className="flex items-center justify-between p-4 border border-slate-100 rounded-xl bg-slate-50/50">
                                <div className="flex items-center gap-4">
                                    <div className={`w-2 h-12 rounded-full ${getStatusIndicatorColor(session.status)}`}></div>
                                    <div>
                                        <h4 className="font-bold text-slate-900 text-lg">{session.timetable.course.code}</h4>
                                        <p className="text-slate-500 text-sm">
                                            {session.timetable.course.name} • {session.actual_time || `${session.timetable.start_time} - ${session.timetable.end_time}`} • {session.actual_venue || session.timetable.venue}
                                        </p>
                                    </div>
                                </div>
                                <div className="flex items-center gap-4">
                                    <span className={`px-3 py-1 rounded-full text-sm font-semibold border ${getStatusColor(session.status)}`}>
                                        {session.status}
                                    </span>
                                </div>
                            </div>
                        ))
                    )}
                </div>
            </div>
        </Layout>
    );
}
