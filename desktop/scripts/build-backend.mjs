import { existsSync } from 'node:fs'
import { spawnSync } from 'node:child_process'
import { dirname, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'

const desktopRoot = resolve(dirname(fileURLToPath(import.meta.url)), '..')
const projectRoot = resolve(desktopRoot, '..')
const candidates = process.platform === 'win32'
  ? [resolve(projectRoot, '.venv', 'Scripts', 'python.exe'), 'python']
  : [resolve(projectRoot, '.venv', 'bin', 'python3'), resolve(projectRoot, '.venv', 'bin', 'python'), 'python3']

const python = candidates.find((candidate) => !candidate.includes('/') && !candidate.includes('\\') || existsSync(candidate))
if (!python) {
  console.error('No Python interpreter found. Create .venv and install the development dependencies first.')
  process.exit(1)
}

const result = spawnSync(python, [resolve(projectRoot, 'scripts', 'build_desktop_backend.py')], {
  cwd: projectRoot,
  stdio: 'inherit',
})

if (result.error) {
  console.error(`Failed to start ${python}: ${result.error.message}`)
  process.exit(1)
}

process.exit(result.status ?? 1)
