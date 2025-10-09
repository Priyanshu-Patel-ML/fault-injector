import http from 'k6/http';
import { check, sleep } from 'k6';
 
export let options = {
    stages: [
        { duration: '30s', target: 30 },   // Start at 30
        { duration: '1m', target: 50 },    // Ramp to 50
        { duration: '1m', target: 35 },    // Drop to 35
        { duration: '1m', target: 45 },    // Up to 45
        { duration: '1m', target: 32 },    // Down to 32
        { duration: '1m', target: 48 },    // Up to 48
        { duration: '1m', target: 38 },    // Down to 38
        { duration: '1m', target: 42 },    // Up to 42
        { duration: '1m', target: 33 },    // Continue pattern...
        { duration: '1m', target: 47 },
        { duration: '1m', target: 36 },
        { duration: '1m', target: 44 },
        { duration: '2m', target: 40 },
        { duration: '2m', target: 42 },
        { duration: '2m', target: 40 },
        { duration: '2m', target: 45 },
        { duration: '2m', target: 42 },
        { duration: '2m', target: 33 },
        { duration: '2m', target: 36 },
        { duration: '2m', target: 39 },
        { duration: '3m', target: 40 },   // Long final stage
    ],
    thresholds: {
        http_req_duration: ['p(95)<5000'],
        http_req_failed: ['rate<0.1'],
    },
};
 
const endpoints = [
    {
        url: 'http://4.154.253.199:8080/api/post/compose',
        method: 'POST',
        body: 'post_type=0&text=Continuous load test message',
        weight: 40
    },
    {
        url: 'http://4.154.253.199:8080/api/user-timeline/read?start=0&stop=100',
        method: 'GET',
        weight: 60
    }
];
 
export default function () {
    const token = __ENV.CHAOS_K6_LOGIN_TOKEN;
    let params = {
        headers: {
            'Cookie': `login_token=${token}`,
            'Content-Type': 'application/x-www-form-urlencoded'
        }
    };
 
    // Weighted random endpoint selection
    const rand = Math.random() * 100;
    const endpoint = rand < 40 ? endpoints[0] : endpoints[1];
 
    let response;
    if (endpoint.method === 'POST') {
        response = http.post(endpoint.url, endpoint.body, params);
    } else {
        response = http.get(endpoint.url, params);
    }
 
    check(response, {
        'status is 200': (r) => r.status === 200,
        'response time < 5s': (r) => r.timings.duration < 5000,
    });
 
    sleep(1); // 1 second between requests
}