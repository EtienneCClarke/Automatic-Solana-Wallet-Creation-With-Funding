import argparse
import csv
import os
import base58
import json
import sys
import asyncio
from solders.keypair import Keypair
from solders.system_program import TransferParams, transfer
from solders.transaction import VersionedTransaction
from solders.pubkey import Pubkey
from solana.rpc.async_api import AsyncClient
from solders.message import MessageV0
from spl.token.instructions import transfer_checked, TransferCheckedParams
from spl.token.instructions import get_associated_token_address, create_associated_token_account
from spl.token.constants import TOKEN_PROGRAM_ID

# Parse CLI arguments
parser = argparse.ArgumentParser()

parser.add_argument("-p", "--PATH", help="Output directory, include trailing slash", type=str, default="./wallet/")
parser.add_argument("-a", "--AMOUNT", help="Funding amount in Lamports or SPL Token", type=int, default=1000000)
parser.add_argument("-s", "--SOURCE_WALLET", help="Wallet used to fund new wallet", type=str)
parser.add_argument("-t", "--TOKEN_MINT", help="Token mint address for SPL Token", type=str)
parser.add_argument("-d", "--TOKEN_DECIMALS", help="Number of decimals for SPL Token", type=int, default=6)

args = parser.parse_args()

def getRPCClient():
    return AsyncClient("") # Enter your RPC URL

def createPathIfNotExists(path):
    # If directory exists skip else create
    if not os.path.exists(args.PATH):
        os.makedirs(os.path.dirname(args.PATH), exist_ok=True)

def checkFileExists(path):
    # check if file exists
    if not os.path.exists(path):
        print(f"❌  Error: could not locate {path}")
        return False
    return True

def generateKeypair():
    try:
        print(">>> Generating keypair...")
        account = Keypair()
        privateKey = base58.b58encode(account.secret() + base58.b58decode(str(account.pubkey()))).decode('utf-8')
        print(f"✅  Keypair successfully generated for: {account.pubkey()}")
        return [account, privateKey]
    except Exception as e:
        print(f"❌  Error generating keypair: {e}")
        sys.exit()

def generateCSV(account, privateKey):
    print(">>> Generating CSV file...")
    csv_path = args.PATH + "wallet.csv"
    try:
        # check if file exists already and ask user if they want to continue
        if os.path.exists(csv_path):
            response = input(f"⚠️   {csv_path} already exists. Do you want to overwrite it? (y/n): ")
            if response.lower() != 'y':
                print("❌  Operation cancelled.")
                sys.exit()

        with open(csv_path, 'w', newline='') as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow(['WALLET', 'PRIVATE KEY'])
            writer.writerow([account.pubkey(), privateKey])
            print(f"✅  CSV file generated at: {csv_path}")
    except Exception as e:
        print(f"❌  Error generating CSV: {e}")
        sys.exit()

def generateJSON(account):
    # Generate JSON keypair
    print(">>> Generating JSON file...")
    json_path = args.PATH + "keypair.json"
    try:

        # check if file exists already and ask user if they want to continue
        if os.path.exists(json_path):
            response = input(f"⚠️   {json_path} already exists. Do you want to overwrite it? (y/n): ")
            if response.lower() != 'y':
                print("❌  Operation cancelled.")
                sys.exit()

        with open(json_path, 'w', encoding='utf-8') as json_file:
            json.dump(json.loads(account.to_json()), json_file, ensure_ascii=False, separators=(',', ':'))
            print(f"✅  JSON file generated at: {json_path}")
    except Exception as e:
        print(f"❌  Error generating JSON file: {e}")
        sys.exit()

def loadJSONKeypair(path):
    print(">>> Reading Keypair file...")
    try:
        # read byte array from JSON file
        with open(path, 'r', encoding='utf-8') as f:
            keypair_data = json.load(f)
            sender_keypair = Keypair.from_bytes(bytes(keypair_data))
            print(f"✅  Keypair loaded from {path}. Address -> {sender_keypair.pubkey()}")
            return sender_keypair
    except Exception as e:
        print(f"❌  Error loading Keypair: {e}")
        sys.exit()

def getAssociatedTokenAccount(account, mint):
    try:
        return get_associated_token_address(
            owner=account.pubkey(),
            mint=mint,
            token_program_id=TOKEN_PROGRAM_ID
        )
    except Exception as e:
        print(f"❌  Error getting associated token account: {e}")
        sys.exit()

async def checkAccountHasEnoughTokens(account, mint):
    try:
        rpc = getRPCClient()
        async with rpc:
            associatedTokenAccount = getAssociatedTokenAccount(account, mint)
            token_balance = await rpc.get_token_account_balance(associatedTokenAccount)
            if int(token_balance.value.amount) < args.AMOUNT:
                print(f"❌  Error: Insufficient token balance in account {associatedTokenAccount}. Current balance: {token_balance.value.ui_amount} tokens")
                sys.exit()
    except Exception as e:
        print(f"❌  Error checking token balance: {e}")
        sys.exit()

