import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useDropzone } from 'react-dropzone';
import Login from './Login';

const API_URL = 'http://localhost:8000';

// Configura axios con interceptor per aggiungere il token
const api = axios.create({ baseURL: API_URL });
api.interceptors.request.use(config => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
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

  // State per filtri e paginazione
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [page, setPage] = useState(0);
  const pageSize = 10;
  const [totalCandidates, setTotalCandidates] = useState(0);

  // Al mount, controlla se esiste un token
  useEffect(() => {
    const token = localStorage.getItem('token');
    if (token) {
      setIsAuthenticated(true);
    }
    setLoadingAuth(false);
  }, []);

  const fetchCandidates = async () => {
    if (!isAuthenticated) return;
    setLoading(true);
    try {
      const res = await api.get('/candidates', {
        params: {
          skip: page * pageSize,
          limit: pageSize,
          search: searchTerm || undefined,
          status: statusFilter || undefined,
        }
      });
      setCandidates(res.data);
      // Stima del totale per la paginazione (semplice)
      setTotalCandidates(res.data.length === pageSize ? (page + 2) * pageSize : (page + 1) * pageSize);
    } catch (err: any) {
      if (err.response?.status === 401) {
        localStorage.removeItem('token');
        setIsAuthenticated(false);
      }
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isAuthenticated) {
      fetchCandidates();
    }
  }, [isAuthenticated, page, searchTerm, statusFilter]);

  const handleLogin = (token: string) => {
    setIsAuthenticated(true);
  };

  const updateStatus = async (candidateId: number, newStatus: string) => {
    try {
      await api.patch(`/candidates/${candidateId}/status`, { status: newStatus });
      fetchCandidates();
    } catch (err) {
      console.error("Errore aggiornamento stato", err);
    }
  };

  const nextPage = () => {
    if (candidates.length === pageSize) {
      setPage(page + 1);
    }
  };

  const prevPage = () => {
    if (page > 0) setPage(page - 1);
  };

  const onDrop = async (acceptedFiles: File[]) => {
    const file = acceptedFiles[0];
    if (!file) return;
    const formData = new FormData();
    formData.append('file', file);
    setUploading(true);
    setUploadResult(null);
    try {
      const res = await api.post('/upload-cv', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      setUploadResult(res.data);
      fetchCandidates();
    } catch (err: any) {
      let errorMessage = 'Errore durante upload';
      if (err.response?.data?.detail) {
        const detail = err.response.data.detail;
        if (Array.isArray(detail)) {
          errorMessage = detail.map((e: any) => e.msg).join(', ');
        } else if (typeof detail === 'string') {
          errorMessage = detail;
        } else {
          errorMessage = JSON.stringify(detail);
        }
      } else if (err.message) {
        errorMessage = err.message;
      }
      setUploadResult({ error: errorMessage });
    } finally {
      setUploading(false);
    }
  };

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
    },
    maxFiles: 1,
  });

  const getStatusBadge = (status: string) => {
    const colors: Record<string, string> = {
      new: 'bg-yellow-100 text-yellow-800',
      reviewed: 'bg-blue-100 text-blue-800',
      shortlisted: 'bg-green-100 text-green-800',
      rejected: 'bg-red-100 text-red-800',
    };
    return colors[status] || 'bg-gray-100';
  };

  if (loadingAuth) {
    return <div className="min-h-screen flex items-center justify-center">Caricamento...</div>;
  }

  if (!isAuthenticated) {
    return <Login onLogin={handleLogin} />;
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-indigo-700 text-white shadow-lg">
        <div className="container mx-auto px-4 py-6 flex justify-between items-center">
          <h1 className="text-3xl font-bold">FluxHR Dashboard</h1>
          <button
            onClick={() => {
              localStorage.removeItem('token');
              setIsAuthenticated(false);
            }}
            className="bg-red-500 hover:bg-red-600 px-4 py-2 rounded-lg text-sm"
          >
            Logout
          </button>
        </div>
      </header>

      <main className="container mx-auto px-4 py-8">
        {/* Area upload CV */}
        <div className="bg-white rounded-xl shadow-md p-6 mb-8">
          <h2 className="text-xl font-semibold mb-4">Carica nuovo CV</h2>
          <div
            {...getRootProps()}
            className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition
              ${isDragActive ? 'border-indigo-500 bg-indigo-50' : 'border-gray-300 hover:border-indigo-400'}`}
          >
            <input {...getInputProps()} />
            {uploading ? (
              <div className="text-indigo-600">⏳ Elaborazione in corso...</div>
            ) : isDragActive ? (
              <p className="text-indigo-600">📂 Rilascia il file qui...</p>
            ) : (
              <div>
                <p className="text-gray-600">📄 Trascina un CV (PDF/DOCX) o clicca per selezionare</p>
                <p className="text-sm text-gray-400 mt-1">I dati sensibili vengono automaticamente sanitizzati (GDPR)</p>
              </div>
            )}
          </div>

          {uploadResult && (
            <div className={`mt-4 p-4 rounded-lg ${uploadResult.error ? 'bg-red-50 text-red-700' : 'bg-green-50 text-green-700'}`}>
              {uploadResult.error ? (
                <p>❌ {uploadResult.error}</p>
              ) : (
                <div>
                  <p>✅ CV processato e candidato salvato (ID: {uploadResult.candidate_id})</p>
                  <div className="mt-2 text-sm">
                    <p><strong>Nome estratto:</strong> {uploadResult.dati_estratti?.nome || 'non rilevato'}</p>
                    <p><strong>Email:</strong> {uploadResult.dati_estratti?.email || 'non rilevata'}</p>
                    <p><strong>Competenze:</strong> {uploadResult.dati_estratti?.competenze?.join(', ') || 'nessuna'}</p>
                  </div>
                  <p className="text-xs text-gray-500 mt-2">Nota: Email informativa Art.14 GDPR inviata al candidato (simulata)</p>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Filtri e paginazione */}
        <div className="p-4 border-b border-gray-200 bg-gray-50">
          <div className="flex flex-wrap gap-4 items-center">
            <div className="flex-1 min-w-[200px]">
              <input
                type="text"
                placeholder="Cerca per nome o email..."
                value={searchTerm}
                onChange={(e) => {
                  setSearchTerm(e.target.value);
                  setPage(0);
                }}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-indigo-500 focus:border-indigo-500"
              />
            </div>
            <div>
              <select
                value={statusFilter}
                onChange={(e) => {
                  setStatusFilter(e.target.value);
                  setPage(0);
                }}
                className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-indigo-500"
              >
                <option value="">Tutti gli stati</option>
                <option value="new">Nuovo</option>
                <option value="reviewed">In revisione</option>
                <option value="shortlisted">Selezionato</option>
                <option value="rejected">Scartato</option>
              </select>
            </div>
            <div className="flex gap-2">
              <button
                onClick={prevPage}
                disabled={page === 0}
                className="px-3 py-2 border rounded-lg disabled:opacity-50 hover:bg-gray-100"
              >
                ← Precedente
              </button>
              <span className="px-3 py-2">Pagina {page + 1}</span>
              <button
                onClick={nextPage}
                disabled={candidates.length < pageSize}
                className="px-3 py-2 border rounded-lg disabled:opacity-50 hover:bg-gray-100"
              >
                Successivo →
              </button>
            </div>
          </div>
        </div>

        {/* Lista candidati */}
        <div className="bg-white rounded-xl shadow-md overflow-hidden">
          <div className="px-6 py-4 border-b border-gray-200 flex justify-between items-center">
            <h2 className="text-xl font-semibold">Candidati registrati</h2>
            <button onClick={fetchCandidates} className="text-indigo-600 hover:text-indigo-800 text-sm">
              🔄 Aggiorna
            </button>
          </div>

          {loading ? (
            <div className="p-8 text-center text-gray-500">Caricamento candidati...</div>
          ) : candidates.length === 0 ? (
            <div className="p-8 text-center text-gray-500">Nessun candidato caricato. Trascina un CV nell'area sopra.</div>
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Nome</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Email</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Competenze</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Stato</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Azioni</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Data</th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {candidates.map((candidate) => (
                    <tr key={candidate.id} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                        {candidate.name || '—'}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{candidate.email}</td>
                      <td className="px-6 py-4 text-sm text-gray-500">
                        <div className="flex flex-wrap gap-1">
                          {candidate.skills.slice(0, 3).map(skill => (
                            <span key={skill} className="bg-gray-100 px-2 py-0.5 rounded text-xs">{skill}</span>
                          ))}
                          {candidate.skills.length > 3 && (
                            <span className="text-xs text-gray-400">+{candidate.skills.length - 3}</span>
                          )}
                        </div>
                       </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`px-2 py-1 inline-flex text-xs leading-5 font-semibold rounded-full ${getStatusBadge(candidate.status)}`}>
                          {candidate.status}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex gap-1">
                          <button
                            onClick={() => updateStatus(candidate.id, 'reviewed')}
                            className={`px-2 py-1 text-xs rounded ${candidate.status === 'reviewed'
                                ? 'bg-blue-600 text-white'
                                : 'bg-blue-100 text-blue-600 hover:bg-blue-200'
                              }`}
                          >
                            Reviewed
                          </button>
                          <button
                            onClick={() => updateStatus(candidate.id, 'shortlisted')}
                            className={`px-2 py-1 text-xs rounded ${candidate.status === 'shortlisted'
                                ? 'bg-green-600 text-white'
                                : 'bg-green-100 text-green-600 hover:bg-green-200'
                              }`}
                          >
                            Shortlist
                          </button>
                          <button
                            onClick={() => updateStatus(candidate.id, 'rejected')}
                            className={`px-2 py-1 text-xs rounded ${candidate.status === 'rejected'
                                ? 'bg-red-600 text-white'
                                : 'bg-red-100 text-red-600 hover:bg-red-200'
                              }`}
                          >
                            Reject
                          </button>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {new Date(candidate.created_at).toLocaleDateString()}
                      </td>
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