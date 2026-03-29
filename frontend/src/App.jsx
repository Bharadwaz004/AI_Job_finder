/**
 * App — orchestrates the full resume → jobs → ranking pipeline.
 * State machine: upload → parsing → searching → ranking → results
 */

import React, { useState, useCallback } from 'react'
import Header from './components/Header'
import StepIndicator from './components/StepIndicator'
import ResumeUpload from './components/ResumeUpload'
import ProfileCard from './components/ProfileCard'
import JobResults from './components/JobResults'
import SkillGapPanel from './components/SkillGapPanel'
import ErrorBanner from './components/ErrorBanner'
import { uploadResume, extractProfile, searchJobs, rankJobs } from './services/api'

const STEPS = [
  { key: 'upload', label: 'Upload Resume' },
  { key: 'profile', label: 'AI Analysis' },
  { key: 'jobs', label: 'Find Jobs' },
  { key: 'results', label: 'Ranked Results' },
]

export default function App() {
  // ── Pipeline state ──
  const [step, setStep] = useState(0)
  const [loading, setLoading] = useState(false)
  const [loadingMsg, setLoadingMsg] = useState('')
  const [error, setError] = useState(null)

  // ── Data ──
  const [resumeId, setResumeId] = useState(null)
  const [profile, setProfile] = useState(null)
  const [profileId, setProfileId] = useState(null)
  const [jobResults, setJobResults] = useState(null)
  const [rankedJobs, setRankedJobs] = useState(null)
  const [skillGap, setSkillGap] = useState(null)
  const [rankingMethod, setRankingMethod] = useState('rule_based')

  // ── Upload handler ──
  const handleUpload = useCallback(async (file) => {
    setError(null)
    setLoading(true)
    setLoadingMsg('Uploading resume...')

    try {
      const uploadResult = await uploadResume(file)
      setResumeId(uploadResult.id)

      setLoadingMsg('AI is analyzing your resume...')
      const profileResult = await extractProfile(uploadResult.id)
      setProfile(profileResult.profile)
      setProfileId(profileResult.id)
      setStep(1)
    } catch (err) {
      setError(err.message || 'Failed to process resume')
    } finally {
      setLoading(false)
      setLoadingMsg('')
    }
  }, [])

  // ── Job search handler ──
  const handleSearchJobs = useCallback(async () => {
    if (!profile) return
    setError(null)
    setLoading(true)
    setLoadingMsg('Searching for matching jobs...')

    try {
      const results = await searchJobs({
        skills: profile.skills.slice(0, 8),
        roles: profile.suggested_roles.slice(0, 3),
        location: profile.location || '',
        limit: 20,
      })
      setJobResults(results)
      setStep(2)

      // Auto-rank with rule_based (fast, no LLM cost)
      setLoadingMsg('Scoring job matches...')
      const ranked = await rankJobs({
        profileId,
        jobIds: results.jobs.map((j) => j.id),
        method: rankingMethod,
      })
      setRankedJobs(ranked.ranked_jobs)
      setSkillGap(ranked.skill_gap_summary)
      setStep(3)
    } catch (err) {
      setError(err.message || 'Job search failed')
    } finally {
      setLoading(false)
      setLoadingMsg('')
    }
  }, [profile, profileId, rankingMethod])

  // ── Re-rank with different method ──
  const handleRerank = useCallback(async (method) => {
    if (!jobResults?.jobs?.length) return
    setRankingMethod(method)
    setLoading(true)
    setLoadingMsg(method === 'llm_based' ? 'AI is deep-scoring each job...' : 'Re-scoring...')
    setError(null)

    try {
      const ranked = await rankJobs({
        profileId,
        jobIds: jobResults.jobs.map((j) => j.id),
        method,
      })
      setRankedJobs(ranked.ranked_jobs)
      setSkillGap(ranked.skill_gap_summary)
    } catch (err) {
      setError(err.message || 'Re-ranking failed')
    } finally {
      setLoading(false)
      setLoadingMsg('')
    }
  }, [jobResults, profileId])

  // ── Reset ──
  const handleReset = () => {
    setStep(0)
    setResumeId(null)
    setProfile(null)
    setProfileId(null)
    setJobResults(null)
    setRankedJobs(null)
    setSkillGap(null)
    setError(null)
  }

  return (
    <div className="min-h-screen">
      <Header onReset={handleReset} showReset={step > 0} />

      <main className="max-w-6xl mx-auto px-4 sm:px-6 pb-20">
        {/* Progress Steps */}
        <StepIndicator steps={STEPS} current={step} />

        {/* Error Banner */}
        {error && <ErrorBanner message={error} onDismiss={() => setError(null)} />}

        {/* Loading Overlay */}
        {loading && (
          <div className="flex flex-col items-center justify-center py-16 gap-4 animate-fade-in">
            <div className="relative">
              <div className="w-12 h-12 rounded-full border-2 border-accent/30 border-t-accent animate-spin" />
              <div className="absolute inset-0 w-12 h-12 rounded-full border-2 border-transparent border-b-mint/40 animate-spin" style={{ animationDuration: '1.5s', animationDirection: 'reverse' }} />
            </div>
            <p className="text-surface-200 text-sm font-medium animate-pulse-soft">
              {loadingMsg}
            </p>
          </div>
        )}

        {/* Step 0: Upload */}
        {!loading && step === 0 && (
          <ResumeUpload onUpload={handleUpload} />
        )}

        {/* Step 1: Profile Review */}
        {!loading && step >= 1 && profile && (
          <ProfileCard
            profile={profile}
            onSearchJobs={handleSearchJobs}
            showSearchButton={step === 1}
          />
        )}

        {/* Step 3: Ranked Results */}
        {!loading && step >= 3 && rankedJobs && (
          <>
            <JobResults
              jobs={rankedJobs}
              method={rankingMethod}
              onRerank={handleRerank}
              totalFound={jobResults?.total}
            />
            {skillGap && <SkillGapPanel data={skillGap} />}
          </>
        )}
      </main>

      {/* Footer */}
      <footer className="border-t border-white/[0.04] py-6 text-center text-xs text-surface-200/40">
        ResumeMatch AI — Built with FastAPI, React &amp; LLM intelligence
      </footer>
    </div>
  )
}