async def checkAccountBalanceInLamports(account):
    try:
        rpc = getRPCClient()
        async with rpc:
            balance = await rpc.get_balance(account.pubkey())
            return balance.value
    except Exception as e:
        print(f"❌  Error checking account balance: {e}")
        sys.exit()

async def checkAccountHasEnoughSOL(account, amount):
    print(f">>> Checking if account {account.pubkey()} has enough SOL... (required {amount / 1_000_000_000} SOL)")
    balance = await checkAccountBalanceInLamports(account)
    if balance < amount:
        print(f"❌  Error: Insufficient balance in account {account.pubkey()}. Current balance: {balance} Lamports")
        sys.exit()
    print(f"✅  Account {account.pubkey()} has sufficient balance: {balance / 1_000_000_000} SOL.")

async def sendSol(sender, recipient, amount):
    try:
        rpc = getRPCClient()
        async with rpc:
            # Get latest blockhash
            latest_blockhash = await rpc.get_latest_blockhash()

            # Create transfer instruction
            transfer_instruction = transfer(
                TransferParams(
                    from_pubkey=sender.pubkey(),
                    to_pubkey=recipient.pubkey(),
                    lamports=amount
                )
            )

            # Create message
            message = MessageV0.try_compile(
                payer=sender.pubkey(),
                instructions=[transfer_instruction],
                address_lookup_table_accounts=[],
                recent_blockhash=latest_blockhash.value.blockhash
            )

            print(f">>> Sending {amount / 1_000_000_000} SOL from {sender.pubkey()} to {recipient.pubkey()}...")
            
            # Create transaction
            transaction = VersionedTransaction(message, [sender])
            response = (await rpc.send_transaction(transaction)).value
            print(f"✅  Transaction sent successfully, signature: {response}")

    except Exception as e:
        print(f"❌  Error sending SOL: {e}")
        sys.exit()

async def sendTokens(sender, recipient, mint, amount, decimals):
    try:
        rpc = getRPCClient()
        async with rpc:

            # Get associated token accounts
            sender_ata = getAssociatedTokenAccount(sender, mint)
            recipient_ata = getAssociatedTokenAccount(recipient, mint)

            # Check if recipient ATA exists, if not, create it
            resp = await rpc.get_account_info(recipient_ata)
            instructions = []
            if resp.value is None:
                print(f">>> Creating associated token account for recipient: {recipient_ata}")
                instructions.append(
                    create_associated_token_account(
                        payer=sender.pubkey(),
                        owner=recipient.pubkey(),
                        mint=mint
                    )
                )

            ui_amount = amount / (10 ** decimals)

            # Create transfer checked instruction
            transfer_instruction = transfer_checked(
                TransferCheckedParams(
                    program_id=TOKEN_PROGRAM_ID,
                    source=sender_ata,
                    mint=mint,
                    dest=recipient_ata,
                    owner=sender.pubkey(),
                    amount=amount,
                    decimals=decimals
                )
            )
            instructions.append(transfer_instruction)

            # Get latest blockhash
            recent_blockhash = await rpc.get_latest_blockhash()

            # Create message
            message = MessageV0.try_compile(
                payer=sender.pubkey(),
                instructions=instructions,
                address_lookup_table_accounts=[],
                recent_blockhash=recent_blockhash.value.blockhash
            )

            print(f">>> Sending {ui_amount} tokens from {sender.pubkey()} to {recipient.pubkey()}...")

            # Create transaction
            transaction = VersionedTransaction(message, [sender])
            response = (await rpc.send_transaction(transaction)).value
            print(f"✅  Transaction sent successfully, signature: {response}")

    except Exception as e:
        print(f"❌  Error sending tokens: {e}")
        sys.exit()

def main():

    # Create output directory if it doesn't exist
    createPathIfNotExists(args.PATH)

    # Check if source wallet exists
    if args.SOURCE_WALLET and not checkFileExists(args.SOURCE_WALLET):
        sys.exit()

    # Generate keypair
    [account, privateKey] = generateKeypair()

    # Generate files
    generateCSV(account, privateKey)
    generateJSON(account)

    if args.SOURCE_WALLET:
        sender = loadJSONKeypair(args.SOURCE_WALLET)
        if args.TOKEN_MINT:
            MINT = Pubkey.from_string(args.TOKEN_MINT)
            asyncio.run(checkAccountHasEnoughTokens(sender, MINT))
            asyncio.run(sendTokens(sender, account, MINT, args.AMOUNT, args.TOKEN_DECIMALS))
        else:
            asyncio.run(checkAccountHasEnoughSOL(sender, args.AMOUNT))
            asyncio.run(sendSol(sender, account, args.AMOUNT))

if __name__ == "__main__":
    main()