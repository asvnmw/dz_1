import http from 'k6/http';
import { check } from 'k6';

const BASE_URL = __ENV.BASE_URL || 'http://127.0.0.1:8000';

export const options = {
  scenarios: {
    heavy: {
      executor: 'ramping-arrival-rate',
      startRate: 1,
      timeUnit: '1s',
      preAllocatedVUs: 20,
      maxVUs: 100,
      stages: [
        { target: 1, duration: '30s' },
        { target: 2, duration: '30s' },
        { target: 4, duration: '30s' },
        { target: 8, duration: '30s' },
        { target: 16, duration: '30s' },
      ],
    },
  },
  thresholds: {
    http_req_duration: ['p(95)<500'],
    http_req_failed: ['rate<0.01'],
  },
};

export default function () {
  const loginRes = http.post(`${BASE_URL}/auth/login`, JSON.stringify({
    username: 'demo', password: 'demo',
  }), { headers: { 'Content-Type': 'application/json' } });

  if (loginRes.status !== 200) return;

  const res = http.get(`${BASE_URL}/api/summary`);

  check(res, { 'summary status 200': (r) => r.status === 200 });
}