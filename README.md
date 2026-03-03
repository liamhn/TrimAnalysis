# TrimAnalysis

Analysis notebooks and helper scripts for the TRIM5α/HIV capsid project.

This repository is set up for a **conda-based** workflow and includes a data bootstrap script for Zenodo.

## Repository layout

- `analysiscode/` — Jupyter notebooks and helper scripts used for analyses.
- `environment.yaml` — conda environment specification for a new user.
- `setup.py` — downloads repository data from Zenodo DOI `10.5281/zenodo.14014166`.

## 1) Clone this repository

If you have the URL:

```bash
git clone https://github.com/liamhn/TrimAnalysis
cd TrimAnalysis
```


## 2) Run setup (one command!)

From the repository root, run:

```bash
python setup.py
```

This single command will:
- ✓ Create the `trimanalysis` conda environment (if it doesn't exist)
- ✓ Register it as a Jupyter kernel
- ✓ Download Zenodo dataset (only if missing or outdated)
- ✓ Verify file checksums and skip downloads when files are up-to-date

Useful options:

```bash
# Force re-download even if checksums match
python setup.py --force

# Skip environment setup (data only)
python setup.py --skip-env

# Skip data download (environment only)
python setup.py --skip-data

# Specify different data location
python setup.py --output-dir my-data

# Use a different DOI
python setup.py --doi 10.5281/zenodo.14014166
```

Notes:
- The script is **idempotent**: safe to run multiple times.
- Checksums are verified automatically—only changed files are re-downloaded.
- The dataset is large (~16 GB zip); ensure sufficient disk space.

## 3) Activate the environment

After setup completes:

```bash
conda activate trimanalysis
```

## 4) Launch notebooks

```bash
jupyter notebook
```

Then open notebooks under `analysiscode/`.
Right now, the only notebook that is set up to work out of the box is the FigureOnlyFromZenodoData.ipynb.
This one should create all of the figures that are currently in the paper (unformatted, but all of the graphs themselves).

The analysis itself can also be updated to run on the zenodo data (which gets downloaded by setup.py, but I haven't set that up automatically yet)

5) A final note: The data you really need in on Narval Tape, the trajectories you want are under t5a ... huNumbering/*t5a*/* -- you will want these if you want to use the other in the analysiscode to generate data. If you want to build your own analysis from scratch, then you can use the data that is downloaded from the Zenodo (these are "true numbered residues"). You can write any analysis on these and it will work fine, just make sure you account for the fact that rhesus and human have different residue numberings.



