import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '../../lib/api';
import Layout from '../../components/Layout';
import { Plus, X } from 'lucide-react';

interface Lecturer {
    id: number;
    name: string;
    email: string;
    phone?: string;
    preferred_contact: string;
}

export default function LecturersPage() {
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [formData, setFormData] = useState({ name: '', email: '', phone: '', preferred_contact: 'EMAIL' });
    const queryClient = useQueryClient();

    const { data: lecturers, isLoading } = useQuery<Lecturer[]>({
        queryKey: ['lecturers'],
        queryFn: async () => {
            const res = await api.get('/lecturers');
            return res.data;
        },
    });

    const addLecturerMutation = useMutation({
        mutationFn: async (newLecturer: any) => {
            const res = await api.post('/lecturers', newLecturer);
            return res.data;
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['lecturers'] });
            setIsModalOpen(false);
            setFormData({ name: '', email: '', phone: '', preferred_contact: 'EMAIL' });
        },
    });

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        addLecturerMutation.mutate(formData);
    };

    return (
        <Layout>
            <header className="mb-8 flex justify-between items-center">
                <div>
                    <h1 className="text-3xl font-bold text-slate-900 font-heading">Lecturers</h1>
                    <p className="text-slate-500 mt-1">Manage teaching staff and contact info</p>
                </div>
                <button 
                    onClick={() => setIsModalOpen(true)}
                    className="bg-primary-600 text-white px-4 py-2 rounded-lg font-medium flex items-center gap-2 hover:bg-primary-700 transition-colors cursor-pointer"
                >
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

            {/* Add Lecturer Modal */}
            {isModalOpen && (
                <div className="fixed inset-0 bg-slate-900/50 flex items-center justify-center p-4 z-50">
                    <div className="bg-white rounded-2xl shadow-xl w-full max-w-md overflow-hidden">
                        <div className="flex justify-between items-center p-6 border-b border-slate-100">
                            <h2 className="text-xl font-bold font-heading">Add New Lecturer</h2>
                            <button onClick={() => setIsModalOpen(false)} className="text-slate-400 hover:text-slate-600 cursor-pointer">
                                <X size={24} />
                            </button>
                        </div>
                        <form onSubmit={handleSubmit} className="p-6 space-y-4">
                            <div>
                                <label className="block text-sm font-medium text-slate-700 mb-1">Full Name</label>
                                <input 
                                    required
                                    type="text" 
                                    placeholder="e.g. Dr. Jane Smith"
                                    className="w-full px-4 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                                    value={formData.name}
                                    onChange={(e) => setFormData({...formData, name: e.target.value})}
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-slate-700 mb-1">Email Address</label>
                                <input 
                                    required
                                    type="email" 
                                    placeholder="e.g. jane.smith@university.edu"
                                    className="w-full px-4 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                                    value={formData.email}
                                    onChange={(e) => setFormData({...formData, email: e.target.value})}
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-slate-700 mb-1">Phone Number (Optional)</label>
                                <input 
                                    type="text" 
                                    placeholder="e.g. +1234567890"
                                    className="w-full px-4 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                                    value={formData.phone}
                                    onChange={(e) => setFormData({...formData, phone: e.target.value})}
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-slate-700 mb-1">Preferred Contact</label>
                                <select 
                                    className="w-full px-4 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 bg-white"
                                    value={formData.preferred_contact}
                                    onChange={(e) => setFormData({...formData, preferred_contact: e.target.value})}
                                >
                                    <option value="EMAIL">Email</option>
                                    <option value="WHATSAPP">WhatsApp</option>
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
                                    disabled={addLecturerMutation.isPending}
                                    className="px-4 py-2 bg-primary-600 text-white font-medium rounded-lg hover:bg-primary-700 transition-colors cursor-pointer disabled:opacity-50"
                                >
                                    {addLecturerMutation.isPending ? 'Saving...' : 'Save Lecturer'}
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}
        </Layout>
    );
}
