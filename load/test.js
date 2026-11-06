import http from 'k6/http';
import { check } from 'k6';
import { Rate } from 'k6/metrics';

const BASE_URL = __ENV.BASE_URL || 'http://127.0.0.1:8000';
const errorRate = new Rate('errors');

const WEIGHTS = {
  'GET /api/loans': 30,
  'GET /api/loans?only_active=true': 15,
  'GET /api/loans/{id}': 15,
  'GET /api/books': 10,
  'GET /api/readers': 5,
  'GET /api/summary': 10,
  'POST /api/loans': 10,
  'POST /api/loans/{id}/return': 5,
};

export const options = {
  setupTimeout: '120s',
  scenarios: {
    mixed: {
      executor: 'ramping-arrival-rate',
      startRate: 1,
      timeUnit: '1s',
      preAllocatedVUs: 100,
      maxVUs: 500,
      stages: [
        { target: 1, duration: '30s' },
        { target: 2, duration: '30s' },
        { target: 4, duration: '30s' },
        { target: 8, duration: '30s' },
        { target: 16, duration: '30s' },
        { target: 32, duration: '30s' },
        { target: 64, duration: '30s' },
        { target: 128, duration: '30s' },
        { target: 256, duration: '30s' },
        { target: 512, duration: '30s' },
      ],
    },
  },
  thresholds: {
    http_req_duration: ['p(95)<500'],
    errors: ['rate<0.01'],
    // http_req_failed УБРАН из порогов — потому что 409 ожидаемы
  },
};

function pickOperation() {
  const total = Object.values(WEIGHTS).reduce((a, b) => a + b, 0);
  let r = Math.random() * total;
  for (const [op, weight] of Object.entries(WEIGHTS)) {
    r -= weight;
    if (r <= 0) return op;
  }
  return 'GET /api/loans';
}

export function setup() {
  const jar = http.cookieJar();
  const loginRes = http.post(`${BASE_URL}/auth/login`, JSON.stringify({
    username: 'demo', password: 'demo',
  }), { headers: { 'Content-Type': 'application/json' }, jar });

  if (loginRes.status !== 200) {
    return { readerId: null, loanId: null };
  }

  const loansRes = http.get(`${BASE_URL}/api/loans?page=1&size=1`, { jar });
  let loanId = null;
  if (loansRes.status === 200) {
    const data = loansRes.json();
    if (data.items && data.items.length > 0) {
      loanId = data.items[0].id;
    }
  }

  const readersRes = http.get(`${BASE_URL}/api/readers?page=1&size=1`, { jar });
  let readerId = null;
  if (readersRes.status === 200) {
    const data = readersRes.json();
    if (data.items && data.items.length > 0) {
      readerId = data.items[0].id;
    }
  }

  return { readerId, loanId };
}

export default function (data) {
  const jar = http.cookieJar();

  const loginRes = http.post(`${BASE_URL}/auth/login`, JSON.stringify({
    username: 'demo', password: 'demo',
  }), { headers: { 'Content-Type': 'application/json' }, jar });

  if (loginRes.status !== 200) {
    errorRate.add(1);
    return;
  }

  const op = pickOperation();
  let res;

  if (op === 'GET /api/loans') {
    res = http.get(`${BASE_URL}/api/loans?page=1&size=20`, { jar });
    check(res, { 'status 200': (r) => r.status === 200 });
    errorRate.add(res.status >= 500 ? 1 : 0);
  } else if (op === 'GET /api/loans?only_active=true') {
    res = http.get(`${BASE_URL}/api/loans?only_active=true`, { jar });
    check(res, { 'status 200': (r) => r.status === 200 });
    errorRate.add(res.status >= 500 ? 1 : 0);
  } else if (op === 'GET /api/loans/{id}') {
    const id = data.loanId || 1;
    res = http.get(`${BASE_URL}/api/loans/${id}`, { jar });
    check(res, { 'status 200': (r) => r.status === 200 });
    errorRate.add(res.status >= 500 ? 1 : 0);
  } else if (op === 'GET /api/books') {
    res = http.get(`${BASE_URL}/api/books?page=1&size=20`, { jar });
    check(res, { 'status 200': (r) => r.status === 200 });
    errorRate.add(res.status >= 500 ? 1 : 0);
  } else if (op === 'GET /api/readers') {
    res = http.get(`${BASE_URL}/api/readers?page=1&size=20`, { jar });
    check(res, { 'status 200': (r) => r.status === 200 });
    errorRate.add(res.status >= 500 ? 1 : 0);
  } else if (op === 'GET /api/summary') {
    res = http.get(`${BASE_URL}/api/summary`, { jar });
    check(res, { 'status 200': (r) => r.status === 200 });
    errorRate.add(res.status >= 500 ? 1 : 0);
  } else if (op === 'POST /api/loans') {
    res = http.post(`${BASE_URL}/api/loans`, JSON.stringify({
      reader_id: data.readerId || 1,
      copy_id: 107878,
      due_at: '2026-12-31',
    }), { headers: { 'Content-Type': 'application/json' }, jar });
    check(res, { 'created or conflict': (r) => r.status === 201 || r.status === 409 });
    errorRate.add(res.status >= 500 ? 1 : 0);
  } else if (op === 'POST /api/loans/{id}/return') {
    const id = data.loanId || 1;
    res = http.post(`${BASE_URL}/api/loans/${id}/return`, JSON.stringify({
      returned_at: '2026-12-31',
    }), { headers: { 'Content-Type': 'application/json' }, jar });
    check(res, { 'returned or conflict': (r) => r.status === 200 || r.status === 409 });
    errorRate.add(res.status >= 500 ? 1 : 0);
  }
}