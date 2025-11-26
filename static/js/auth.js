// Auth utility functions

// Hash password using SHA256. Use SubtleCrypto when available; otherwise fall back to a
// compact JS implementation. This ensures `crypto`-missing environments still work.
async function hashPassword(password) {
    const subtle = (window.crypto && window.crypto.subtle) || (window.msCrypto && window.msCrypto.subtle) || null;

    if (subtle) {
        const encoder = new TextEncoder();
        const data = encoder.encode(password);
        const hashBuffer = await subtle.digest('SHA-256', data);
        const hashArray = Array.from(new Uint8Array(hashBuffer));
        const hashHex = hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
        return hashHex;
    }

    console.warn('SubtleCrypto not available — using JS SHA-256 fallback');
    return sha256Hex(password);
}

// Compact SHA-256 fallback (pure JS). Returns hex string.
// Source: small public-domain style implementation adapted for brevity.
function sha256Hex(ascii) {
    function rightRotate(n, x) { return (x >>> n) | (x << (32 - n)); }
    const K = [
        0x428a2f98,0x71374491,0xb5c0fbcf,0xe9b5dba5,0x3956c25b,0x59f111f1,0x923f82a4,0xab1c5ed5,
        0xd807aa98,0x12835b01,0x243185be,0x550c7dc3,0x72be5d74,0x80deb1fe,0x9bdc06a7,0xc19bf174,
        0xe49b69c1,0xefbe4786,0x0fc19dc6,0x240ca1cc,0x2de92c6f,0x4a7484aa,0x5cb0a9dc,0x76f988da,
        0x983e5152,0xa831c66d,0xb00327c8,0xbf597fc7,0xc6e00bf3,0xd5a79147,0x06ca6351,0x14292967,
        0x27b70a85,0x2e1b2138,0x4d2c6dfc,0x53380d13,0x650a7354,0x766a0abb,0x81c2c92e,0x92722c85,
        0xa2bfe8a1,0xa81a664b,0xc24b8b70,0xc76c51a3,0xd192e819,0xd6990624,0xf40e3585,0x106aa070,
        0x19a4c116,0x1e376c08,0x2748774c,0x34b0bcb5,0x391c0cb3,0x4ed8aa4a,0x5b9cca4f,0x682e6ff3,
        0x748f82ee,0x78a5636f,0x84c87814,0x8cc70208,0x90befffa,0xa4506ceb,0xbef9a3f7,0xc67178f2
    ];

    let h0 = 0x6a09e667, h1 = 0xbb67ae85, h2 = 0x3c6ef372, h3 = 0xa54ff53a,
        h4 = 0x510e527f, h5 = 0x9b05688c, h6 = 0x1f83d9ab, h7 = 0x5be0cd19;

    const msg = unescape(encodeURIComponent(ascii)); // utf8
    const msgLen = msg.length;
    const words = [];
    for (let i = 0; i < msgLen; i++) words[i >> 2] |= msg.charCodeAt(i) << (24 - (i % 4) * 8);
    words[msgLen >> 2] |= 0x80 << (24 - (msgLen % 4) * 8);
    words[(((msgLen + 8) >> 6) << 4) + 15] = msgLen * 8;

    for (let i = 0; i < words.length; i += 16) {
        const w = words.slice(i, i + 16);
        const W = new Array(64);
        for (let t = 0; t < 16; t++) W[t] = w[t] | 0;
        for (let t = 16; t < 64; t++) {
            const s0 = (rightRotate(7, W[t-15]) ^ rightRotate(18, W[t-15]) ^ (W[t-15] >>> 3)) >>> 0;
            const s1 = (rightRotate(17, W[t-2]) ^ rightRotate(19, W[t-2]) ^ (W[t-2] >>> 10)) >>> 0;
            W[t] = (W[t-16] + s0 + W[t-7] + s1) >>> 0;
        }

        let a = h0, b = h1, c = h2, d = h3, e = h4, f = h5, g = h6, h = h7;
        for (let t = 0; t < 64; t++) {
            const S1 = (rightRotate(6, e) ^ rightRotate(11, e) ^ rightRotate(25, e)) >>> 0;
            const ch = ((e & f) ^ (~e & g)) >>> 0;
            const temp1 = (h + S1 + ch + K[t] + W[t]) >>> 0;
            const S0 = (rightRotate(2, a) ^ rightRotate(13, a) ^ rightRotate(22, a)) >>> 0;
            const maj = ((a & b) ^ (a & c) ^ (b & c)) >>> 0;
            const temp2 = (S0 + maj) >>> 0;

            h = g;
            g = f;
            f = e;
            e = (d + temp1) >>> 0;
            d = c;
            c = b;
            b = a;
            a = (temp1 + temp2) >>> 0;
        }

        h0 = (h0 + a) >>> 0;
        h1 = (h1 + b) >>> 0;
        h2 = (h2 + c) >>> 0;
        h3 = (h3 + d) >>> 0;
        h4 = (h4 + e) >>> 0;
        h5 = (h5 + f) >>> 0;
        h6 = (h6 + g) >>> 0;
        h7 = (h7 + h) >>> 0;
    }

    const toHex = n => ('00000000' + n.toString(16)).slice(-8);
    return toHex(h0) + toHex(h1) + toHex(h2) + toHex(h3) + toHex(h4) + toHex(h5) + toHex(h6) + toHex(h7);
}

