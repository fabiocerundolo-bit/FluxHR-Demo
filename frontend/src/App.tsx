import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useDropzone } from 'react-dropzone';
import Login from './Login';

const API_URL = 'http://localhost:8000';
const api = axios.create({ baseURL: API_URL });
api.interceptors.request.use(config => {
  const token = localStorage.getItem('token');
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

interface Candidate {
  id: number;
  name: string | null;
  email: string;
  skills: string[];
  status: string;
  created_at: string;
}

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [loadingAuth, setLoadingAuth] = useState(true);
  const [candidates, setCandidates] = useState<Candidate[]>([]);
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [uploadResult, setUploadResult] = useState<any>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [page, setPage] = useState(0);
  const pageSize = 10;
  const [uploadExpanded, setUploadExpanded] = useState(true);
  const [filtersExpanded, setFiltersExpanded] = useState(true);
  const [darkMode, setDarkMode] = useState(() => localStorage.getItem('darkMode') === 'true');
  const [presentationMode, setPresentationMode] = useState(false);

  useEffect(() => {
    if (darkMode) document.documentElement.classList.add('dark');
    else document.documentElement.classList.remove('dark');
    localStorage.setItem('darkMode', darkMode.toString());
  }, [darkMode]);

  useEffect(() => {
    const token = localStorage.getItem('token');
    if (token) setIsAuthenticated(true);
    setLoadingAuth(false);
  }, []);

  const fetchCandidates = async () => {
    if (!isAuthenticated) return;
    setLoading(true);
    try {
      const res = await api.get('/candidates', {
        params: { skip: page * pageSize, limit: pageSize, search: searchTerm || undefined, status: statusFilter || undefined }
      });
      setCandidates(res.data);
    } catch (err: any) {
      if (err.response?.status === 401) { localStorage.removeItem('token'); setIsAuthenticated(false); }
      console.error(err);
    } finally { setLoading(false); }
  };

  useEffect(() => {
    if (isAuthenticated) fetchCandidates();
  }, [isAuthenticated, page, searchTerm, statusFilter]);

  const handleLogin = (token: string) => setIsAuthenticated(true);
  const updateStatus = async (candidateId: number, newStatus: string) => {
    try { await api.patch(`/candidates/${candidateId}/status`, { status: newStatus }); fetchCandidates(); }
    catch (err) { console.error(err); }
  };
  const deleteCandidate = async (candidateId: number, candidateName: string) => {
    if (!window.confirm(`Eliminare "${candidateName || 'Id ' + candidateId}"?`)) return;
    try { await api.delete(`/candidates/${candidateId}`); fetchCandidates(); }
    catch (err) { console.error(err); alert("Errore durante l'eliminazione."); }
  };
  const nextPage = () => { if (candidates.length === pageSize) setPage(page+1); };
  const prevPage = () => { if (page > 0) setPage(page-1); };

  const onDrop = async (acceptedFiles: File[]) => {
    const file = acceptedFiles[0];
    if (!file) return;
    const formData = new FormData();
    formData.append('file', file);
    setUploading(true);
    setUploadResult(null);
    try {
      const res = await api.post('/upload-cv', formData, { headers: { 'Content-Type': 'multipart/form-data' } });
      setUploadResult(res.data);
      fetchCandidates();
    } catch (err: any) {
      let errorMessage = 'Errore durante upload';
      if (err.response?.data?.detail) {
        const detail = err.response.data.detail;
        if (Array.isArray(detail)) errorMessage = detail.map((e: any) => e.msg).join(', ');
        else if (typeof detail === 'string') errorMessage = detail;
        else errorMessage = JSON.stringify(detail);
      } else if (err.message) errorMessage = err.message;
      setUploadResult({ error: errorMessage });
    } finally { setUploading(false); }
  };

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { 'application/pdf': ['.pdf'], 'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'] },
    maxFiles: 1,
  });

  const getStatusBadge = (status: string) => {
    const colors: Record<string, string> = {
      new: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200',
      reviewed: 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200',
      shortlisted: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200',
      rejected: 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200',
    };
    return colors[status] || 'bg-gray-100 dark:bg-gray-700 dark:text-gray-300';
  };

  if (loadingAuth) return <div className="min-h-screen flex items-center justify-center dark:bg-gray-900 dark:text-white">Caricamento...</div>;
  if (!isAuthenticated) return <Login onLogin={handleLogin} />;

  const containerClass = `min-h-screen transition-all duration-300 ${darkMode ? 'dark bg-gray-900 text-white' : 'bg-gray-50 text-gray-900'} ${presentationMode ? 'p-2' : 'p-4'}`;
  const cardClass = `rounded-xl shadow-md overflow-hidden transition-all ${darkMode ? 'bg-gray-800 border border-gray-700' : 'bg-white'}`;
  const buttonClass = (isActive = false) => `px-3 py-2 rounded-lg text-sm font-medium transition ${darkMode ? (isActive ? 'bg-gray-600 text-white' : 'bg-gray-700 text-gray-200 hover:bg-gray-600') : (isActive ? 'bg-indigo-600 text-white' : 'bg-indigo-100 text-indigo-700 hover:bg-indigo-200')}`;

  return (
    <div className={containerClass}>
      <header className={`${cardClass} mb-4`}>
        <div className="px-4 py-3 flex flex-wrap justify-between items-center gap-2">
          <h1 className="text-2xl font-bold">FluxHR Dashboard</h1>
          <div className="flex gap-2">
            <button onClick={() => setDarkMode(!darkMode)} className={buttonClass()}>{darkMode ? '☀️ Chiaro' : '🌙 Scuro'}</button>
            <button onClick={() => setPresentationMode(!presentationMode)} className={buttonClass(presentationMode)}>{presentationMode ? '🎬 Esci presentazione' : '🎬 Presentazione'}</button>
            <button onClick={() => { localStorage.removeItem('token'); setIsAuthenticated(false); }} className="bg-red-500 hover:bg-red-600 text-white px-3 py-2 rounded-lg text-sm">Logout</button>
          </div>
        </div>
      </header>

      <main className={`${presentationMode ? 'space-y-2' : 'space-y-6'}`}>
        {/* Upload card */}
        <div className={cardClass}>
          <div className="px-4 py-3 border-b border-gray-200 dark:border-gray-700 flex justify-between items-center cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-700" onClick={() => setUploadExpanded(!uploadExpanded)}>
            <h2 className="text-lg font-semibold">📄 Carica CV</h2>
            <span className="text-xl">{uploadExpanded ? '−' : '+'}</span>
          </div>
          {uploadExpanded && (
            <div className={`${presentationMode ? 'p-2' : 'p-4'}`}>
              <div {...getRootProps()} className={`border-2 border-dashed rounded-lg p-4 text-center cursor-pointer transition ${isDragActive ? 'border-indigo-500 bg-indigo-50 dark:bg-indigo-900/30' : 'border-gray-300 dark:border-gray-600'}`}>
                <input {...getInputProps()} />
                {uploading ? <div className="text-indigo-600 dark:text-indigo-400">⏳ Elaborazione...</div> : isDragActive ? <p className="text-indigo-600 dark:text-indigo-400">📂 Rilascia il file...</p> : <div><p className="text-gray-600 dark:text-gray-300">📄 Trascina un CV (PDF/DOCX) o clicca</p><p className="text-xs text-gray-400 mt-1">GDPR: sanitizzazione automatica</p></div>}
              </div>
              {uploadResult && (
                <div className={`mt-3 p-2 rounded-lg text-sm ${uploadResult.error ? 'bg-red-100 text-red-700 dark:bg-red-900 dark:text-red-200' : 'bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-200'}`}>
                  {uploadResult.error ? `❌ ${uploadResult.error}` : (<div>✅ CV processato (ID: {uploadResult.candidate_id})<br /><strong>Nome:</strong> {uploadResult.dati_estratti?.nome || '—'}<br /><strong>Email:</strong> {uploadResult.dati_estratti?.email || '—'}</div>)}
                </div>
              )}
            </div>
          )}
        </div>

        {/* Filtri card */}
        <div className={cardClass}>
          <div className="px-4 py-3 border-b border-gray-200 dark:border-gray-700 flex justify-between items-center cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-700" onClick={() => setFiltersExpanded(!filtersExpanded)}>
            <h2 className="text-lg font-semibold">🔍 Filtri e navigazione</h2>
            <span className="text-xl">{filtersExpanded ? '−' : '+'}</span>
          </div>
          {filtersExpanded && (
            <div className={`${presentationMode ? 'p-2' : 'p-4'} bg-gray-50 dark:bg-gray-900/50`}>
              <div className="flex flex-wrap gap-2 items-center">
                <input type="text" placeholder="Cerca nome o email..." value={searchTerm} onChange={(e) => { setSearchTerm(e.target.value); setPage(0); }} className={`flex-1 min-w-[150px] px-3 py-2 border rounded-lg focus:ring-indigo-500 dark:bg-gray-800 dark:border-gray-600 dark:text-white ${presentationMode ? 'text-sm' : ''}`} />
                <select value={statusFilter} onChange={(e) => { setStatusFilter(e.target.value); setPage(0); }} className="px-3 py-2 border rounded-lg dark:bg-gray-800 dark:border-gray-600">
                  <option value="">Tutti</option><option value="new">Nuovo</option><option value="reviewed">In revisione</option><option value="shortlisted">Selezionato</option><option value="rejected">Scartato</option>
                </select>
                <div className="flex gap-1"><button onClick={prevPage} disabled={page===0} className={buttonClass()}>← Prec.</button><span className="px-2 py-2">Pag. {page+1}</span><button onClick={nextPage} disabled={candidates.length<pageSize} className={buttonClass()}>Succ. →</button></div>
              </div>
            </div>
          )}
        </div>

        {/* Tabella candidati */}
        <div className={cardClass}>
          <div className="px-4 py-3 border-b border-gray-200 dark:border-gray-700 flex justify-between items-center"><h2 className="text-lg font-semibold">📋 Candidati</h2><button onClick={fetchCandidates} className="text-indigo-600 dark:text-indigo-400 text-sm">🔄 Aggiorna</button></div>
          {loading ? <div className="p-8 text-center">Caricamento...</div> : candidates.length===0 ? <div className="p-8 text-center">Nessun candidato. Carica un CV.</div> : (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
                <thead className="bg-gray-50 dark:bg-gray-800"><tr><th className="px-4 py-2 text-left text-xs font-medium uppercase">Nome</th><th className="px-4 py-2 text-left text-xs font-medium uppercase">Email</th><th className="px-4 py-2 text-left text-xs font-medium uppercase">Competenze</th><th className="px-4 py-2 text-left text-xs font-medium uppercase">Stato</th><th className="px-4 py-2 text-left text-xs font-medium uppercase">Azioni</th><th className="px-4 py-2 text-left text-xs font-medium uppercase">Data</th><th className="px-4 py-2 text-left text-xs font-medium uppercase">Elimina</th></tr></thead>
                <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
                  {candidates.map(c => (
                    <tr key={c.id} className="hover:bg-gray-50 dark:hover:bg-gray-800">
                      <td className="px-4 py-2 whitespace-nowrap text-sm">{c.name||'—'}</td>
                      <td className="px-4 py-2 whitespace-nowrap text-sm">{c.email}</td>
                      <td className="px-4 py-2 text-sm">{c.skills.slice(0,2).join(', ')}{c.skills.length>2 && ' +'}</td>
                      <td className="px-4 py-2 whitespace-nowrap"><span className={`px-2 py-0.5 rounded-full text-xs ${getStatusBadge(c.status)}`}>{c.status}</span></td>
                      <td className="px-4 py-2 whitespace-nowrap"><div className="flex gap-1"><button onClick={()=>updateStatus(c.id,'reviewed')} className="px-2 py-0.5 text-xs rounded bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-200">Review</button><button onClick={()=>updateStatus(c.id,'shortlisted')} className="px-2 py-0.5 text-xs rounded bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-200">Short</button><button onClick={()=>updateStatus(c.id,'rejected')} className="px-2 py-0.5 text-xs rounded bg-red-100 text-red-700 dark:bg-red-900 dark:text-red-200">Reject</button></div></td>
                      <td className="px-4 py-2 whitespace-nowrap text-xs">{new Date(c.created_at).toLocaleDateString()}</td>
                      <td className="px-4 py-2 whitespace-nowrap text-center"><button onClick={()=>deleteCandidate(c.id,c.name||'')} className="text-red-600 hover:text-red-800 text-sm" title="Elimina">🗑️</button></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}

export default App;