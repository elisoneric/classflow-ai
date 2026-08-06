import { useQuery } from '@tanstack/react-query';
import api from '../../lib/api';
import Layout from '../../components/Layout';
import { Plus } from 'lucide-react';

interface Timetable {
    id: number;
    day_of_week: number;
    start_time: string;
    end_time: string;
    venue: string;
    course?: {
        code: string;
        name: string;
    };
}

export default function TimetablePage() {
    const { data: timetables, isLoading } = useQuery<Timetable[]>({
        queryKey: ['timetables'],
        queryFn: async () => {
            const res = await api.get('/timetables');
            return res.data;
        },
    });

    const getDayName = (day: number) => {
        const days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];
        return days[day];
    };

    return (
        <Layout>
            <header className="mb-8 flex justify-between items-center">
                <div>
                    <h1 className="text-3xl font-bold text-slate-900 font-heading">Timetable</h1>
                    <p className="text-slate-500 mt-1">Weekly schedule of all courses</p>
                </div>
                <button className="bg-primary-600 text-white px-4 py-2 rounded-lg font-medium flex items-center gap-2 hover:bg-primary-700 transition-colors">
                    <Plus size={20} /> Schedule Class
                </button>
            </header>

            <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
                <table className="w-full text-left">
                    <thead className="bg-slate-50 border-b border-slate-200 text-slate-500 font-medium">
                        <tr>
                            <th className="px-6 py-4">Day</th>
                            <th className="px-6 py-4">Time</th>
                            <th className="px-6 py-4">Course</th>
                            <th className="px-6 py-4">Venue</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100">
                        {isLoading ? (
                            <tr>
                                <td colSpan={4} className="px-6 py-8 text-center text-slate-500">Loading timetable...</td>
                            </tr>
                        ) : timetables?.length === 0 ? (
                            <tr>
                                <td colSpan={4} className="px-6 py-8 text-center text-slate-500">No classes scheduled. Click 'Schedule Class' to add one.</td>
                            </tr>
                        ) : (
                            timetables?.sort((a, b) => a.day_of_week - b.day_of_week).map((schedule) => (
                                <tr key={schedule.id} className="hover:bg-slate-50/50 transition-colors">
                                    <td className="px-6 py-4 font-bold text-slate-900">{getDayName(schedule.day_of_week)}</td>
                                    <td className="px-6 py-4 text-slate-600">{schedule.start_time} - {schedule.end_time}</td>
                                    <td className="px-6 py-4 text-slate-900 font-medium">{schedule.course?.code} <span className="text-slate-500 font-normal">({schedule.course?.name})</span></td>
                                    <td className="px-6 py-4 text-slate-600">{schedule.venue}</td>
                                </tr>
                            ))
                        )}
                    </tbody>
                </table>
            </div>
        </Layout>
    );
}
