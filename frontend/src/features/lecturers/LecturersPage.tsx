import { useQuery } from '@tanstack/react-query';
import api from '../../lib/api';
import Layout from '../../components/Layout';
import { Plus } from 'lucide-react';

interface Lecturer {
    id: number;
    name: string;
    email: string;
    phone?: string;
    preferred_contact: string;
}

export default function LecturersPage() {
    const { data: lecturers, isLoading } = useQuery<Lecturer[]>({
        queryKey: ['lecturers'],
        queryFn: async () => {
            const res = await api.get('/lecturers');
            return res.data;
        },
    });

    return (
        <Layout>
            <header className="mb-8 flex justify-between items-center">
                <div>
                    <h1 className="text-3xl font-bold text-slate-900 font-heading">Lecturers</h1>
                    <p className="text-slate-500 mt-1">Manage teaching staff and contact info</p>
                </div>
                <button className="bg-primary-600 text-white px-4 py-2 rounded-lg font-medium flex items-center gap-2 hover:bg-primary-700 transition-colors">
                    <Plus size={20} /> Add Lecturer
                </button>
            </header>

            <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
                <table className="w-full text-left">
                    <thead className="bg-slate-50 border-b border-slate-200 text-slate-500 font-medium">
                        <tr>
                            <th className="px-6 py-4">Name</th>
                            <th className="px-6 py-4">Email</th>
                            <th className="px-6 py-4">Phone</th>
                            <th className="px-6 py-4">Preferred Contact</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100">
                        {isLoading ? (
                            <tr>
                                <td colSpan={4} className="px-6 py-8 text-center text-slate-500">Loading lecturers...</td>
                            </tr>
                        ) : lecturers?.length === 0 ? (
                            <tr>
                                <td colSpan={4} className="px-6 py-8 text-center text-slate-500">No lecturers found. Click 'Add Lecturer' to create one.</td>
                            </tr>
                        ) : (
                            lecturers?.map((lecturer) => (
                                <tr key={lecturer.id} className="hover:bg-slate-50/50 transition-colors">
                                    <td className="px-6 py-4 font-bold text-slate-900">{lecturer.name}</td>
                                    <td className="px-6 py-4 text-slate-600">{lecturer.email}</td>
                                    <td className="px-6 py-4 text-slate-600">{lecturer.phone || 'N/A'}</td>
                                    <td className="px-6 py-4">
                                        <span className="px-3 py-1 bg-slate-100 text-slate-700 rounded-full text-sm font-semibold">
                                            {lecturer.preferred_contact}
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
