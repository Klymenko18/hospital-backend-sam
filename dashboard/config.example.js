window.DASHBOARD_CFG = {
  region: "eu-central-1",
  userPoolId: "REPLACE_WITH_UserPoolId",
  userPoolWebClientId: "REPLACE_WITH_UserPoolClientId",
  domain: "https://REPLACE_PREFIX.auth.eu-central-1.amazoncognito.com",
  redirectSignIn: "http://REPLACE_BUCKET.s3-website-eu-central-1.amazonaws.com/",
  redirectSignOut: "http://REPLACE_BUCKET.s3-website-eu-central-1.amazonaws.com/",
  apiBaseUrl: "https://REPLACE_API_ID.execute-api.eu-central-1.amazonaws.com",
  scopes: ["openid", "email", "profile"]
};
