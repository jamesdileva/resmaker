const { app, BrowserWindow } = require('electron');
const fs = require('fs');
const path = require('path');

const DEV_SERVER_URL = 'http://127.0.0.1:5173';

// Boot-state marker in the Electron userData dir. Sentinel's feature
// sandbox verifier requires a per-app state artifact here; see
// backend/app/services/feature_runner.py (_verify_sandbox).
function writeBootMarker() {
  try {
    const logPath = path.join(app.getPath('userData'), 'career-os.log');
    fs.appendFileSync(logPath, `${new Date().toISOString()} career-os boot\n`);
  } catch {
    // best effort — never block startup on logging
  }
}

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
  // load the compiled bundle straight from disk.
  if (!app.isPackaged && process.env.CAREER_OS_DEV !== '0') {
    win.loadURL(DEV_SERVER_URL);
  } else {
    win.loadFile(path.join(__dirname, '..', 'dist', 'index.html'));
  }
}

app.whenReady().then(() => {
  writeBootMarker();
  createWindow();

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit();
});
