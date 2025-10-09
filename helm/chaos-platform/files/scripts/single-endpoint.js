import http from 'k6/http';
import { check, fail, sleep } from 'k6';

export let options = {
    vus: __ENV.CHAOS_K6_VUS ? parseInt(__ENV.CHAOS_K6_VUS) : 1,
    duration: __ENV.CHAOS_K6_DURATION || '10s',
};

export default function () {
    const url = __ENV.CHAOS_K6_URL;
    if (!url) {
        fail("❌ No CHAOS_K6_URL provided");
    }

    const method = __ENV.CHAOS_K6_METHOD || "GET";
    const body = __ENV.CHAOS_K6_BODY || null;

    // 🔑 Always fetch the token fresh for each iteration
    const token = __ENV.CHAOS_K6_LOGIN_TOKEN;
    let params = { headers: {} };

    if (token) {
        params.headers['Cookie'] = `login_token=${token}`;
        console.log(`🔑 Using JWT token: ${token}`); 
    }

    if (__ENV.CHAOS_K6_HEADERS) {
        try {
            const extraHeaders = JSON.parse(__ENV.CHAOS_K6_HEADERS);
            Object.assign(params.headers, extraHeaders);
        } catch (err) {
            fail("❌ Invalid CHAOS_K6_HEADERS JSON: " + err.message);
        }
    }

    let res;
    if (method === "POST") {
        if (!params.headers['Content-Type']) {
            params.headers['Content-Type'] = 'application/x-www-form-urlencoded';
        }
        res = http.post(url, body, params);
    } else {
        res = http.get(url, params);
    }

    const success = check(res, {
        "status is 200": (r) => r.status === 200,
        "response < 5s": (r) => r.timings.duration < 5000,
    });

    if (!success) {
        console.error(`⚠️ Request failed:
  URL: ${url}
  Status: ${res.status}
  Body: ${res.body ? res.body.substring(0, 200) : "empty"}...`);
    } else {
        console.log(`✅ Success:
  URL: ${url}
  Status: ${res.status}`);
    }

    sleep(1); // ✅ wait 1s between requests like your other script
}
