#!/usr/bin/env node

const { spawnSync } = require('node:child_process');
const fs = require('node:fs');
const path = require('node:path');

const desktopDir = path.resolve(__dirname, '..');
const projectRoot = path.resolve(desktopDir, '..');
const frontendDir = path.join(projectRoot, 'frontend');
const frontendDist = path.join(frontendDir, 'dist');
const targetDir = path.join(desktopDir, 'resources', 'ui');

function buildFrontend() {
  console.log('[desktop] Construyendo frontend con Vite...');
  const result = spawnSync('npm', ['run', 'build'], {
    cwd: frontendDir,
    stdio: 'inherit',
    shell: process.platform === 'win32',
  });
  if (result.status !== 0) {
    throw new Error('Falló la build del frontend. Revisa los mensajes anteriores.');
  }
}

function copyDist() {
  if (!fs.existsSync(frontendDist)) {
    throw new Error(`No existe frontend/dist. Ejecuta "npm install" y "npm run build" dentro de frontend.`);
  }
  fs.rmSync(targetDir, { recursive: true, force: true });
  fs.mkdirSync(targetDir, { recursive: true });
  fs.cpSync(frontendDist, targetDir, { recursive: true });
  console.log(`[desktop] Recursos copiados a ${targetDir}`);
}

try {
  buildFrontend();
  copyDist();
} catch (error) {
  const message = error instanceof Error ? error.message : String(error);
  console.error(`[desktop] ${message}`);
  process.exit(1);
}
