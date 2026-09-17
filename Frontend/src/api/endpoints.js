import client from './client'

/** Turn a filter object into a query string, dropping empty values so the
 *  API never sees `?status=&search=`. */
function query(params = {}) {
  const search = new URLSearchParams()
  Object.entries(params).forEach(([key, value]) => {
    if (value === '' || value === null || value === undefined) return
    search.append(key, Array.isArray(value) ? value.join(',') : value)
  })
  const string = search.toString()
  return string ? `?${string}` : ''
}

export const auth = {
  register: (payload) => client.post('/auth/register/', payload),
  login: (payload) => client.post('/auth/login/', payload),
  me: () => client.get('/auth/me/'),
  updateMe: (payload) => client.patch('/auth/me/', payload),
  profile: () => client.get('/auth/profile/'),
  updateProfile: (payload) => client.patch('/auth/profile/', payload),
  settings: () => client.get('/auth/settings/'),
  updateSettings: (payload) => client.patch('/auth/settings/', payload),
  changePassword: (payload) => client.post('/auth/change-password/', payload),
}

export const jobs = {
  list: (params) => client.get(`/jobs/${query(params)}`),
  get: (id) => client.get(`/jobs/${id}/`),
  create: (payload) => client.post('/jobs/', payload),
  update: (id, payload) => client.patch(`/jobs/${id}/`, payload),
  remove: (id) => client.delete(`/jobs/${id}/`),
  setStatus: (id, payload) => client.post(`/jobs/${id}/status/`, payload),
  toggleFavourite: (id) => client.post(`/jobs/${id}/favourite/`),
  matches: (params) => client.get(`/jobs/matches/${query(params)}`),
  options: () => client.get('/jobs/options/'),
}

export const resumes = {
  list: () => client.get('/resumes/'),
  create: (formData) => client.post('/resumes/', formData),
  update: (id, payload) => client.patch(`/resumes/${id}/`, payload),
  remove: (id) => client.delete(`/resumes/${id}/`),
  setDefault: (id) => client.post(`/resumes/${id}/set-default/`),
}

export const applications = {
  list: (params) => client.get(`/applications/${query(params)}`),
  get: (id) => client.get(`/applications/${id}/`),
  update: (id, payload) => client.patch(`/applications/${id}/`, payload),
  remove: (id) => client.delete(`/applications/${id}/`),
  quickApply: (payload) => client.post('/applications/quick-apply/', payload),
  markSubmitted: (id) => client.post(`/applications/${id}/mark-submitted/`),
}

export const reminders = {
  list: (params) => client.get(`/reminders/${query(params)}`),
  create: (payload) => client.post('/reminders/', payload),
  update: (id, payload) => client.patch(`/reminders/${id}/`, payload),
  remove: (id) => client.delete(`/reminders/${id}/`),
  complete: (id) => client.post(`/reminders/${id}/complete/`),
  reopen: (id) => client.post(`/reminders/${id}/reopen/`),
  upcoming: (params) => client.get(`/reminders/upcoming/${query(params)}`),
}

export const automation = {
  runs: (params) => client.get(`/automation/runs/${query(params)}`),
  run: (id) => client.get(`/automation/runs/${id}/`),
  start: (payload) => client.post('/automation/runs/start/', payload),
  cancel: (id) => client.post(`/automation/runs/${id}/cancel/`),
  preflight: (url) => client.get(`/automation/runs/preflight/${query({ url })}`),
  sites: () => client.get('/automation/sites/'),
}

export const analytics = {
  dashboard: (params) => client.get(`/analytics/dashboard/${query(params)}`),
  summary: () => client.get('/analytics/summary/'),
  timeline: (params) => client.get(`/analytics/timeline/${query(params)}`),
  statusTimeline: (params) => client.get(`/analytics/status-timeline/${query(params)}`),
  breakdowns: () => client.get('/analytics/breakdowns/'),
  funnel: () => client.get('/analytics/funnel/'),
}
