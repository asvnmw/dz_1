import http from 'k6/http';
import { check } from 'k6';
import { Rate } from 'k6/metrics';

const BASE_URL = __ENV.BASE_URL || 'http://127.0.0.1:8000';
const RATE = parseInt(__ENV.RATE || '1');
const DURATION = __ENV.DURATION || '30s';
const errorRate = new Rate('errors');

export const options = {
  setupTimeout: '120s',
  scenarios: {
    heavy: {
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

export function setup() {
  const jar = http.cookieJar();
  const loginRes = http.post(`${BASE_URL}/auth/login`, JSON.stringify({
    username: 'demo', password: 'demo',
  }), { headers: { 'Content-Type': 'application/json' }, jar });

  if (loginRes.status !== 200) {
    throw new Error(`Login failed! Status: ${loginRes.status}`);
  }
  return { jar };
}

export default function (data) {
  const jar = data.jar;
  const res = http.get(`${BASE_URL}/api/summary`, { jar });
  check(res, { 'status 200': (r) => r.status === 200 });
  errorRate.add(res.status >= 500 ? 1 : 0);
}