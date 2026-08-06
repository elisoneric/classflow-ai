import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '../../lib/api';
import Layout from '../../components/Layout';
import { Plus, X } from 'lucide-react';

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

interface Course {
    id: number;
    code: string;
    name: string;
}

export default function TimetablePage() {
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [formData, setFormData] = useState({ 
        course_id: '', 
        day_of_week: '0', 
        start_time: '', 
        end_time: '', 
        venue: '' 
    });
    const queryClient = useQueryClient();

    const { data: timetables, isLoading } = useQuery<Timetable[]>({
        queryKey: ['timetables'],
        queryFn: async () => {
            const res = await api.get('/timetables');
            return res.data;
        },
    });

    const { data: courses } = useQuery<Course[]>({
        queryKey: ['courses'],
        queryFn: async () => {
            const res = await api.get('/courses');
            return res.data;
        },
    });

    const addTimetableMutation = useMutation({
        mutationFn: async (newSchedule: any) => {
            const payload = { 
                ...newSchedule, 
                course_id: parseInt(newSchedule.course_id),
                day_of_week: parseInt(newSchedule.day_of_week)
            };
            // The backend expects `time` objects which can parse from HH:MM strings.
            // But they might require seconds depending on the backend validation. Let's append :00 if missing.
            if (payload.start_time.length === 5) payload.start_time += ':00';
            if (payload.end_time.length === 5) payload.end_time += ':00';

            const res = await api.post('/timetables', payload);
            return res.data;
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['timetables'] });
            setIsModalOpen(false);
            setFormData({ course_id: '', day_of_week: '0', start_time: '', end_time: '', venue: '' });
        },
    });

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        addTimetableMutation.mutate(formData);
    };

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
                <button 
                    onClick={() => setIsModalOpen(true)}
                    className="bg-primary-600 text-white px-4 py-2 rounded-lg font-medium flex items-center gap-2 hover:bg-primary-700 transition-colors cursor-pointer"
                >
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

            {/* Schedule Class Modal */}
            {isModalOpen && (
                <div className="fixed inset-0 bg-slate-900/50 flex items-center justify-center p-4 z-50">
                    <div className="bg-white rounded-2xl shadow-xl w-full max-w-md overflow-hidden">
                        <div className="flex justify-between items-center p-6 border-b border-slate-100">
                            <h2 className="text-xl font-bold font-heading">Schedule New Class</h2>
                            <button onClick={() => setIsModalOpen(false)} className="text-slate-400 hover:text-slate-600 cursor-pointer">
                                <X size={24} />
                            </button>
                        </div>
                        <form onSubmit={handleSubmit} className="p-6 space-y-4">
                            <div>
                                <label className="block text-sm font-medium text-slate-700 mb-1">Select Course</label>
                                <select 
                                    required
                                    className="w-full px-4 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 bg-white"
                                    value={formData.course_id}
                                    onChange={(e) => setFormData({...formData, course_id: e.target.value})}
                                >
                                    <option value="" disabled>-- Select a Course --</option>
                                    {courses?.map(c => (
                                        <option key={c.id} value={c.id}>{c.code} - {c.name}</option>
                                    ))}
                                </select>
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-slate-700 mb-1">Day of Week</label>
                                <select 
                                    required
                                    className="w-full px-4 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 bg-white"
                                    value={formData.day_of_week}
                                    onChange={(e) => setFormData({...formData, day_of_week: e.target.value})}
                                >
                                    <option value="0">Monday</option>
                                    <option value="1">Tuesday</option>
                                    <option value="2">Wednesday</option>
                                    <option value="3">Thursday</option>
                                    <option value="4">Friday</option>
                                    <option value="5">Saturday</option>
                                    <option value="6">Sunday</option>
                                </select>
                            </div>
                            <div className="grid grid-cols-2 gap-4">
                                <div>
                                    <label className="block text-sm font-medium text-slate-700 mb-1">Start Time</label>
                                    <input 
                                        required
                                        type="time" 
                                        className="w-full px-4 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                                        value={formData.start_time}
                                        onChange={(e) => setFormData({...formData, start_time: e.target.value})}
                                    />
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-slate-700 mb-1">End Time</label>
                                    <input 
                                        required
                                        type="time" 
                                        className="w-full px-4 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                                        value={formData.end_time}
                                        onChange={(e) => setFormData({...formData, end_time: e.target.value})}
                                    />
                                </div>
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-slate-700 mb-1">Venue</label>
                                <input 
                                    required
                                    type="text" 
                                    placeholder="e.g. Lecture Theater 1"
                                    className="w-full px-4 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                                    value={formData.venue}
                                    onChange={(e) => setFormData({...formData, venue: e.target.value})}
                                />
                            </div>
                            <div className="pt-4 flex justify-end gap-3">
                                <button 
                                    type="button" 
                                    onClick={() => setIsModalOpen(false)}
                                    className="px-4 py-2 text-slate-600 font-medium hover:bg-slate-50 rounded-lg transition-colors cursor-pointer"
                                >
                                    Cancel
                                </button>
                                <button 
                                    type="submit" 
                                    disabled={addTimetableMutation.isPending}
                                    className="px-4 py-2 bg-primary-600 text-white font-medium rounded-lg hover:bg-primary-700 transition-colors cursor-pointer disabled:opacity-50"
                                >
                                    {addTimetableMutation.isPending ? 'Saving...' : 'Save Schedule'}
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}
        </Layout>
    );
}
