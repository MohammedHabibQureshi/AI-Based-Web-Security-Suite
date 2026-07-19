import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { Key, Bell, Shield, CheckCircle2 } from 'lucide-react';

export const Settings: React.FC = () => {
  const { user } = useAuth();
  
  // Gemini settings
  const [geminiKey, setGeminiKey] = useState('');
  const [geminiModel, setGeminiModel] = useState('gemini-1.5-flash');
  const [savedGemini, setSavedGemini] = useState(false);

  // Alerts settings
  const [emailAlerts, setEmailAlerts] = useState('immediate');
  const [savedAlerts, setSavedAlerts] = useState(false);

  useEffect(() => {
    const savedKey = localStorage.getItem('sentinel_gemini_key') || '';
    const savedModel = localStorage.getItem('sentinel_gemini_model') || 'gemini-1.5-flash';
    setGeminiKey(savedKey);
    setGeminiModel(savedModel);

    const savedEmailSetting = localStorage.getItem('sentinel_alerts_email') || 'immediate';
    setEmailAlerts(savedEmailSetting);
  }, []);

  const saveGeminiSettings = (e: React.FormEvent) => {
    e.preventDefault();
    localStorage.setItem('sentinel_gemini_key', geminiKey);
    localStorage.setItem('sentinel_gemini_model', geminiModel);
    setSavedGemini(true);
    setTimeout(() => setSavedGemini(false), 3000);
  };

  const saveAlertSettings = (e: React.FormEvent) => {
    e.preventDefault();
    localStorage.setItem('sentinel_alerts_email', emailAlerts);
    setSavedAlerts(true);
    setTimeout(() => setSavedAlerts(false), 3000);
  };

  return (
    <div className="space-y-8 animate-fadeIn">
      <div>
        <h1 className="text-2xl font-bold text-white tracking-tight">Web Security Suite Settings</h1>
        <p className="text-sm text-slate-400">Configure team API integrations, threat notifications, and model selection</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        {/* Bring Your Own Gemini Key */}
        <div className="glass-panel p-6 rounded-2xl space-y-6">
          <h3 className="text-base font-bold text-white flex items-center space-x-2 border-b border-slate-800/80 pb-4">
            <Key className="h-5 w-5 text-red-500" />
            <span>AI Model & API Integration</span>
          </h3>

          <form onSubmit={saveGeminiSettings} className="space-y-4">
            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-slate-400 mb-1.5">
                Gemini API Provider Key
              </label>
              <input
                type="password"
                placeholder="AIzaSy..."
                value={geminiKey}
                onChange={(e) => setGeminiKey(e.target.value)}
                className="w-full px-4 py-2.5 bg-[#090f23] border border-slate-800 rounded-xl text-slate-100 placeholder-slate-500 focus:outline-none focus:border-red-500 transition-colors text-xs"
              />
              <span className="text-[10px] text-slate-500 block mt-1.5">
                Enterprise bring-your-own-key settings. If empty, the system uses the default global server-side key.
              </span>
            </div>

            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-slate-400 mb-1.5">
                Model Name
              </label>
              <select
                value={geminiModel}
                onChange={(e) => setGeminiModel(e.target.value)}
                className="w-full px-4 py-2.5 bg-[#090f23] border border-slate-800 rounded-xl text-slate-100 focus:outline-none focus:border-red-500 transition-colors text-xs"
              >
                <option value="gemini-1.5-flash">gemini-1.5-flash (Fast & Affordable)</option>
                <option value="gemini-2.0-flash">gemini-2.0-flash (High Context Detections)</option>
              </select>
            </div>

            <button
              type="submit"
              className="px-4 py-2.5 bg-red-500 hover:bg-red-600 text-white text-xs font-semibold rounded-xl flex items-center space-x-1.5 transition-colors"
            >
              <span>Save AI Settings</span>
              {savedGemini && <CheckCircle2 className="h-4 w-4" />}
            </button>
          </form>
        </div>

        {/* Threat Notifications */}
        <div className="glass-panel p-6 rounded-2xl space-y-6">
          <h3 className="text-base font-bold text-white flex items-center space-x-2 border-b border-slate-800/80 pb-4">
            <Bell className="h-5 w-5 text-red-500" />
            <span>SMTP Alerts & Notifications</span>
          </h3>

          <form onSubmit={saveAlertSettings} className="space-y-4">
            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-slate-400 mb-1.5">
                Critical threat alerts
              </label>
              <select
                value={emailAlerts}
                onChange={(e) => setEmailAlerts(e.target.value)}
                className="w-full px-4 py-2.5 bg-[#090f23] border border-slate-800 rounded-xl text-slate-100 focus:outline-none focus:border-red-500 transition-colors text-xs"
              >
                <option value="immediate">Immediate Dispatch (SMTP Server Send)</option>
                <option value="daily">Daily Digest Summary</option>
                <option value="disabled">Muted / Disabled</option>
              </select>
              <span className="text-[10px] text-slate-500 block mt-1.5">
                SMTP credentials must be fully established in your global backend settings configuration.
              </span>
            </div>

            <button
              type="submit"
              className="px-4 py-2.5 bg-red-500 hover:bg-red-600 text-white text-xs font-semibold rounded-xl flex items-center space-x-1.5 transition-colors"
            >
              <span>Save Alert Choices</span>
              {savedAlerts && <CheckCircle2 className="h-4 w-4" />}
            </button>
          </form>
        </div>

        {/* Profile Card */}
        <div className="glass-panel p-6 rounded-2xl md:col-span-2 space-y-4">
          <h3 className="text-base font-bold text-white flex items-center space-x-2 border-b border-slate-800/80 pb-4">
            <Shield className="h-5 w-5 text-red-500" />
            <span>Workspace Permissions & Access Control</span>
          </h3>
          <div className="grid grid-cols-2 gap-6 text-xs">
            <div className="space-y-1">
              <span className="text-slate-500 block">Workspace Member</span>
              <strong className="text-white text-sm">{user?.name}</strong>
            </div>
            <div className="space-y-1">
              <span className="text-slate-500 block">Assigned Role</span>
              <strong className="text-white text-sm uppercase tracking-wider text-red-400">{user?.role}</strong>
            </div>
            <div className="space-y-1">
              <span className="text-slate-500 block">Registered Email</span>
              <strong className="text-white text-sm">{user?.email}</strong>
            </div>
            <div className="space-y-1">
              <span className="text-slate-500 block">Establish Date</span>
              <strong className="text-white text-sm">{user?.created_at.substring(0, 10)}</strong>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
export default Settings;