// Set authentication cookies
function setAuthCookies(uid, pwHash) {
    const expiryDate = new Date();
    expiryDate.setTime(expiryDate.getTime() + (30 * 24 * 60 * 60 * 1000)); // 30 days
    const expires = 'expires=' + expiryDate.toUTCString();
    
    document.cookie = `uid=${uid};${expires};path=/;SameSite=Lax`;
    document.cookie = `pwhash=${pwHash};${expires};path=/;SameSite=Lax`;
}

// Get authentication cookies
function getAuthCookies() {
    const cookies = {};
    document.cookie.split(';').forEach(cookie => {
        const [name, value] = cookie.trim().split('=');
        cookies[name] = value;
    });
    return {
        uid: cookies.uid || null,
        pwhash: cookies.pwhash || null
    };
}

// Clear authentication cookies
function clearAuthCookies() {
    document.cookie = 'uid=;expires=Thu, 01 Jan 1970 00:00:00 UTC;path=/;';
    document.cookie = 'pwhash=;expires=Thu, 01 Jan 1970 00:00:00 UTC;path=/;';
}

// Verify if user is authenticated
async function verifyAuth() {
    const auth = getAuthCookies();
    
    if (!auth.uid || !auth.pwhash) {
        return false;
    }
    
    try {
        const response = await fetch('/api/verify', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                uid: parseInt(auth.uid),
                pwhash: auth.pwhash
            })
        });
        
        const data = await response.json();
        return data.success === true;
    } catch (error) {
        console.error('Auth verification error:', error);
        return false;
    }
}

// Check authentication and redirect if not logged in
async function requireAuth() {
    const isAuthenticated = await verifyAuth();
    
    if (!isAuthenticated) {
        window.location.href = '/login/';
        return false;
    }
    
    return true;
}

// Login function
async function login(username, password) {
    try {
        const response = await fetch('/api/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                username: username,
                password: password
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            setAuthCookies(data.uid, data.pwhash);
            return { success: true, uid: data.uid };
        } else {
            return { success: false, message: data.message || 'Login failed' };
        }
    } catch (error) {
        console.error('Login error:', error);
        return { success: false, message: 'Network error' };
    }
}

// Register function
async function register(username, password, introduction) {
    try {
        const response = await fetch('/api/register', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                username: username,
                password: password,
                introduction: introduction
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            return { success: true, uid: data.uid };
        } else {
            return { success: false, message: data.message || 'Registration failed' };
        }
    } catch (error) {
        console.error('Register error:', error);
        return { success: false, message: 'Network error' };
    }
}

// Logout function
function logout() {
    clearAuthCookies();
    window.location.href = '/login/';
}

// Get current user ID
function getCurrentUID() {
    const auth = getAuthCookies();
    return auth.uid ? parseInt(auth.uid) : null;
}

// Get current password hash
function getCurrentPWHash() {
    const auth = getAuthCookies();
    return auth.pwhash || null;
}
