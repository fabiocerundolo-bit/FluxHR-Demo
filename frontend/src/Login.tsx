import React, { useState } from 'react';
import axios from 'axios';

interface LoginProps {
  onLogin: (token: string) => void;
}

const Login: React.FC<LoginProps> = ({ onLogin }) => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const formData = new URLSearchParams();
      formData.append('username', username);
      formData.append('password', password);
      const res = await axios.post('http://localhost:8000/token', formData, {
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
      });
      localStorage.setItem('token', res.data.access_token);
      onLogin(res.data.access_token);
    } catch (err) {
      setError('Login fallito');
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-100">
      <div className="bg-white p-8 rounded shadow-md w-96">
        <h2 className="text-2xl font-bold mb-6">FluxHR - Accesso</h2>
        <form onSubmit={handleSubmit}>
          <input type="text" placeholder="Username" className="w-full p-2 border mb-4" value={username} onChange={e => setUsername(e.target.value)} />
          <input type="password" placeholder="Password" className="w-full p-2 border mb-4" value={password} onChange={e => setPassword(e.target.value)} />
          {error && <p className="text-red-500">{error}</p>}
          <button type="submit" className="w-full bg-indigo-600 text-white py-2 rounded">Accedi</button>
        </form>
        <p className="mt-4 text-sm text-gray-500">Credenziali demo: admin / fluxhr2025</p>
      </div>
    </div>
  );
};

export default Login;