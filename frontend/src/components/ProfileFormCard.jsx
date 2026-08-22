import React, { useState } from 'react';
import { User, Check, Loader2, AlertCircle } from 'lucide-react';

export default function ProfileFormCard({ onProfileSuccess }) {
  const [formData, setFormData] = useState({
    target_role: 'Senior Backend Engineer',
    skills: 'Python, FastAPI, Docker, Kubernetes, PostgreSQL, Redis, FAISS, PyTorch',
    projects: 'Agri Notifier (real-time crop telemetry alert system built with Python & FastAPI)',
    experience: '6 years specializing in distributed systems and FastAPI backends',
    education: 'B.S. in Computer Science - UC Berkeley',
    career_goals: 'Senior AI & Backend Engineer specializing in RAG systems',
  });

  const [submitting, setSubmitting] = useState(false);
  const [successInfo, setSuccessInfo] = useState(null);
  const [errorMsg, setErrorMsg] = useState('');

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    setErrorMsg('');
    setSuccessInfo(null);

    try {
      const response = await fetch('/api/profile', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || `Profile submission failed with status ${response.status}`);
      }

      setSuccessInfo(data);
      if (onProfileSuccess) {
        onProfileSuccess(data);
      }
    } catch (err) {
      console.error('Profile submit error:', err);
      setErrorMsg(err.message || 'Failed to submit profile details.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-xs">
      <div className="flex items-center gap-2 mb-4">
        <User className="w-4 h-4 text-blue-600" />
        <h3 className="font-semibold text-slate-900 text-sm">Candidate Profile</h3>
      </div>

      <form onSubmit={handleSubmit} className="space-y-3">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          <div>
            <label className="block text-xs font-medium text-slate-700 mb-1">Target Role</label>
            <input
              type="text"
              name="target_role"
              value={formData.target_role}
              onChange={handleChange}
              placeholder="e.g. Senior Backend Engineer"
              className="w-full bg-slate-50 border border-slate-200 rounded-lg px-3 py-2 text-xs text-slate-900 focus:outline-none focus:border-blue-600 focus:bg-white transition-colors"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-700 mb-1">Years of Experience</label>
            <input
              type="text"
              name="experience"
              value={formData.experience}
              onChange={handleChange}
              placeholder="e.g. 6 years"
              className="w-full bg-slate-50 border border-slate-200 rounded-lg px-3 py-2 text-xs text-slate-900 focus:outline-none focus:border-blue-600 focus:bg-white transition-colors"
            />
          </div>
        </div>

        <div>
          <label className="block text-xs font-medium text-slate-700 mb-1">Skills</label>
          <input
            type="text"
            name="skills"
            value={formData.skills}
            onChange={handleChange}
            placeholder="e.g. Python, FastAPI, Docker, Kubernetes, FAISS, PyTorch"
            className="w-full bg-slate-50 border border-slate-200 rounded-lg px-3 py-2 text-xs text-slate-900 focus:outline-none focus:border-blue-600 focus:bg-white transition-colors"
          />
        </div>

        <div>
          <label className="block text-xs font-medium text-slate-700 mb-1">Projects</label>
          <input
            type="text"
            name="projects"
            value={formData.projects}
            onChange={handleChange}
            placeholder="e.g. Agri Notifier"
            className="w-full bg-slate-50 border border-slate-200 rounded-lg px-3 py-2 text-xs text-slate-900 focus:outline-none focus:border-blue-600 focus:bg-white transition-colors"
          />
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          <div>
            <label className="block text-xs font-medium text-slate-700 mb-1">Education</label>
            <input
              type="text"
              name="education"
              value={formData.education}
              onChange={handleChange}
              placeholder="e.g. B.S. Computer Science"
              className="w-full bg-slate-50 border border-slate-200 rounded-lg px-3 py-2 text-xs text-slate-900 focus:outline-none focus:border-blue-600 focus:bg-white transition-colors"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-700 mb-1">Career Goals</label>
            <input
              type="text"
              name="career_goals"
              value={formData.career_goals}
              onChange={handleChange}
              placeholder="e.g. Backend/AI engineering"
              className="w-full bg-slate-50 border border-slate-200 rounded-lg px-3 py-2 text-xs text-slate-900 focus:outline-none focus:border-blue-600 focus:bg-white transition-colors"
            />
          </div>
        </div>

        {errorMsg && (
          <div className="p-2.5 rounded-lg bg-rose-50 border border-rose-200 text-rose-700 text-xs flex items-start gap-2">
            <AlertCircle className="w-4 h-4 text-rose-500 shrink-0 mt-0.5" />
            <span>{errorMsg}</span>
          </div>
        )}

        {successInfo && (
          <div className="p-2.5 rounded-lg bg-slate-50 border border-slate-200 text-xs flex items-center gap-2 text-emerald-700 font-medium">
            <Check className="w-3.5 h-3.5 text-emerald-600" />
            <span>Profile details saved & added to knowledge base</span>
          </div>
        )}

        <button
          type="submit"
          disabled={submitting}
          className="w-full py-2.5 px-4 mt-2 rounded-lg font-medium text-xs bg-blue-600 hover:bg-blue-700 text-white flex items-center justify-center gap-2 transition-colors shadow-xs disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {submitting ? (
            <>
              <Loader2 className="w-3.5 h-3.5 animate-spin text-white" />
              <span>Saving Profile...</span>
            </>
          ) : (
            <span>Build Profile</span>
          )}
        </button>
      </form>
    </div>
  );
}
