import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '../../lib/api';
import Layout from '../../components/Layout';
import { Plus, X } from 'lucide-react';

interface Course {
    id: number;
    code: string;
    name: string;
    status: string;
    lecturer?: {
        name: string;
    };
}

interface Lecturer {
    id: number;
    name: string;
}

export default function CoursesPage() {
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [formData, setFormData] = useState({ code: '', name: '', lecturer_id: '' });
    const queryClient = useQueryClient();

    const { data: courses, isLoading } = useQuery<Course[]>({
        queryKey: ['courses'],
        queryFn: async () => {
            const res = await api.get('/courses');
            return res.data;
        },
    });

    const { data: lecturers } = useQuery<Lecturer[]>({
        queryKey: ['lecturers'],
        queryFn: async () => {
            const res = await api.get('/lecturers');
            return res.data;
        },
    });

    const addCourseMutation = useMutation({
        mutationFn: async (newCourse: any) => {
            const payload = { ...newCourse };
            if (payload.lecturer_id === "") {
                payload.lecturer_id = null;
            } else {
                payload.lecturer_id = parseInt(payload.lecturer_id);
            }
            const res = await api.post('/courses', payload);
            return res.data;
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['courses'] });
            setIsModalOpen(false);
            setFormData({ code: '', name: '', lecturer_id: '' });
        },
    });

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        addCourseMutation.mutate(formData);
    };

    return (
        <Layout>
            <header className="mb-8 flex justify-between items-center">
                <div>
                    <h1 className="text-3xl font-bold text-slate-900 font-heading">Courses</h1>
                    <p className="text-slate-500 mt-1">Manage all university courses</p>
                </div>
                <button 
                    onClick={() => setIsModalOpen(true)}
                    className="bg-primary-600 text-white px-4 py-2 rounded-lg font-medium flex items-center gap-2 hover:bg-primary-700 transition-colors cursor-pointer"
                >
                    <Plus size={20} /> Add Course
                </button>
            </header>

            <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
                <table className="w-full text-left">
                    <thead className="bg-slate-50 border-b border-slate-200 text-slate-500 font-medium">
                        <tr>
                            <th className="px-6 py-4">Course Code</th>
                            <th className="px-6 py-4">Course Name</th>
                            <th className="px-6 py-4">Lecturer</th>
                            <th className="px-6 py-4">Status</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100">
                        {isLoading ? (
                            <tr>
                                <td colSpan={4} className="px-6 py-8 text-center text-slate-500">Loading courses...</td>
                            </tr>
                        ) : courses?.length === 0 ? (
                            <tr>
                                <td colSpan={4} className="px-6 py-8 text-center text-slate-500">No courses found. Click 'Add Course' to create one.</td>
                            </tr>
                        ) : (
                            courses?.map((course) => (
                                <tr key={course.id} className="hover:bg-slate-50/50 transition-colors">
                                    <td className="px-6 py-4 font-bold text-slate-900">{course.code}</td>
                                    <td className="px-6 py-4 text-slate-600">{course.name}</td>
                                    <td className="px-6 py-4 text-slate-600">{course.lecturer?.name || 'Unassigned'}</td>
                                    <td className="px-6 py-4">
                                        <span className="px-3 py-1 bg-slate-100 text-slate-700 rounded-full text-sm font-semibold">
                                            {course.status}
                                        </span>
                                    </td>
                                </tr>
                            ))
                        )}
                    </tbody>
                </table>
            </div>

            {/* Add Course Modal */}
            {isModalOpen && (
                <div className="fixed inset-0 bg-slate-900/50 flex items-center justify-center p-4 z-50">
                    <div className="bg-white rounded-2xl shadow-xl w-full max-w-md overflow-hidden">
                        <div className="flex justify-between items-center p-6 border-b border-slate-100">
                            <h2 className="text-xl font-bold font-heading">Add New Course</h2>
                            <button onClick={() => setIsModalOpen(false)} className="text-slate-400 hover:text-slate-600 cursor-pointer">
                                <X size={24} />
                            </button>
                        </div>
                        <form onSubmit={handleSubmit} className="p-6 space-y-4">
                            <div>
                                <label className="block text-sm font-medium text-slate-700 mb-1">Course Code</label>
                                <input 
                                    required
                                    type="text" 
                                    placeholder="e.g. CSC 801"
                                    className="w-full px-4 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                                    value={formData.code}
                                    onChange={(e) => setFormData({...formData, code: e.target.value})}
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-slate-700 mb-1">Course Name</label>
                                <input 
                                    required
                                    type="text" 
                                    placeholder="e.g. Advanced Databases"
                                    className="w-full px-4 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                                    value={formData.name}
                                    onChange={(e) => setFormData({...formData, name: e.target.value})}
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-slate-700 mb-1">Assign Lecturer (Optional)</label>
                                <select 
                                    className="w-full px-4 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 bg-white"
                                    value={formData.lecturer_id}
                                    onChange={(e) => setFormData({...formData, lecturer_id: e.target.value})}
                                >
                                    <option value="">-- Unassigned --</option>
                                    {lecturers?.map(l => (
                                        <option key={l.id} value={l.id}>{l.name}</option>
                                    ))}
                                </select>
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
                                    disabled={addCourseMutation.isPending}
                                    className="px-4 py-2 bg-primary-600 text-white font-medium rounded-lg hover:bg-primary-700 transition-colors cursor-pointer disabled:opacity-50"
                                >
                                    {addCourseMutation.isPending ? 'Saving...' : 'Save Course'}
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}
        </Layout>
    );
}
