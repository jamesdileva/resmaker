const { app, BrowserWindow } = require('electron');
const { spawn } = require('child_process');
const fs = require('fs');
const http = require('http');
const path = require('path');

const DEV_SERVER_URL = 'http://127.0.0.1:5173';
const API_PORT = 8000;

// Boot-state marker in the Electron userData dir. Sentinel's feature
// sandbox verifier requires a per-app state artifact here; see
// backend/app/services/feature_runner.py (_verify_sandbox). Backend
// lifecycle lines land in the same file.
function logLine(message) {
  try {
    const logPath = path.join(app.getPath('userData'), 'career-os.log');
    fs.appendFileSync(logPath, `${new Date().toISOString()} ${message}\n`);
  } catch {
    // best effort — never block startup on logging
  }
}

// ---------------------------------------------------------------------------
// Local backend management (Sprint 33 follow-up): the packaged exe is a thin
// client over a FastAPI backend on :8000. When launched directly from inside
// the repo (win-unpacked sits under frontend/), we can spawn that backend
// from the project venv so the app works standalone; outside the repo tree
// there is no venv and we degrade gracefully (the UI shows an offline
// banner). Only the child WE spawn is ever killed.
let backendProc = null;

function exeDir() {
  // <repo>\frontend\dist_electron\win-unpacked\Career OS.exe -> repo root.
  // In dev (`electron .` from frontend/) __dirname is <repo>\frontend\electron,
  // so walking up lands on <repo> either way.
  return path.resolve(app.getPath('exe'), '..');
}

function repoRoot() {
  let dir = app.isPackaged ? exeDir() : path.resolve(__dirname, '..', '..');
  for (let i = 0; i < 4 && dir; i++) {
    if (
      fs.existsSync(path.join(dir, 'backend', '.venv', 'Scripts', 'python.exe'))
    ) {
      return dir;
    }
    const parent = path.dirname(dir);
    if (parent === dir) break;
    dir = parent;
  }
  return null;
}

function backendHealthy() {
  return new Promise((resolve) => {
    const request = http.get(
      `http://127.0.0.1:${API_PORT}/health`,
      { timeout: 1500 },
      (response) => {
        response.resume();
        resolve(response.statusCode === 200);
      },
    );
    request.on('timeout', () => {
      request.destroy();
      resolve(false);
    });
    request.on('error', () => resolve(false));
  });
}

async function ensureBackend() {
  for (let attempt = 0; attempt < 3; attempt++) {
    if (await backendHealthy()) {
      logLine(`backend already healthy on :${API_PORT} (reusing)`);
      return;
    }
    const root = repoRoot();
    if (!root) {
      logLine(
        'backend venv not found near the app — leaving the API offline '
          + '(renderer shows the offline banner)',
      );
      return;
    }
    const python = path.join(root, 'backend', '.venv', 'Scripts', 'python.exe');
    backendProc = spawn(
      python,
      ['-m', 'uvicorn', 'app.main:app', '--port', String(API_PORT)],
      {
        cwd: path.join(root, 'backend'),
        stdio: 'ignore',
        windowsHide: true,
      },
    );
    backendProc.on('exit', (code) => {
      logLine(`spawned backend exited (code ${code})`);
      backendProc = null;
    });
    logLine('spawned local backend from project venv on :8000');
    // Wait for it to bind before deciding whether another attempt helps.
    for (let waited = 0; waited < 30; waited++) {
      await new Promise((resolve) => setTimeout(resolve, 1000));
      if (await backendHealthy()) {
        logLine(`backend healthy after ${waited + 1}s`);
        return;
      }
      if (!backendProc) break; // died during startup
    }
  }
  logLine(`backend never became healthy on :${API_PORT}`);
}

function stopBackend() {
  if (!backendProc) return;
  try {
    // taskkill /T covers uvicorn's child processes on Windows; scoped to
    // our own PID — never by image name.
    spawn('taskkill', ['/PID', String(backendProc.pid), '/T', '/F'], {
      stdio: 'ignore',
      windowsHide: true,
    });
    logLine('torn down spawned backend');
  } catch {
    // best effort at shutdown
  }
  backendProc = null;
}

// ---------------------------------------------------------------------------

function createWindow() {
  const win = new BrowserWindow({
    width: 1280,
    height: 800,
    title: 'Career OS',
    webPreferences: {
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: true,
    },
  });

  // In dev (electron:dev) the Vite server serves the UI; packaged builds
  // load the compiled bundle straight from disk. If a dev shell starts
  // without Vite (e.g. `npm start` launched directly), fall back to the
  // last built bundle instead of showing a blank white window.
  if (!app.isPackaged && process.env.CAREER_OS_DEV !== '0') {
    win.loadURL(DEV_SERVER_URL).catch(() => {
      win.loadFile(path.join(__dirname, '..', 'dist', 'index.html'));
    });
  } else {
    win.loadFile(path.join(__dirname, '..', 'dist', 'index.html'));
  }
}

app.whenReady().then(() => {
  logLine('career-os boot');
  void ensureBackend(); // fire-and-forget: window opens while uvicorn binds
  createWindow();

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});

app.on('before-quit', stopBackend);

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit();
});
