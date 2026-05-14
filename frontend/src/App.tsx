import React, { useState, useEffect, useMemo } from 'react';
import { 
  LayoutDashboard, Users, Shield, Mail, 
  Activity, Search, Upload, Download, 
  CheckCircle, Clock, Lock, LogOut, User,
  FileText, Trash2, AlertCircle, ChevronRight
} from 'lucide-react';
import { BarChart, Bar, ResponsiveContainer, XAxis, YAxis, Tooltip, Cell } from 'recharts';
import axios from 'axios';

// --- INTERFACCE TYPESCRIPT ---
interface Candidate {
  id: number;
  name: string | null;
  email: string;
  phone: string | null;
  skills: string[];
  status: string;
  created_at: string;
}

interface DashboardStats {
  total_candidates: number;
  skills_bar: { name: string; count: number }[];
  status_pie: { name: string; value: number }[];
  status_distribution: Record<string, number>;
}

const API_BASE = "http://localhost:8000";

const App: React.FC = () => {
  // --- STATO ---
  const [token, setToken] = useState<string | null>(localStorage.getItem('flux_token'));
  const [view, setView] = useState('stats');
  const [candidates, setCandidates] = useState<Candidate[]>([]);
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [searchTerm, setSearchTerm] = useState("");
  const [loginData, setLoginData] = useState({ username: '', password: '' });
  const [loginError, setLoginError] = useState(false);

  // --- CONFIGURAZIONE API ---
  const api = useMemo(() => axios.create({
    baseURL: API_BASE,
    headers: token ? { Authorization: `Bearer ${token}` } : {}
  }), [token]);

  // --- FUNZIONI DI GESTIONE ---
  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoginError(false);
    try {
      const params = new URLSearchParams();
      params.append('username', loginData.username);
      params.append('password', loginData.password);

      const res = await axios.post(`${API_BASE}/token`, params);
      const newToken = res.data.access_token;
      localStorage.setItem('flux_token', newToken);
      setToken(newToken);
    } catch (err) {
      setLoginError(true);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('flux_token');
    setToken(null);
  };

  const fetchData = async () => {
    if (!token) return;
    try {
      const [candRes, statsRes] = await Promise.all([
        api.get('/candidates'),
        api.get('/stats')
      ]);
      setCandidates(candRes.data);
      setStats(statsRes.data);
    } catch (err: any) {
      if (err.response?.status === 401) handleLogout();
    }
  };

  const updateStatus = async (id: number, newStatus: string) => {
    try {
      await api.patch(`/candidates/${id}/status`, { status: newStatus });
      fetchData();
    } catch (err) {
      alert("Errore nell'aggiornamento dello stato.");
    }
  };

  const deleteCandidate = async (id: number) => {
    if (!window.confirm("Eliminare definitivamente il candidato e tutti i suoi dati (GDPR)?")) return;
    try {
      await api.delete(`/candidates/${id}`);
      fetchData();
    } catch (err) {
      alert("Errore durante l'eliminazione.");
    }
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 15000);
    return () => clearInterval(interval);
  }, [token, api]);

  // --- LOGICA FILTRO ---
  const filteredCandidates = candidates.filter(c => 
    c.name?.toLowerCase().includes(searchTerm.toLowerCase()) || 
    c.email.toLowerCase().includes(searchTerm.toLowerCase())
  );

  // --- RENDER: LOGIN ---
  if (!token) {
    return (
      <div className="h-screen w-full bg-[#09090b] flex items-center justify-center p-4 font-sans antialiased">
        <div className="w-full max-w-md bg-[#18181b] border border-[#27272a] rounded-3xl p-10 shadow-2xl relative">
          <div className="text-center mb-8">
            <div className="h-14 w-14 bg-indigo-600 rounded-2xl flex items-center justify-center shadow-lg shadow-indigo-600/20 mx-auto mb-4 text-white">
              <Shield size={28} />
            </div>
            <h1 className="text-3xl font-bold text-white tracking-tight">FluxHR Access</h1>
            <p className="text-[#a1a1aa] mt-2">Protocollo Sicurezza Talent v3.0</p>
          </div>

          <form onSubmit={handleLogin} className="space-y-4">
            {loginError && (
              <div className="bg-red-500/10 border border-red-500/20 text-red-400 p-3 rounded-xl text-xs flex items-center gap-2">
                <AlertCircle size={14} /> Credenziali non valide (admin/password).
              </div>
            )}
            <input 
              type="text" placeholder="Username" 
              className="w-full bg-[#09090b] border border-[#27272a] p-4 rounded-xl text-white outline-none focus:border-indigo-500 transition-all"
              onChange={e => setLoginData({...loginData, username: e.target.value})}
            />
            <input 
              type="password" placeholder="Password" 
              className="w-full bg-[#09090b] border border-[#27272a] p-4 rounded-xl text-white outline-none focus:border-indigo-500 transition-all"
              onChange={e => setLoginData({...loginData, password: e.target.value})}
            />
            <button className="w-full bg-indigo-600 hover:bg-indigo-500 p-4 rounded-xl text-white font-bold shadow-lg shadow-indigo-600/20 transition-all">
              Accedi al Database
            </button>
          </form>
        </div>
      </div>
    );
  }

  // --- RENDER: DASHBOARD ---
  return (
    <div className="flex h-screen bg-[#09090b] text-[#fafafa] font-sans overflow-hidden antialiased">
      {/* Sidebar */}
      <aside className="w-64 border-r border-[#27272a] bg-[#18181b] p-6 flex flex-col gap-4">
        <div className="flex items-center gap-3 px-2 mb-8">
          <div className="h-9 w-9 bg-indigo-600 rounded-xl flex items-center justify-center text-white">
            <Activity size={20} />
          </div>
          <span className="text-xl font-bold tracking-tight">FluxHR</span>
        </div>

        <nav className="flex flex-col gap-2">
          {[
            { id: 'stats', label: 'Dashboard', icon: <LayoutDashboard size={18}/> },
            { id: 'candidates', label: 'Candidati', icon: <Users size={18}/> },
            { id: 'gdpr', label: 'Compliance', icon: <Shield size={18}/> },
          ].map(item => (
            <button 
              key={item.id}
              onClick={() => setView(item.id)}
              className={`flex items-center gap-3 px-4 py-3 rounded-xl transition-all ${view === item.id ? 'bg-indigo-600/10 text-indigo-500 border border-indigo-500/20' : 'text-[#a1a1aa] hover:bg-white/5'}`}
            >
              {item.icon} {item.label}
            </button>
          ))}
        </nav>

        <button onClick={handleLogout} className="mt-auto p-4 text-red-400 hover:bg-red-500/10 rounded-xl flex items-center gap-3 transition-all">
          <LogOut size={18}/> Logout
        </button>
      </aside>

      <main className="flex-1 p-10 overflow-y-auto">
        <header className="flex justify-between items-center mb-12">
          <div>
            <h1 className="text-4xl font-bold tracking-tight capitalize">{view}</h1>
            <p className="text-[#a1a1aa] mt-1">Gestione Talenti Enterprise</p>
          </div>
          {view === 'candidates' && (
            <div className="relative w-80">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-[#71717a]" size={16} />
              <input 
                type="text" placeholder="Filtra candidati..." 
                className="w-full bg-[#18181b] border border-[#27272a] py-2 pl-10 pr-4 rounded-xl text-sm outline-none focus:border-indigo-500"
                value={searchTerm} onChange={e => setSearchTerm(e.target.value)}
              />
            </div>
          )}
        </header>

        {/* View 1: Statistiche */}
        {view === 'stats' && stats && (
          <div className="grid grid-cols-3 gap-6 animate-in fade-in duration-700">
            <div className="col-span-2 bg-[#18181b] p-8 rounded-3xl border border-[#27272a]">
              <h3 className="text-[#a1a1aa] mb-8 uppercase text-[10px] font-bold tracking-widest">Skill Distribution (Real-time)</h3>
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={stats.skills_bar}>
                    <XAxis dataKey="name" stroke="#525252" fontSize={10} axisLine={false} tickLine={false} />
                    <Tooltip cursor={{fill: '#27272a'}} contentStyle={{backgroundColor: '#18181b', border: 'none', borderRadius: '12px'}} />
                    <Bar dataKey="count" fill="#6366f1" radius={[4, 4, 0, 0]} barSize={35} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
            <div className="bg-indigo-600 p-8 rounded-3xl shadow-xl flex flex-col justify-center relative overflow-hidden group">
              <Users className="absolute -right-10 -bottom-10 w-48 h-48 opacity-10 group-hover:scale-110 transition-transform duration-700"/>
              <span className="text-indigo-100 uppercase text-[10px] font-bold relative z-10 tracking-widest">Talenti Acquisiti</span>
              <div className="text-7xl font-black mt-2 relative z-10">{stats.total_candidates}</div>
            </div>
          </div>
        )}

        {/* View 2: Lista Candidati */}
        {view === 'candidates' && (
          <div className="bg-[#18181b] rounded-3xl border border-[#27272a] overflow-hidden shadow-2xl animate-in fade-in duration-500">
            <table className="w-full text-left">
              <thead className="bg-[#27272a]/50 text-[#a1a1aa] text-[10px] uppercase tracking-widest font-bold">
                <tr>
                  <th className="p-6">Nominativo</th>
                  <th className="p-6">Stato Pipeline</th>
                  <th className="p-6">Azioni</th>
                  <th className="p-6 text-right">Data</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#27272a]">
                {filteredCandidates.map(c => (
                  <tr key={c.id} className="hover:bg-white/[0.02] transition-colors group">
                    <td className="p-6">
                      <div className="font-bold text-white">{c.name || 'In attesa di parsing...'}</div>
                      <div className="text-xs text-[#71717a]">{c.email}</div>
                    </td>
                    <td className="p-6">
                      <select 
                        value={c.status} 
                        onChange={(e) => updateStatus(c.id, e.target.value)}
                        className={`text-[10px] font-bold uppercase py-1.5 px-3 rounded-full border bg-transparent outline-none cursor-pointer transition-all ${
                          c.status === 'new' ? 'border-blue-500/40 text-blue-400' : 
                          c.status === 'reviewed' ? 'border-yellow-500/40 text-yellow-400' :
                          'border-emerald-500/40 text-emerald-400'
                        }`}
                      >
                        <option value="new" className="bg-[#18181b]">Nuovo</option>
                        <option value="reviewed" className="bg-[#18181b]">Revisionato</option>
                        <option value="shortlisted" className="bg-[#18181b]">Selezionato</option>
                        <option value="rejected" className="bg-[#18181b]">Scartato</option>
                      </select>
                    </td>
                    <td className="p-6">
                      <div className="flex items-center gap-3 opacity-0 group-hover:opacity-100 transition-opacity">
                        <button 
                          onClick={() => window.open(`${API_BASE}/candidates/${c.id}/download`)}
                          className="p-2 hover:bg-indigo-500/20 rounded-lg text-indigo-400 transition-colors"
                          title="Scarica CV"
                        >
                          <Download size={16} />
                        </button>
                        <button 
                          onClick={() => deleteCandidate(c.id)}
                          className="p-2 hover:bg-red-500/20 rounded-lg text-red-500 transition-colors"
                          title="Elimina (GDPR)"
                        >
                          <Trash2 size={16} />
                        </button>
                      </div>
                    </td>
                    <td className="p-6 text-right text-xs font-mono text-[#71717a]">
                      {new Date(c.created_at).toLocaleDateString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            {filteredCandidates.length === 0 && (
                <div className="p-20 text-center text-[#71717a]">Nessun candidato presente.</div>
            )}
          </div>
        )}

        {/* View 3: GDPR Compliance */}
        {view === 'gdpr' && (
          <div className="bg-[#18181b] border border-[#27272a] rounded-3xl p-10 animate-in fade-in duration-500 shadow-2xl">
            <div className="flex items-center justify-between mb-12">
              <div>
                <h2 className="text-2xl font-bold flex items-center gap-3"><Shield className="text-emerald-500"/> Registro Audit Privacy</h2>
                <p className="text-[#a1a1aa] text-sm mt-1 italic">Conformità ai sensi del Regolamento UE 2016/679</p>
              </div>
              <div className="bg-emerald-500/10 text-emerald-400 px-4 py-2 rounded-full border border-emerald-500/20 text-[10px] font-bold uppercase tracking-widest">
                Sistema Integro
              </div>
            </div>
            
            <div className="space-y-4">
              {candidates.map(c => (
                <div key={c.id} className="bg-[#09090b] p-6 rounded-2xl border border-[#27272a] flex justify-between items-center group hover:border-indigo-500/40 transition-all">
                  <div className="flex items-center gap-4">
                    <div className="p-3 bg-[#18181b] rounded-xl text-indigo-400 shadow-inner">
                      <Mail size={20}/>
                    </div>
                    <div>
                      <div className="text-sm font-bold text-white uppercase tracking-tight">Art. 14 Informative Sent</div>
                      <div className="text-xs text-[#71717a] font-mono">{c.email}</div>
                    </div>
                  </div>
                  <div className="flex items-center gap-4">
                    <div className="text-right hidden md:block mr-4">
                        <span className="block text-[10px] text-[#71717a] font-bold uppercase">Retention</span>
                        <span className="text-xs text-indigo-400 font-bold">180 giorni</span>
                    </div>
                    <div className="bg-emerald-500/10 text-emerald-400 text-[10px] font-bold px-4 py-2 rounded-full border border-emerald-500/20 flex items-center gap-2">
                        <CheckCircle size={14}/> Completed
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </main>
    </div>
  );
};

export default App;