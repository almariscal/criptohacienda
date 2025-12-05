const { contextBridge } = require('electron');

const apiBaseUrl = process.env.CHR_DESKTOP_API_URL || '';

contextBridge.exposeInMainWorld('desktopConfig', {
  apiBaseUrl,
  platform: process.platform,
});
