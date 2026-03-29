import React, { useCallback, useState } from 'react'
import { useDropzone } from 'react-dropzone'
import { Upload, FileText, AlertCircle } from 'lucide-react'

const MAX_SIZE = 10 * 1024 * 1024 // 10MB
const ACCEPTED = {
  'application/pdf': ['.pdf'],
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
}

export default function ResumeUpload({ onUpload }) {
  const [fileError, setFileError] = useState(null)
  const [selectedFile, setSelectedFile] = useState(null)

  const onDrop = useCallback(
    (accepted, rejected) => {
      setFileError(null)

      if (rejected.length > 0) {
        const err = rejected[0].errors[0]
        if (err.code === 'file-too-large') {
          setFileError('File exceeds 10MB limit')
        } else if (err.code === 'file-invalid-type') {
          setFileError('Only PDF and DOCX files are accepted')
        } else {
          setFileError(err.message)
        }
        return
      }

      if (accepted.length > 0) {
        setSelectedFile(accepted[0])
      }
    },
    []
  )

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: ACCEPTED,
    maxSize: MAX_SIZE,
    maxFiles: 1,
    multiple: false,
  })

  const handleSubmit = () => {
    if (selectedFile) {
      onUpload(selectedFile)
    }
  }

  return (
    <div className="max-w-xl mx-auto animate-fade-in">
      {/* Hero text */}
      <div className="text-center mb-10">
        <h2 className="font-display text-3xl sm:text-4xl font-semibold text-white mb-3 tracking-tight">
          Drop your resume,<br />
          <span className="text-accent-light">find your match.</span>
        </h2>
        <p className="text-surface-200/60 text-sm max-w-md mx-auto leading-relaxed">
          Our AI parses your resume, finds relevant jobs, and scores each one
          so you know exactly where you stand.
        </p>
      </div>

      {/* Dropzone */}
      <div
        {...getRootProps()}
        className={`
          relative glass-card p-10 text-center cursor-pointer
          transition-all duration-300 group
          ${isDragActive ? 'border-accent/50 bg-accent/[0.04] scale-[1.01]' : 'hover:border-white/[0.12]'}
          ${selectedFile ? 'border-mint/30 bg-mint/[0.03]' : ''}
        `}
      >
        <input {...getInputProps()} />

        <div className="flex flex-col items-center gap-4">
          {selectedFile ? (
            <>
              <div className="w-14 h-14 rounded-2xl bg-mint/10 flex items-center justify-center">
                <FileText size={24} className="text-mint-light" />
              </div>
              <div>
                <p className="text-white font-medium text-sm">{selectedFile.name}</p>
                <p className="text-surface-200/50 text-xs mt-1">
                  {(selectedFile.size / 1024).toFixed(0)} KB — Ready to analyze
                </p>
              </div>
            </>
          ) : (
            <>
              <div className={`
                w-14 h-14 rounded-2xl flex items-center justify-center transition-colors
                ${isDragActive ? 'bg-accent/20' : 'bg-white/[0.04] group-hover:bg-white/[0.06]'}
              `}>
                <Upload
                  size={24}
                  className={`transition-colors ${isDragActive ? 'text-accent-light' : 'text-surface-200/60'}`}
                />
              </div>
              <div>
                <p className="text-white/80 text-sm font-medium">
                  {isDragActive ? 'Drop it here!' : 'Drag & drop your resume'}
                </p>
                <p className="text-surface-200/40 text-xs mt-1">
                  PDF or DOCX up to 10MB
                </p>
              </div>
            </>
          )}
        </div>

        {/* Animated border glow on drag */}
        {isDragActive && (
          <div className="absolute inset-0 rounded-2xl glow-accent pointer-events-none" />
        )}
      </div>

      {/* Error */}
      {fileError && (
        <div className="mt-4 flex items-center gap-2 text-rose-400 text-xs">
          <AlertCircle size={14} />
          {fileError}
        </div>
      )}

      {/* Submit button */}
      {selectedFile && (
        <div className="mt-6 flex justify-center animate-slide-up">
          <button onClick={handleSubmit} className="btn-primary px-8">
            Analyze Resume
          </button>
        </div>
      )}
    </div>
  )
}
