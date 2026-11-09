import http from 'k6/http';
import { check } from 'k6';
import { Rate } from 'k6/metrics';

const BASE_URL = __ENV.BASE_URL || 'http://127.0.0.1:8000';
const RATE = parseInt(__ENV.RATE || '1');
const DURATION = __ENV.DURATION || '30s';
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
    step: {
      executor: 'constant-arrival-rate',
      rate: RATE,
      timeUnit: '1s',
      duration: DURATION,
      preAllocatedVUs: Math.max(50, RATE * 2),
      maxVUs: Math.max(200, RATE * 4),
    },
  },
  thresholds: {
    http_req_duration: ['p(95)<500'],
    errors: ['rate<0.01'],
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
    throw new Error(`Login failed! Status: ${loginRes.status}`);
  }

  let loanId = null;
  const loansRes = http.get(`${BASE_URL}/api/loans?page=1&size=1`, { jar });
  if (loansRes.status === 200) {
    const data = loansRes.json();
    if (data.items && data.items.length > 0) loanId = data.items[0].id;
  }

  let readerId = null;
  const readersRes = http.get(`${BASE_URL}/api/readers?page=1&size=1`, { jar });
  if (readersRes.status === 200) {
    const data = readersRes.json();
    if (data.items && data.items.length > 0) readerId = data.items[0].id;
  }

  let copyIds = [];
  for (let i = 0; i < 100; i++) {
    copyIds.push(Math.floor(Math.random() * 50000) + 1);
  }

  const cookies = jar.cookiesForURL(BASE_URL);
  return { readerId, loanId, copyIds, cookies };
}

export default function (data) {
  const jar = http.cookieJar();
  for (const [name, value] of Object.entries(data.cookies)) {
    jar.set(BASE_URL, name, value[0]);
  }

  const op = pickOperation();
  let res;

  if (op === 'GET /api/loans') {
    res = http.get(`${BASE_URL}/api/loans?page=1&size=20`, { jar });
    check(res, { 'status 200': (r) => r.status === 200 });
  } else if (op === 'GET /api/loans?only_active=true') {
    res = http.get(`${BASE_URL}/api/loans?only_active=true`, { jar });
    check(res, { 'status 200': (r) => r.status === 200 });
  } else if (op === 'GET /api/loans/{id}') {
    res = http.get(`${BASE_URL}/api/loans/${data.loanId || 1}`, { jar });
    check(res, { 'status 200': (r) => r.status === 200 });
  } else if (op === 'GET /api/books') {
    res = http.get(`${BASE_URL}/api/books?page=1&size=20`, { jar });
    check(res, { 'status 200': (r) => r.status === 200 });
  } else if (op === 'GET /api/readers') {
    res = http.get(`${BASE_URL}/api/readers?page=1&size=20`, { jar });
    check(res, { 'status 200': (r) => r.status === 200 });
  } else if (op === 'GET /api/summary') {
    res = http.get(`${BASE_URL}/api/summary`, { jar });
    check(res, { 'status 200': (r) => r.status === 200 });
  } else if (op === 'POST /api/loans') {
    const randomCopyId = data.copyIds[Math.floor(Math.random() * data.copyIds.length)];
    res = http.post(`${BASE_URL}/api/loans`, JSON.stringify({
      reader_id: data.readerId || 1,
      copy_id: randomCopyId,
      due_at: '2026-12-31',
    }), { headers: { 'Content-Type': 'application/json' }, jar });
    check(res, { 'created, conflict or not found': (r) => r.status === 201 || r.status === 409 || r.status === 404 });
  } else if (op === 'POST /api/loans/{id}/return') {
    res = http.post(`${BASE_URL}/api/loans/${data.loanId || 1}/return`, JSON.stringify({
      returned_at: '2026-12-31',
    }), { headers: { 'Content-Type': 'application/json' }, jar });
    check(res, { 'returned or conflict': (r) => r.status === 200 || r.status === 409 });
  }
  
  errorRate.add(res.status >= 500 ? 1 : 0);
}