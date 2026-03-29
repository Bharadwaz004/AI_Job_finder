/**
 * API service — centralized HTTP client for backend communication.
 * All endpoints return { data, error } for uniform error handling.
 */

import axios from 'axios'

const API_BASE = import.meta.env.VITE_API_URL || '/api'

const client = axios.create({
  baseURL: API_BASE,
  timeout: 120_000, // LLM calls can be slow
  headers: { 'Content-Type': 'application/json' },
})

// ── Response interceptor for error normalization ──
client.interceptors.response.use(
  (res) => res,
  (err) => {
    const message =
      err.response?.data?.message ||
      err.response?.data?.detail ||
      err.message ||
      'Something went wrong'
    return Promise.reject({ message, status: err.response?.status })
  }
)

// ═══════════════════════════════════════
//  Resume
// ═══════════════════════════════════════

export async function uploadResume(file) {
  const form = new FormData()
  form.append('file', file)

  const { data } = await client.post('/upload-resume', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return data
}

export async function extractProfile(resumeId) {
  const { data } = await client.post(`/extract-profile?resume_id=${resumeId}`)
  return data
}

export async function getProfile(profileId) {
  const { data } = await client.get(`/profile/${profileId}`)
  return data
}

// ═══════════════════════════════════════
//  Jobs
// ═══════════════════════════════════════

export async function searchJobs({ skills, roles = [], location = '', limit = 20 }) {
  const { data } = await client.post('/jobs', { skills, roles, location, limit })
  return data
}

// ═══════════════════════════════════════
//  Ranking
// ═══════════════════════════════════════

export async function rankJobs({ profileId, jobIds = [], method = 'hybrid' }) {
  const { data } = await client.post('/rank-jobs', {
    profile_id: profileId,
    job_ids: jobIds,
    method,
  })
  return data
}

export default client
