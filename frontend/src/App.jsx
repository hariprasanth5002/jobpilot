import React, { useState } from 'react';
import Sidebar from './components/Sidebar';
import FileUploadCard from './components/FileUploadCard';
import ProfileFormCard from './components/ProfileFormCard';
import AskQuestionCard from './components/AskQuestionCard';
import AnswerDisplayCard from './components/AnswerDisplayCard';
import { FileText, Compass, CheckCircle2 } from 'lucide-react';

export default function App() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [uploadsState, setUploadsState] = useState({
    resume: false,
    job_description: false,
    user_details: false,
  });

  const [chatResult, setChatResult] = useState(null);
  const [chatLoading, setChatLoading] = useState(false);
  const [chatError, setChatError] = useState('');

  const isProfileReady = uploadsState.resume || uploadsState.job_description || uploadsState.user_details;

  const handleUploadSuccess = (sourceKey) => {
    setUploadsState((prev) => ({ ...prev, [sourceKey]: true }));
  };

  const handleProfileSuccess = () => {
    setUploadsState((prev) => ({ ...prev, user_details: true }));
  };

  const handleAskQuestion = async (question) => {
    setChatLoading(true);
    setChatError('');

    try {
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ question }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || `Server returned status ${response.status}`);
      }

      setChatResult(data);
    } catch (err) {
      console.error('Chat error:', err);
      setChatError(err.message || 'Failed to connect to JobPilot backend. Ensure FastAPI server is running on http://localhost:8000.');
    } finally {
      setChatLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen bg-slate-50 text-slate-900 font-sans">
      {/* Left Sidebar Navigation */}
      <Sidebar activeTab={activeTab} onSelectTab={setActiveTab} />

      {/* Main Dashboard Area */}
      <div className="flex-1 flex flex-col min-w-0 min-h-screen">
        {/* Top Navbar Header */}
        <header className="bg-white border-b border-slate-200 px-8 py-4 flex items-center justify-between sticky top-0 z-10 shadow-2xs">
          <div>
            <h2 className="text-base font-bold text-slate-900">Career Assistant Dashboard</h2>
            <p className="text-xs text-slate-500">Analyze fit, identify skill gaps, and get grounded interview preparation</p>
          </div>

          <div className="flex items-center gap-3 text-xs">
            <span className={`px-2.5 py-1 rounded-md border text-[11px] font-medium ${
              isProfileReady ? 'bg-emerald-50 border-emerald-200 text-emerald-700' : 'bg-slate-100 border-slate-200 text-slate-600'
            }`}>
              Knowledge Base: {isProfileReady ? 'Ready' : 'Pending Uploads'}
            </span>
          </div>
        </header>

        {/* Content Body */}
        <main className="flex-1 max-w-5xl w-full mx-auto p-8 space-y-8">
          {/* Welcome / Readiness Status Banner */}
          <div className="p-4 rounded-xl border border-slate-200 bg-white shadow-xs flex items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              <CheckCircle2 className={`w-5 h-5 shrink-0 ${isProfileReady ? 'text-emerald-600' : 'text-blue-600'}`} />
              <div>
                <p className="font-semibold text-sm text-slate-900">
                  {isProfileReady
                    ? 'Your job-specific knowledge base is ready.'
                    : 'Upload your resume and job description to start personalized preparation.'}
                </p>
                <p className="text-xs text-slate-500 mt-0.5">
                  {isProfileReady
                    ? 'FAISS index & metadata populated. Ask questions below for grounded, guardrailed answers.'
                    : 'Documents will be chunked, embedded via all-MiniLM-L6-v2, and indexed into FAISS.'}
                </p>
              </div>
            </div>

            <div className="flex items-center gap-3 text-xs font-medium text-slate-600 shrink-0 font-mono">
              <span className={uploadsState.resume ? 'text-emerald-700 font-semibold' : 'text-slate-400'}>
                Resume {uploadsState.resume ? '✓' : ''}
              </span>
              <span>·</span>
              <span className={uploadsState.job_description ? 'text-emerald-700 font-semibold' : 'text-slate-400'}>
                JD {uploadsState.job_description ? '✓' : ''}
              </span>
              <span>·</span>
              <span className={uploadsState.user_details ? 'text-emerald-700 font-semibold' : 'text-slate-400'}>
                Profile {uploadsState.user_details ? '✓' : ''}
              </span>
            </div>
          </div>

          {/* STEP 01 — Build your profile */}
          <section className="space-y-4">
            <div className="flex items-center gap-2 border-b border-slate-200 pb-2">
              <span className="font-mono text-xs font-bold text-blue-600 bg-blue-50 px-2 py-0.5 rounded border border-blue-100">01</span>
              <h3 className="text-sm font-bold text-slate-900">Build your profile</h3>
            </div>

            {/* Documents Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <FileUploadCard
                title="Resume"
                endpoint="/api/documents/resume"
                icon={FileText}
                sourceKey="resume"
                onUploadSuccess={handleUploadSuccess}
              />

              <FileUploadCard
                title="Job Description"
                endpoint="/api/documents/job-description"
                icon={Compass}
                sourceKey="job_description"
                onUploadSuccess={handleUploadSuccess}
              />
            </div>

            {/* Candidate Profile Form */}
            <ProfileFormCard onProfileSuccess={handleProfileSuccess} />
          </section>

          {/* STEP 02 — Ask JobPilot */}
          <section className="space-y-4">
            <div className="flex items-center gap-2 border-b border-slate-200 pb-2">
              <span className="font-mono text-xs font-bold text-blue-600 bg-blue-50 px-2 py-0.5 rounded border border-blue-100">02</span>
              <h3 className="text-sm font-bold text-slate-900">Ask JobPilot</h3>
            </div>

            <AskQuestionCard
              onAskQuestion={handleAskQuestion}
              loading={chatLoading}
              error={chatError}
            />
          </section>

          {/* STEP 03 — Review your guidance */}
          <section className="space-y-4">
            <div className="flex items-center gap-2 border-b border-slate-200 pb-2">
              <span className="font-mono text-xs font-bold text-blue-600 bg-blue-50 px-2 py-0.5 rounded border border-blue-100">03</span>
              <h3 className="text-sm font-bold text-slate-900">Review your guidance</h3>
            </div>

            <AnswerDisplayCard result={chatResult} loading={chatLoading} />
          </section>
        </main>
      </div>
    </div>
  );
}
