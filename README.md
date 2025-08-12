# Automatic Solana Wallet Creation & Funding

## Table of Contents
- [Project Overview](#project-overview)
- [How It Works](#how-it-works)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
    - [Clone the Repository](#clone-the-repository)
    - [Set Up Virtual Environment](#set-up-virtual-environment)
- [Usage](#usage)

## Project Overview

This project provides a Python script for generating Solana wallets and optionally funding them with SOL or any SPL token. The script is designed for developers and operators who need to automate wallet creation and initial funding for Solana-based applications.

### Key Features

- **Wallet Generation:**  
  Creates a new Solana wallet using the `solders` library and outputs both a CSV file (with the public address and private key) and a `keypair.json` file (compatible with Solana CLI tools).

- **Automatic Funding:**  
  Optionally funds the newly created wallet with either SOL or a specified SPL token. The amount and token mint can be set via optional command-line arguments.

- **Flexible Output:**  
  Output directory and file overwriting behavior are configurable via CLI flags.

- **Safety Checks:**  
  - Verifies source wallet and sufficient balance before funding.
  - Ensures associated token accounts exist before SPL token transfers.

- **Async Solana RPC:**  
  Uses asynchronous RPC calls for efficient blockchain interactions.

## How It Works

The `main.py` script automates the process of creating and funding Solana wallets. Here’s a breakdown of its technical workflow:

### Architecture

- **Command-Line Interface:**  
  The script uses Python’s `argparse` to accept parameters for output directory, funding amount, source wallet, token mint, and decimals.

- **Key Functions:**
  - `generateKeypair()`: Creates a new Solana keypair.
  - `generateCSV()`: Saves the wallet address and private key to a CSV file.
  - `generateJSON()`: Saves the keypair in JSON format compatible with Solana CLI.
  - `loadJSONKeypair()`: Loads an existing wallet from a JSON file.
  - `getAssociatedTokenAccount()`: Computes the associated token account address for SPL tokens.
  - `sendSol()`: Sends SOL from a source wallet to the new wallet.
  - `sendTokens()`: Sends SPL tokens, creating the recipient’s associated token account if needed.
  - `checkAccountHasEnoughSOL()` / `checkAccountHasEnoughTokens()`: Ensure the source wallet has sufficient funds.

- **External Services and APIs:**
  - **Solana RPC:**  
    Uses the `solana-py` and `solders` libraries to interact with the Solana blockchain via asynchronous RPC calls.
  - **SPL Token Program:**  
    Handles SPL token transfers and associated token account creation.

## Prerequisites
- Python 3.6 or higher
- Git

## Installation

### Clone the Repository
```bash
git clone https://github.com/EtienneCClarke/Automatic-Solana-Wallet-Creation-With-Funding.git
```

### Open Project
```bash
cd Automatic-Solana-Wallet-Creation-With-Funding
```

### Set Up Virtual Environment
```bash
# Create a virtual environment
python -m venv venv

# Activate the virtual environment
# On Windows
venv\Scripts\activate
# On macOS/Linux
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## Usage

You can run the script from the command line and customize its behavior using the following flags:

| Flag / Option            | Description                                      | Default                |
|--------------------------|--------------------------------------------------|-----------------------|
| `-p`, `--PATH`           | Output directory for files                       | `./wallet/`           |
| `-a`, `--AMOUNT`         | Funding amount in Lamports or SPL token    | `1000000`             |
| `-s`, `--SOURCE_WALLET`  | Path to the source wallet JSON file              | *(None)*              |
| `-t`, `--TOKEN_MINT`     | SPL token mint address for funding               | *(None)*              |
| `-d`, `--TOKEN_DECIMALS` | Number of decimals for SPL token                 | `6`                   |

### How to Use

To run the script with default options:
```bash
python main.py
```
