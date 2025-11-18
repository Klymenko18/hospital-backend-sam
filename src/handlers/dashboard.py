"""Serve a minimal admin dashboard and runtime config via API Gateway + Lambda."""
import json
from typing import Dict, Any


_HTML = """<!doctype html>
<html lang="en"><head>
<meta charset="utf-8"/><meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>Hospital Admin Dashboard</title>
</head><body>
<h2>Hospital Admin Dashboard</h2>
<div id="status">Loading...</div>
<pre id="metrics"></pre>
<script src="https://unpkg.com/aws-amplify@6.0.0/dist/aws-amplify.min.js"></script>
<script>
(async () => {
  const cfgResp = await fetch("./config.js",{cache:"no-store"});
  const text = await cfgResp.text(); eval(text); // sets window.DASHBOARD_CFG
  const { Auth } = window.aws_amplify;
  const cfg = window.DASHBOARD_CFG;

  aws_amplify.Amplify.configure({
    Auth: {
      region: cfg.region,
      userPoolId: cfg.userPoolId,
      userPoolWebClientId: cfg.userPoolWebClientId,
      oauth: {
        domain: cfg.domain.replace(/^https?:\\/\\//,''),
        scope: ['openid','email','profile'],
        redirectSignIn: cfg.redirectSignIn,
        redirectSignOut: cfg.redirectSignOut,
        responseType: 'code'
      }
    }
  });

  document.getElementById('status').innerText = 'Checking session...';
  try { await Auth.currentAuthenticatedUser(); }
  catch (_) { document.getElementById('status').innerText='Redirecting to sign-in...'; return Auth.federatedSignIn(); }

  document.getElementById('status').innerText = 'Fetching metrics...';
  const token = (await Auth.currentSession()).getIdToken().getJwtToken();
  const r = await fetch(cfg.apiBaseUrl + '/admin/metrics', { headers: { Authorization: 'Bearer ' + token }});
  document.getElementById('metrics').textContent = await r.text();
  document.getElementById('status').innerText = 'OK';
})();
</script>
</body></html>
"""


def _resp(code: int, body: str, ctype: str) -> Dict[str, Any]:
    return {
        "statusCode": code,
        "headers": {
            "Content-Type": ctype,
            "Cache-Control": "no-store",
            "Access-Control-Allow-Origin": "*",
        },
        "body": body,
    }


def handler(event: Dict[str, Any], _ctx) -> Dict[str, Any]:
    """Entry point for API Gateway HTTP API."""
    path = event.get("rawPath") or ""
    domain = (event.get("requestContext") or {}).get("domainName") or (event.get("headers") or {}).get("host") or ""
    base = f"https://{domain}"

    if path.endswith("/admin") or path.endswith("/admin/") or path == "/":
        return _resp(200, _HTML, "text/html; charset=utf-8")

    if path.endswith("/admin/config.js"):
        import os
        cfg = {
            "region": os.environ["REGION"],
            "userPoolId": os.environ["USER_POOL_ID"],
            "userPoolWebClientId": os.environ["USER_POOL_CLIENT_ID"],
            "domain": os.environ["COGNITO_DOMAIN"],
            "redirectSignIn": base + "/admin",
            "redirectSignOut": base + "/admin",
            "apiBaseUrl": base,
        }
        js = "window.DASHBOARD_CFG=" + json.dumps(cfg)
        return _resp(200, js, "application/javascript; charset=utf-8")

    return _resp(404, "Not Found", "text/plain; charset=utf-8")
