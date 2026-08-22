import React, { useState, useRef } from 'react';
import { Upload, FileText, Check, AlertCircle, Loader2 } from 'lucide-react';

export default function FileUploadCard({ title, endpoint, icon: Icon, sourceKey, onUploadSuccess }) {
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [successInfo, setSuccessInfo] = useState(null);
  const [errorMsg, setErrorMsg] = useState('');
  const fileInputRef = useRef(null);

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    if (!selectedFile) return;

    if (!selectedFile.name.toLowerCase().endsWith('.pdf')) {
      setErrorMsg('Only PDF files are accepted. Please upload a .pdf file.');
      setFile(null);
      return;
    }

    setErrorMsg('');
    setSuccessInfo(null);
    setFile(selectedFile);
  };

  const handleUpload = async () => {
    if (!file) {
      setErrorMsg('Please select a PDF file first.');
      return;
    }

    setUploading(true);
    setErrorMsg('');
    setSuccessInfo(null);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch(endpoint, {
        method: 'POST',
        body: formData,
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || `Upload failed with status ${response.status}`);
      }

      setSuccessInfo(data);
      if (onUploadSuccess) {
        onUploadSuccess(sourceKey, data);
      }
    } catch (err) {
      console.error(`Upload error for ${title}:`, err);
      setErrorMsg(err.message || 'Failed to upload document. Please check server availability.');
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-xs flex flex-col justify-between hover:border-slate-300 transition-colors">
      <div>
        <div className="flex items-center gap-2 mb-3">
          <Icon className="w-4 h-4 text-blue-600" />
          <h3 className="font-semibold text-slate-900 text-sm">{title}</h3>
        </div>

        {/* Dropzone Area */}
        <div
          onClick={() => fileInputRef.current?.click()}
          className={`border border-dashed rounded-lg p-4 text-center cursor-pointer transition-colors ${
            file
              ? 'border-blue-300 bg-blue-50/50'
              : 'border-slate-200 hover:border-slate-300 bg-slate-50/50 hover:bg-slate-50'
          }`}
        >
          <input
            type="file"
            ref={fileInputRef}
            onChange={handleFileChange}
            accept=".pdf,application/pdf"
            className="hidden"
          />

          {file ? (
            <div className="flex items-center justify-center gap-2 text-slate-800">
              <FileText className="w-4 h-4 text-blue-600 shrink-0" />
              <span className="text-xs font-medium truncate max-w-[200px]">{file.name}</span>
            </div>
          ) : (
            <div className="flex items-center justify-center gap-2 text-slate-500 py-1">
              <Upload className="w-4 h-4 text-slate-400" />
              <span className="text-xs font-medium">Upload {title} PDF</span>
            </div>
          )}
        </div>

        {/* Error notification */}
        {errorMsg && (
          <div className="mt-3 p-2.5 rounded-lg bg-rose-50 border border-rose-200 text-rose-700 text-xs flex items-start gap-2">
            <AlertCircle className="w-4 h-4 text-rose-500 shrink-0 mt-0.5" />
            <span>{errorMsg}</span>
          </div>
        )}

        {/* Success information */}
        {successInfo && (
          <div className="mt-3 p-3 rounded-lg bg-slate-50 border border-slate-200 text-xs space-y-1">
            <div className="flex items-center gap-1.5 text-emerald-700 font-medium">
              <Check className="w-3.5 h-3.5 text-emerald-600" />
              <span>{title} uploaded</span>
            </div>
            <p className="text-slate-600 pl-5">✓ {successInfo.new_chunks} sections processed</p>
            <p className="text-slate-600 pl-5">✓ Knowledge base updated ({successInfo.vectors_indexed} vectors)</p>
          </div>
        )}
      </div>

      <button
        onClick={handleUpload}
        disabled={!file || uploading}
        className={`mt-4 w-full py-2 px-3 rounded-lg font-medium text-xs flex items-center justify-center gap-2 transition-colors ${
          uploading
            ? 'bg-blue-100 text-blue-500 cursor-not-allowed'
            : file
            ? 'bg-blue-600 hover:bg-blue-700 text-white shadow-xs'
            : 'bg-slate-100 text-slate-400 cursor-not-allowed'
        }`}
      >
        {uploading ? (
          <>
            <Loader2 className="w-3.5 h-3.5 animate-spin text-blue-600" />
            <span>Processing Document...</span>
          </>
        ) : (
          <span>Upload PDF</span>
        )}
      </button>
    </div>
  );
}
