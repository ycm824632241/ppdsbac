import axios from 'axios'
const http = axios.create({ baseURL: '/api', timeout: 60000 })

export const setupApi = {
  globalSetup: ()    => http.post('/setup/global'),
  raSetup:     ()    => http.post('/setup/ra'),
  taSetup:     ()    => http.post('/setup/ta'),
  aaSetup:     (n)   => http.post('/setup/aa',     { n }),
  userSetup:   (id)  => http.post('/setup/user',   { user_id: id }),
  regist:      (id)  => http.post('/setup/regist', { user_id: id }),
  state:       ()    => http.get('/setup/state'),
}

export const workflowApi = {
  pseudonym: (id)  => http.post('/workflow/pseudonym', { user_id: id }),
  enc:       (d)   => http.post('/workflow/enc',       d),
  accReq:    (d)   => http.post('/workflow/acc_req',   d),
  accAgg:    (id)  => http.post('/workflow/acc_agg',   { user_id: id }),
  dec:       (d)   => http.post('/workflow/dec',       d),
  trace:     (id)  => http.post('/workflow/trace',     { user_id: id }),
  fullDemo:  (d)   => http.post('/workflow/full_demo', d),
}

export const benchApi    = { run: () => http.post('/bench/run') }
export const securityApi = {
  unlinkability:  () => http.post('/security/unlinkability'),
  unforgeability: () => http.post('/security/unforgeability'),
}
