const { app, BrowserWindow, dialog } = require('electron');
const path = require('node:path');
const fs = require('node:fs');
const http = require('node:http');
const { spawn } = require('node:child_process');

const BACKEND_PORT = process.env.CHR_BACKEND_PORT || '8000';
const BACKEND_HOST = process.env.CHR_BACKEND_HOST || '127.0.0.1';
const isDev = process.env.NODE_ENV === 'development' || !app.isPackaged;

let mainWindow;
let backendProcess;

const resourcesDir = () =>
  app.isPackaged ? process.resourcesPath : path.resolve(__dirname, 'resources');

const projectRoot = () => path.resolve(__dirname, '..');

const uiEntryPoint = () => path.join(resourcesDir(), 'ui', 'index.html');

const backendBinaryName = () => (process.platform === 'win32' ? 'criptohacienda-backend.exe' : 'criptohacienda-backend');

function ensureDirWritable(dirPath) {
  try {
    fs.mkdirSync(dirPath, { recursive: true });
    fs.accessSync(dirPath, fs.constants.W_OK);
    return true;
  } catch (error) {
    console.warn(`[desktop] Unable to write to ${dirPath}:`, error.message);
    return false;
  }
}

function resolveDataDir() {
  if (process.env.CHR_DATA_DIR) {
    const customPath = path.resolve(process.env.CHR_DATA_DIR);
    if (ensureDirWritable(customPath)) {
      return customPath;
    }
  }

  const appImageSource = process.env.APPIMAGE;
  if (appImageSource) {
    const portableDir = path.join(path.dirname(appImageSource), 'criptohacienda-data');
    if (ensureDirWritable(portableDir)) {
      return portableDir;
    }
  }

  const portableCandidate = path.join(path.dirname(process.execPath), 'criptohacienda-data');
  if (ensureDirWritable(portableCandidate)) {
    return portableCandidate;
  }

  const fallback = path.join(app.getPath('userData'), 'data');
  ensureDirWritable(fallback);
  return fallback;
}

function resolveBackendCommand() {
  if (!app.isPackaged) {
    const python = process.env.CHR_PYTHON || (process.platform === 'win32' ? 'python' : 'python3');
    const args = ['-m', 'backend.desktop_main'];
    return {
      command: python,
      args,
      cwd: projectRoot(),
    };
  }

  const binaryPath = path.join(resourcesDir(), 'backend', backendBinaryName());
  if (!fs.existsSync(binaryPath)) {
    throw new Error(
      `No se encontró el servicio backend empaquetado en ${binaryPath}. ` +
        'Genera el ejecutable con PyInstaller y colócalo en desktop/resources/backend antes de construir la app.'
    );
  }
  return {
    command: binaryPath,
    args: [],
    cwd: path.dirname(binaryPath),
  };
}

function startBackend(dataDir) {
  const backendConfig = resolveBackendCommand();
  const env = {
    ...process.env,
    PORT: BACKEND_PORT,
    CRIPTOHACIENDA_DESKTOP_PORT: BACKEND_PORT,
    CRIPTOHACIENDA_DESKTOP_HOST: BACKEND_HOST,
    CRIPTOHACIENDA_DATA_DIR: dataDir,
  };
  const stdio = isDev ? 'inherit' : 'ignore';
  backendProcess = spawn(backendConfig.command, backendConfig.args, {
    cwd: backendConfig.cwd,
    env,
    stdio,
    windowsHide: true,
  });

  backendProcess.on('error', (error) => {
    console.error('[desktop] Error lanzando el backend:', error);
    dialog.showErrorBox(
      'Cripto Hacienda',
      'No se pudo iniciar el backend embebido. Comprueba que PyInstaller generó el ejecutable correctamente.'
    );
    app.quit();
  });

  backendProcess.on('exit', (code, signal) => {
    console.log(`[desktop] Backend finalizado (code=${code ?? 'null'} signal=${signal ?? 'none'})`);
    backendProcess = undefined;
    if (!isDev && code !== 0) {
      dialog.showErrorBox(
        'Cripto Hacienda',
        'El servicio backend se cerró inesperadamente. Reabre la aplicación o revisa los logs.'
      );
      app.quit();
    }
  });
}

function stopBackend() {
  if (!backendProcess) {
    return;
  }
  try {
    backendProcess.kill();
  } catch (error) {
    console.warn('[desktop] No se pudo terminar el backend limpio:', error);
  } finally {
    backendProcess = undefined;
  }
}

function pingBackend() {
  return new Promise((resolve) => {
    const req = http.get(
      {
        host: BACKEND_HOST,
        port: BACKEND_PORT,
        path: '/api/health',
        timeout: 1000,
      },
      (res) => {
        res.resume();
        resolve(res.statusCode === 200);
      }
    );
    req.on('error', () => resolve(false));
    req.on('timeout', () => {
      req.destroy();
      resolve(false);
    });
  });
}

async function waitForBackend() {
  const maxAttempts = 40;
  for (let attempt = 0; attempt < maxAttempts; attempt += 1) {
    // eslint-disable-next-line no-await-in-loop
    const ready = await pingBackend();
    if (ready) {
      return;
    }
    // eslint-disable-next-line no-await-in-loop
    await new Promise((resolve) => setTimeout(resolve, 500));
  }
  throw new Error('El backend no inició a tiempo.');
}

async function createMainWindow() {
  const uiFile = uiEntryPoint();
  if (!fs.existsSync(uiFile)) {
    throw new Error(
      `No se encontró la build del frontend (${uiFile}). Ejecuta "npm run sync:frontend" en desktop antes de arrancar.`
    );
  }

  mainWindow = new BrowserWindow({
    title: 'Cripto Hacienda',
    width: 1280,
    height: 800,
    minWidth: 1100,
    minHeight: 720,
    backgroundColor: '#0f172a',
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
    },
  });

  mainWindow.on('closed', () => {
    mainWindow = null;
  });

  await mainWindow.loadFile(uiFile);
}

async function bootstrap() {
  try {
    const dataDir = resolveDataDir();
    const apiBaseUrl = `http://${BACKEND_HOST}:${BACKEND_PORT}`;
    process.env.CHR_DESKTOP_API_URL = apiBaseUrl;
    startBackend(dataDir);
    await waitForBackend();
    await createMainWindow();
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error);
    dialog.showErrorBox('Cripto Hacienda', message);
    stopBackend();
    app.quit();
  }
}

app.whenReady().then(() => {
  bootstrap();

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createMainWindow().catch((error) => {
        const message = error instanceof Error ? error.message : String(error);
        dialog.showErrorBox('Cripto Hacienda', message);
      });
    }
  });
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('before-quit', () => {
  stopBackend();
});
