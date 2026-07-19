import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Shield, Mail, Lock, User as UserIcon, Building, ArrowRight, AlertTriangle } from 'lucide-react';
import { API_BASE } from '../context/AuthContext';

export const Register: React.FC = () => {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [tenantName, setTenantName] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const res = await fetch(`${API_BASE}/auth/register`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          name,
          email,
          tenant_name: tenantName,
          password,
        }),
      });

      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || 'Registration failed.');
      }

      login(data.access_token, data.user);
      navigate('/');
    } catch (err: any) {
      setError(err.message || 'Something went wrong during registration.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#020617] flex items-center justify-center p-4 relative overflow-hidden">
      {/* Background Gradients */}
      <div className="absolute top-1/4 left-1/4 -translate-x-1/2 -translate-y-1/2 w-[500px] h-[500px] bg-red-500/10 rounded-full blur-[120px] pointer-events-none"></div>
      <div className="absolute bottom-1/4 right-1/4 translate-x-1/2 translate-y-1/2 w-[500px] h-[500px] bg-blue-500/10 rounded-full blur-[120px] pointer-events-none"></div>

      <div className="w-full max-w-md relative z-10">
        {/* Brand */}
        <div className="text-center mb-8">
          <div className="inline-flex p-3 bg-red-500/10 border border-red-500/20 rounded-2xl mb-4 shadow-lg shadow-red-500/5">
            <Shield className="h-10 w-10 text-red-500 fill-red-500/10" />
          </div>
          <h1 className="font-outfit text-3xl font-extrabold tracking-tight text-white">
            Register Web Security <span className="text-red-500">Suite</span>
          </h1>
          <p className="text-slate-400 text-sm mt-1.5">Launch your secure multi-tenant environment</p>
        </div>

        {/* Form Panel */}
        <div className="glass-panel p-8 rounded-2xl shadow-glass">
          <form onSubmit={handleSubmit} className="space-y-5">
            {error && (
              <div className="bg-red-500/10 border border-red-500/20 rounded-xl p-4 flex items-start space-x-3 text-red-400 text-sm">
                <AlertTriangle className="h-5 w-5 shrink-0 mt-0.5" />
                <span>{error}</span>
              </div>
            )}

            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-slate-400 mb-1.5">
                Full Name
              </label>
              <div className="relative">
                <UserIcon className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-slate-500" />
                <input
                  type="text"
                  required
                  placeholder="John Doe"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className="w-full pl-11 pr-4 py-2.5 bg-[#090f23] border border-slate-800 rounded-xl text-slate-100 placeholder-slate-500 focus:outline-none focus:border-red-500 transition-colors"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-slate-400 mb-1.5">
                Company / Tenant Name
              </label>
              <div className="relative">
                <Building className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-slate-500" />
                <input
                  type="text"
                  required
                  placeholder="Acme Cybersec"
                  value={tenantName}
                  onChange={(e) => setTenantName(e.target.value)}
                  className="w-full pl-11 pr-4 py-2.5 bg-[#090f23] border border-slate-800 rounded-xl text-slate-100 placeholder-slate-500 focus:outline-none focus:border-red-500 transition-colors"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-slate-400 mb-1.5">
                Email Address
              </label>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-slate-500" />
                <input
                  type="email"
                  required
                  placeholder="john@company.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full pl-11 pr-4 py-2.5 bg-[#090f23] border border-slate-800 rounded-xl text-slate-100 placeholder-slate-500 focus:outline-none focus:border-red-500 transition-colors"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-slate-400 mb-1.5">
                Secure Password
              </label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-slate-500" />
                <input
                  type="password"
                  required
                  placeholder="••••••••"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full pl-11 pr-4 py-2.5 bg-[#090f23] border border-slate-800 rounded-xl text-slate-100 placeholder-slate-500 focus:outline-none focus:border-red-500 transition-colors"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full py-3 px-4 bg-red-500 hover:bg-red-600 disabled:bg-red-500/50 text-white font-semibold rounded-xl flex items-center justify-center space-x-2 transition-all duration-200 shadow-lg shadow-red-500/20"
            >
              <span>{loading ? 'Initializing Workspace...' : 'Create Secure Workspace'}</span>
              {!loading && <ArrowRight className="h-4 w-4" />}
            </button>
          </form>

          <div className="mt-5 border-t border-slate-800 pt-5 text-center text-sm text-slate-500">
            Already have a workspace?{' '}
            <Link to="/login" className="text-red-500 hover:underline font-semibold">
              Sign In
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
};
export default Register;
