/**
 * Web Security Suite Node.js/Express SDK Middleware
 */
const http = require('http');

function sentinelaiMiddleware(options = {}) {
  const portalUrl = options.portalUrl || 'http://localhost:8000';
  const domain = options.domain;
  const failSafeOpen = options.failSafeOpen !== false; // Default true

  if (!domain) {
    console.warn('[Web Security Suite] Warning: domain option is required for request checks.');
  }

  return function (req, res, next) {
    if (!domain) {
      return next();
    }

    // Capture request details
    let body = '';
    if (req.body) {
      body = typeof req.body === 'string' ? req.body : JSON.stringify(req.body);
    }

    const payload = JSON.stringify({
      domain: domain,
      method: req.method,
      path: req.path,
      headers: req.headers,
      query_params: req.url.split('?')[1] || '',
      body: body,
      ip_address: req.ip || req.connection.remoteAddress || '127.0.0.1'
    });

    const parsedUrl = new URL(`${portalUrl}/api/waf/check`);
    const requestOptions = {
      hostname: parsedUrl.hostname,
      port: parsedUrl.port || 80,
      path: parsedUrl.pathname,
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Content-Length': Buffer.byteLength(payload)
      },
      timeout: 2000 // 2 seconds threshold
    };

    const clientReq = http.request(requestOptions, (clientRes) => {
      let responseBody = '';
      clientRes.on('data', (chunk) => {
        responseBody += chunk;
      });

      clientRes.on('end', () => {
        try {
          if (clientRes.statusCode === 200) {
            const data = JSON.parse(responseBody);
            if (data.blocked) {
              res.status(403).send(`
                <html>
                  <body style="background: #020617; color: #f1f5f9; font-family: sans-serif; display: flex; align-items: center; justify-content: center; height: 100vh; margin: 0;">
                    <div style="text-align: center; border: 1px solid rgba(239, 68, 68, 0.3); border-radius: 12px; padding: 30px; background: #0f172a; max-width: 450px;">
                      <h1 style="color: #ef4444;">Request Blocked</h1>
                      <p style="color: #94a3b8;">Blocked by Web Security Suite Application Shield Middleware.</p>
                      <div style="font-size: 12px; font-family: monospace; background: #020617; padding: 10px; border-radius: 6px;">
                        Reason: ${data.reason || 'Security Rule Match'}
                      </div>
                    </div>
                  </body>
                </html>
              `);
              return;
            }
          }
          next();
        } catch (e) {
          handleFailure(e);
        }
      });
    });

    clientReq.on('error', (e) => {
      handleFailure(e);
    });

    clientReq.on('timeout', () => {
      clientReq.destroy();
      handleFailure(new Error('Timeout connecting to Web Security Suite threat detection server.'));
    });

    function handleFailure(err) {
      console.error('[Web Security Suite] Detection server connection error:', err.message);
      if (failSafeOpen) {
        next();
      } else {
        res.status(403).send('Forbidden - Web Security Suite failure (Fail-Closed Mode).');
      }
    }

    clientReq.write(payload);
    clientReq.end();
  };
}

module.exports = sentinelaiMiddleware;
