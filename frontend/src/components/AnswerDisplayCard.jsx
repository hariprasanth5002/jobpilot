import React from 'react';
import { ShieldAlert, Layers } from 'lucide-react';

export default function AnswerDisplayCard({ result, loading }) {
  if (loading) {
    return (
      <div className="bg-white border border-slate-200 rounded-xl p-6 text-center animate-pulse space-y-2 shadow-xs">
        <div className="w-5 h-5 border-2 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto mb-2" />
        <h3 className="text-sm font-medium text-slate-800">Analyzing Profile & Grounding Context...</h3>
        <p className="text-xs text-slate-500">Retrieving FAISS vectors → checking context guardrails → Ollama local LLM</p>
      </div>
    );
  }

  if (!result) {
    return (
      <div className="bg-white border border-dashed border-slate-200 rounded-xl p-6 text-center shadow-xs">
        <h3 className="text-xs font-medium text-slate-600">No analysis performed yet</h3>
        <p className="text-xs text-slate-400 mt-1 max-w-sm mx-auto">
          Upload your resume and job description, then ask a question above to generate grounded career guidance.
        </p>
      </div>
    );
  }

  const { question, intent, answer, sources, guardrail_blocked } = result;

  // Format response line by line cleanly
  const renderFormattedAnswer = (text) => {
    if (!text) return null;

    const lines = text.split('\n');
    const elements = [];
    let currentBulletList = [];

    const flushList = (keyPrefix) => {
      if (currentBulletList.length > 0) {
        elements.push(
          <ul key={`${keyPrefix}-list`} className="space-y-1.5 my-2 text-slate-700 text-xs">
            {currentBulletList.map((item, i) => (
              <li key={i} className="flex items-start gap-2">
                <span className="text-slate-400 font-bold">•</span>
                <span className="leading-relaxed">{item}</span>
              </li>
            ))}
          </ul>
        );
        currentBulletList = [];
      }
    };

    lines.forEach((line, index) => {
      const trimmed = line.trim();
      if (!trimmed) {
        flushList(`empty-${index}`);
        return;
      }

      // Check section headings
      if (
        trimmed.endsWith(':') ||
        /^(Matched Skills|Missing \/ Unverified|Priority|Reason|Requirement|What it means|Why it matters|Current candidate evidence|Preparation Priorities|Candidate Strengths|Areas to Prepare|Project to Highlight|How to Explain It|Possible Follow-Up Questions)/i.test(trimmed) ||
        /^(\d+\.\s+[A-Z])/.test(trimmed)
      ) {
        flushList(`heading-${index}`);
        elements.push(
          <h4 key={`h-${index}`} className="font-semibold text-slate-900 text-xs mt-3.5 mb-1 text-blue-700">
            {trimmed}
          </h4>
        );
      } else if (trimmed.startsWith('- ') || trimmed.startsWith('* ') || trimmed.startsWith('• ')) {
        const bulletText = trimmed.replace(/^[-*•]\s*/, '');
        currentBulletList.push(bulletText);
      } else {
        flushList(`p-${index}`);
        elements.push(
          <p key={`p-${index}`} className="text-xs text-slate-700 leading-relaxed my-1">
            {trimmed}
          </p>
        );
      }
    });

    flushList('final');
    return elements;
  };

  return (
    <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-xs space-y-4">
      {/* Response Header */}
      <div className="flex flex-wrap items-center justify-between gap-2 pb-3 border-b border-slate-100">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">AI Guidance</span>
            <span className="text-xs text-slate-300">•</span>
            <span className="text-xs font-semibold text-blue-600 capitalize">
              Intent: {intent}
            </span>
          </div>
          <p className="text-xs text-slate-800 mt-1 font-medium">"{question}"</p>
        </div>

        {guardrail_blocked && (
          <span className="text-xs px-2.5 py-0.5 rounded border bg-amber-50 border-amber-200 text-amber-800 font-medium flex items-center gap-1">
            <ShieldAlert className="w-3.5 h-3.5 text-amber-600" />
            <span>Guardrail Intercepted</span>
          </span>
        )}
      </div>

      {/* Answer Body */}
      <div className="bg-slate-50 border border-slate-200 rounded-lg p-4 text-xs font-normal text-slate-800 leading-relaxed">
        {guardrail_blocked && (
          <div className="mb-3 p-3 rounded bg-amber-50 border border-amber-200 text-amber-900 text-xs flex items-start gap-2">
            <ShieldAlert className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
            <div>
              <p className="font-semibold text-amber-900">Insufficient Context in Uploaded Documents</p>
              <p className="text-[11px] text-amber-800 mt-0.5">
                The requested information was not found in your provided resume or job description. Ollama generation was suppressed to prevent hallucination.
              </p>
            </div>
          </div>
        )}

        <div className="space-y-1">{renderFormattedAnswer(answer)}</div>
      </div>

      {/* Grounded Sources */}
      <div className="pt-1">
        <div className="flex items-center gap-1.5 text-xs text-slate-500 font-medium mb-2">
          <Layers className="w-3.5 h-3.5 text-slate-400" />
          <span>Grounded Sources</span>
        </div>

        {sources && sources.length > 0 ? (
          <div className="flex flex-wrap gap-2">
            {sources.map((src, idx) => (
              <span
                key={idx}
                className="text-[11px] px-2.5 py-1 rounded bg-slate-50 border border-slate-200 text-slate-700 font-mono"
              >
                <strong className="font-semibold capitalize text-slate-900">{src.source.replace('_', ' ')}</strong>
                {src.section && <span className="text-slate-500"> · {src.section}</span>}
              </span>
            ))}
          </div>
        ) : (
          <p className="text-xs text-slate-400 italic">No matching sources found in knowledge base.</p>
        )}
      </div>
    </div>
  );
}
