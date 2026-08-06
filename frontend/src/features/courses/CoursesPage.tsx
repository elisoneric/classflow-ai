import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import api from '../../lib/api';
import Layout from '../../components/Layout';
import { Plus } from 'lucide-react';

interface Course {
    id: number;
    code: string;
    name: string;
    status: string;
    lecturer?: {
        name: string;
    };
}

export default function CoursesPage() {
    const { data: courses, isLoading } = useQuery<Course[]>({
        queryKey: ['courses'],
        queryFn: async () => {
            const res = await api.get('/courses');
            return res.data;
        },
    });

    return (
        <Layout>
            <header className="mb-8 flex justify-between items-center">
                <div>
                    <h1 className="text-3xl font-bold text-slate-900 font-heading">Courses</h1>
                    <p className="text-slate-500 mt-1">Manage all university courses</p>
                </div>
                <button className="bg-primary-600 text-white px-4 py-2 rounded-lg font-medium flex items-center gap-2 hover:bg-primary-700 transition-colors">
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
        </Layout>
    );
}
