// MSAL setup for the P&G Dedicated Store Coverage dashboard. Reuses the same
// Entra ID app registration as the main Call Cycle Coverage dashboard
// (clientId f7e6dfb5-798c-4feb-8d7c-d1f6c53dc37f) -- one less admin-consent
// step -- but this dashboard is single-page (login + app both live in
// index.html, no separate login.html), so its own redirect URI needs adding
// to that app registration: https://meridian-group-za.github.io/Meridian-Call-Cycle-Coverage/pg/index.html
//
// No Graph/SharePoint scopes requested here -- this dashboard reads its data
// from a static cycle-data.json shipped alongside it (refreshed by re-running
// scripts/live_data_server.py's transform and re-exporting), not a live
// SharePoint fetch, so plain sign-in (no extra API permissions) is enough to
// gate access.
const PG_MSAL_CONFIG = {
  clientId: "f7e6dfb5-798c-4feb-8d7c-d1f6c53dc37f",
  tenantId: "cbe83df2-b350-4dab-8d5f-f78d21fe7d27", // Meridian Group tenant
  redirectUri: "https://meridian-group-za.github.io/Meridian-Call-Cycle-Coverage/pg/index.html",
};

// Local dev (this dashboard served from 127.0.0.1/localhost) skips real auth
// entirely, same as the main Call Cycle Coverage dashboard.
function isLocalDev() {
  return ["localhost", "127.0.0.1"].includes(location.hostname);
}

let pgMsalInstance = null;
function getPgMsalInstance() {
  if (!pgMsalInstance) {
    pgMsalInstance = new msal.PublicClientApplication({
      auth: { clientId: PG_MSAL_CONFIG.clientId, authority: `https://login.microsoftonline.com/${PG_MSAL_CONFIG.tenantId}`, redirectUri: PG_MSAL_CONFIG.redirectUri },
      cache: { cacheLocation: "sessionStorage" },
    });
  }
  return pgMsalInstance;
}
