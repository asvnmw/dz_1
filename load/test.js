import http from 'k6/http';
import { check } from 'k6';
import { Rate } from 'k6/metrics';

const BASE_URL = __ENV.BASE_URL || 'http://127.0.0.1:8000';
const errorRate = new Rate('errors');

const WEIGHTS = {
  'GET /api/loans': 35,
  'GET /api/loans?only_active=true': 20,
  'GET /api/loans/{id}': 20,
  'GET /api/books': 10,
  'GET /api/readers': 5,
  'GET /api/summary': 10,
};

export const options = {
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
    http_req_failed: ['rate<0.01'],
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

export default function () {
  const jar = http.cookieJar();

  const loginRes = http.post(`${BASE_URL}/auth/login`, JSON.stringify({
    username: 'demo',
    password: 'demo',
  }), { headers: { 'Content-Type': 'application/json' }, jar });

  if (loginRes.status !== 200) {
    errorRate.add(1);
    return;
  }

  const loansRes = http.get(`${BASE_URL}/api/loans?page=1&size=1`, { jar });
  let loanId = 1;
  if (loansRes.status === 200) {
    const data = loansRes.json();
    if (data.items && data.items.length > 0) {
      loanId = data.items[0].id;
    }
  }

  const op = pickOperation();
  let res;

  if (op === 'GET /api/loans') {
    res = http.get(`${BASE_URL}/api/loans?page=1&size=20`, { jar });
  } else if (op === 'GET /api/loans?only_active=true') {
    res = http.get(`${BASE_URL}/api/loans?only_active=true`, { jar });
  } else if (op === 'GET /api/loans/{id}') {
    res = http.get(`${BASE_URL}/api/loans/${loanId}`, { jar });
  } else if (op === 'GET /api/books') {
    res = http.get(`${BASE_URL}/api/books?page=1&size=20`, { jar });
  } else if (op === 'GET /api/readers') {
    res = http.get(`${BASE_URL}/api/readers?page=1&size=20`, { jar });
  } else if (op === 'GET /api/summary') {
    res = http.get(`${BASE_URL}/api/summary`, { jar });
  }

  check(res, { 'status 200': (r) => r.status === 200 });
  errorRate.add(res.status >= 500 ? 1 : 0);
}