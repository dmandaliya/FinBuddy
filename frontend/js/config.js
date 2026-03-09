// config.js — single place to control the API URL
// Auto-switches between local development and production (Render).
// Every other JS file imports the API constant from here via window.API_BASE.

(function () {
  const isLocal =
    window.location.hostname === "localhost" ||
    window.location.hostname === "127.0.0.1";

  // Replace this URL after you deploy to Render.
  // It will look like: https://finbuddy-api.onrender.com
  const PROD_API = "https://finbuddy-api.onrender.com";

  window.API_BASE = isLocal ? "http://127.0.0.1:8001" : PROD_API;
})();
