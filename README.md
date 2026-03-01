# TrimAnalysis

Analysis notebooks and helper scripts for the TRIM5α/HIV capsid project.

This repository is set up for a **conda-based** workflow and includes a data bootstrap script for Zenodo.

## Repository layout

- `analysiscode/` — Jupyter notebooks and helper scripts used for analyses.
- `environment.yaml` — conda environment specification for a new user.
- `setup.py` — downloads repository data from Zenodo DOI `10.5281/zenodo.14014166`.

## 1) Install Git (if needed)

### Windows

Option A (recommended, winget):

```powershell
winget install --id Git.Git -e --source winget
```

Option B:
- Download and install from: https://git-scm.com/download/win

Verify:

```powershell
git --version
```

### macOS

```bash
brew install git
# or
xcode-select --install
```

Verify:

```bash
git --version
```

### Linux (Ubuntu/Debian)

```bash
sudo apt update
sudo apt install -y git
```

Verify:

```bash
git --version
```

## 2) Clone this repository

If you have the URL:

```bash
git clone <REPO_URL>
cd TrimAnalysis
```

If you already have the folder locally, just open it in VS Code and continue.

## 3) Install Conda (Miniconda or Anaconda)

If conda is not installed yet:
- Miniconda: https://docs.conda.io/en/latest/miniconda.html
- Anaconda: https://www.anaconda.com/download

After install, open a **new terminal** and verify:

```bash
conda --version
```

## 4) Create and activate the environment

From the repository root:

```bash
conda env create -f environment.yaml
conda activate trimanalysis
```

## 5) Download project data from Zenodo

Run:

```bash
python setup.py --output-dir data
```

Useful options:

```bash
python setup.py --output-dir data --force
python setup.py --doi 10.5281/zenodo.14014166 --output-dir data
```

Notes:
- The DOI resolves to the latest Zenodo version.
- The dataset is large (~16 GB zip); ensure sufficient disk space.

## 6) Launch notebooks

```bash
jupyter lab
```

Then open notebooks under `analysiscode/`.

## 7) Basic Git workflow

Check status:

```bash
git status
```

Pull latest changes:

```bash
git pull
```

Create a feature branch:

```bash
git checkout -b my-feature
```

Commit work:

```bash
git add .
git commit -m "Describe your change"
```

Push branch:

```bash
git push -u origin my-feature
```

## 8) Updating dependencies later

If `environment.yaml` changes:

```bash
conda env update -f environment.yaml --prune
```

## Troubleshooting

- **`conda: command not found`**
  - Reopen terminal, or initialize shell with `conda init`, then reopen terminal.
- **`python` not found**
  - Activate env first: `conda activate trimanalysis`.
- **Kernel/package mismatch in Jupyter**
  - Ensure Jupyter is running from the activated conda environment.
- **Slow/incomplete data download**
  - Re-run with `--force` to retry all files.

---

If you want, a next step is to add a short “recommended notebook run order” section for new users in this README.
