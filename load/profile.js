import http from 'k6/http';
import { check } from 'k6';

const BASE_URL = __ENV.BASE_URL || 'http://127.0.0.1:8000';

export const options = {
  scenarios: {
    profile: {
      executor: 'constant-arrival-rate',
      rate: 74,               // 74 зап/с — предел тяжёлой операции
      timeUnit: '1s',
      duration: '60s',        // ровно 60 секунд
      preAllocatedVUs: 100,
      maxVUs: 500,
    },
  },
  thresholds: {
    http_req_duration: ['p(95)<5000'],
  },
};

export default function () {
  const jar = http.cookieJar();

  const loginRes = http.post(`${BASE_URL}/auth/login`, JSON.stringify({
    username: 'demo', password: 'demo',
  }), { headers: { 'Content-Type': 'application/json' }, jar });

  if (loginRes.status !== 200) return;

  const res = http.get(`${BASE_URL}/api/summary`, { jar });

  check(res, { 'summary status 200': (r) => r.status === 200 });
}