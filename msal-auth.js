// Shared MSAL setup for login.html + index.html. Reuses the Call Cycle
// Portal's own Entra ID app registration (not a new one) since it already
// has Files.ReadWrite consented against the SharePoint site this dashboard
// reads from -- one less admin-consent step. The only thing that needs
// adding in Entra ID is this dashboard's redirect URI on that existing app.
const MSAL_CONFIG = {
  clientId: "f7e6dfb5-798c-4feb-8d7c-d1f6c53dc37f",
  tenantId: "cbe83df2-b350-4dab-8d5f-f78d21fe7d27", // Meridian Group tenant
  redirectUri: "https://meridian-group-za.github.io/Meridian-Call-Cycle-Coverage/login.html",
};
const GRAPH_SCOPES = ["Files.ReadWrite"];

// SharePoint location of the live Call Cycle Master run file, matching the
// portal's own SHAREPOINT_HOSTNAME/SITE_PATH/FOLDER_PATH constants exactly
// -- same file, same site, no separate copy.
const SHAREPOINT_HOSTNAME = "meridiangroupza.sharepoint.com";
const SHAREPOINT_SITE_PATH = "sites/StockFixInventory";
const SHAREPOINT_FOLDER_PATH = "StockFix/Call Cycles";
const RUN_FILENAME = "run-latest.json";

// Local dev (this dashboard served from 127.0.0.1/localhost) skips real
// auth entirely and uses the live_data_server.py / mock-data fallback that
// already existed before this wiring -- only the deployed GitHub Pages
// version requires a real Microsoft sign-in.
function isLocalDev() {
  return ["localhost", "127.0.0.1"].includes(location.hostname);
}

let msalInstance = null;
function getMsalInstance() {
  if (!msalInstance) {
    msalInstance = new msal.PublicClientApplication({
      auth: { clientId: MSAL_CONFIG.clientId, authority: `https://login.microsoftonline.com/${MSAL_CONFIG.tenantId}`, redirectUri: MSAL_CONFIG.redirectUri },
      cache: { cacheLocation: "sessionStorage" },
    });
  }
  return msalInstance;
}

async function getGraphToken() {
  const inst = getMsalInstance();
  const account = inst.getAllAccounts()[0];
  if (!account) throw new Error("Not signed in");
  try {
    const result = await inst.acquireTokenSilent({ scopes: GRAPH_SCOPES, account });
    return result.accessToken;
  } catch (e) {
    await inst.acquireTokenRedirect({ scopes: GRAPH_SCOPES, account });
    return null; // page will redirect; nothing after this runs
  }
}

// Fetches run-latest.json's full contents from SharePoint via Graph and
// transforms combinedMaster into the same {rep_rows, merch_rows} shape the
// dashboard already expects (JS port of scripts/live_data_server.py's
// slim()/norm_division so both paths produce identical output).
async function fetchCallCycleMasterFromGraph() {
  const token = await getGraphToken();
  if (!token) return null;
  const siteRes = await fetch(`https://graph.microsoft.com/v1.0/sites/${SHAREPOINT_HOSTNAME}:/${SHAREPOINT_SITE_PATH}`, { headers: { Authorization: "Bearer " + token } });
  if (!siteRes.ok) throw new Error("Could not resolve SharePoint site (status " + siteRes.status + ")");
  const siteId = (await siteRes.json()).id;
  const path = encodeURI(`${SHAREPOINT_FOLDER_PATH}/${RUN_FILENAME}`);
  const fileRes = await fetch(`https://graph.microsoft.com/v1.0/sites/${siteId}/drive/root:/${path}:/content`, { headers: { Authorization: "Bearer " + token } });
  if (!fileRes.ok) throw new Error("Could not load " + RUN_FILENAME + " (status " + fileRes.status + ")");
  const raw = await fileRes.json();
  return transformCombinedMaster(raw);
}

function normDivision(v) {
  v = (v || "").trim().toUpperCase();
  if (!v) return "Unknown";
  return v.charAt(0) + v.slice(1).toLowerCase();
}

function transformCombinedMaster(raw) {
  const rep_rows = [], merch_rows = [];
  (raw.combinedMaster || []).forEach((r) => {
    // "Office" banner is internal Meridian admin/conference-room addresses,
    // not real stores -- drop entirely rather than land in "Other / Unclassified".
    if ((r["BANNER"] || "").trim().toUpperCase() === "OFFICE") return;
    const isMerch = (r["RESOURCE TYPE"] || "").includes("MERCHANDISER");
    const row = {
      storeCode: r["GEO REP STORE CODE"] || r["STORE CODE"],
      storeName: r["STORE NAME"],
      banner: r["BANNER"],
      division: normDivision(r["DIVISION"]),
      region: r["REGION"],
      resourceId: r["RESOURCE EMP ID"],
      resourceName: r["RESOURCE NAME"],
      resourceType: r["RESOURCE TYPE"],
      frequency: r["CALLING FREQUENCY"],
      managerId: r["MANAGER EMP CODE"],
      managerName: r["LINE MANAGER"],
    };
    (isMerch ? merch_rows : rep_rows).push(row);
  });
  return { timestamp: raw.timestamp, processedBy: raw.processedBy, rep_rows, merch_rows };
}
