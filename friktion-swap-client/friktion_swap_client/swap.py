#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------------
""" Module to call Swap contract """
# ---------------------------------------------------------------------------
# Imports
# ---------------------------------------------------------------------------
from dataclasses import asdict
import time
from friktion_swap_client.friktion_anchor.instructions import cancel
from friktion_swap_client.pda import DELEGATE_AUTHORITY_ADDRESS, SwapOrderAddresses, find_give_pool_address, find_receive_pool_address, find_swap_order_address, find_user_orders_address
from solana.utils import helpers
from shutil import ExecError
from anchorpy import Wallet
from anchorpy import Provider
from solana.blockhash import Blockhash
from solana.keypair import Keypair
from solana.publickey import PublicKey
from solana.rpc.api import Client
from solana.rpc.async_api import AsyncClient
from solana.rpc.commitment import Processed
from solana.publickey import PublicKey
from solana.utils.helpers import decode_byte_string
import spl.token._layouts as layouts
from spl.token.client import Token
from nacl import signing
import sys
sys.path.insert(0, "/Users/alexwlezien/Friktion/paradigm-integration/friktion-anchor")
from .friktion_anchor.accounts import SwapOrder, UserOrders
from .friktion_anchor.program_id import PROGRAM_ID
from solana.sysvar import SYSVAR_RENT_PUBKEY
from solana.sysvar import SYSVAR_INSTRUCTIONS_PUBKEY
from .friktion_anchor.instructions import create, exec, exec_msg
from solana.rpc.async_api import AsyncClient
from solana.system_program import SYS_PROGRAM_ID
from .swap_order_template import SwapOrderTemplate
from .bid_details import BidDetails
from spl.token.constants import ASSOCIATED_TOKEN_PROGRAM_ID, TOKEN_PROGRAM_ID
from solana.transaction import Transaction
from enum import Enum
import asyncio

def get_token_account(token_account_pk: PublicKey):
    http_client = Client(commitment=Processed)
    print('is connected?: {}'.format(http_client.is_connected()))
    resp = http_client.get_account_info(token_account_pk)
    print("token account: {}".format(resp))
    account_data = layouts.ACCOUNT_LAYOUT.parse(decode_byte_string(resp["result"]["value"]["data"][0]))
    return account_data

class Network(Enum):
    DEVNET = 1
    TESTNET = 2
    MAINNET = 3

def get_url_for_network(network: Network) -> str:
    if network == Network.DEVNET:
        return "https://api.devnet.solana.com"
    elif network == Network.TESTNET:
        return "https://api.testnet.solana.com"
    else:
        # mainnet
        return "https://solana-api.projectserum.com"

MIN_REQUIRED_ALLOWANCE = 100

# ---------------------------------------------------------------------------
# Swap Program
# ---------------------------------------------------------------------------
class SwapContract():

    network: Network
    url: str
    
    def __init__(self, network: Network):
        self.network = network
        self.url = get_url_for_network(network)


    # delegate should be the PDA of the swap order
    def give_allowance(self, wallet: Wallet, token_acct_to_delegate: PublicKey, mint: PublicKey, allowance: int):

        client = Client(self.url)
        token = Token(
            client,
            mint,
            TOKEN_PROGRAM_ID,
            wallet.payer
        )

        acct_info = token.get_account_info(token_acct_to_delegate)
        # use a global authority for all swaps
        # assert acct_info.owner == swap_order.counterparty
        
        token.approve(
            token_acct_to_delegate,
            DELEGATE_AUTHORITY_ADDRESS,
            wallet.public_key,
            allowance
        )

        return True
    
    # delegate should be the PDA of the swap order
    def verify_allowance(self, wallet: Wallet, mint: PublicKey, token_account: PublicKey):
        client = Client(self.url)
        token = Token(
            client,
            mint,
            TOKEN_PROGRAM_ID,
            wallet.payer
        )
        
        acct_info = token.get_account_info(token_account)
        print(acct_info.delegated_amount)
        assert acct_info.delegate == DELEGATE_AUTHORITY_ADDRESS
        assert acct_info.delegated_amount >= MIN_REQUIRED_ALLOWANCE

        return acct_info.delegated_amount

    """
    Object used to interact with swap contract
    Args:
        config (ContractConfig): Configuration to setup the Contract
    """

    async def get_offer_details(self, user: PublicKey, order_id: int) -> SwapOrder:
        """
        Method to get bid details
        Args:
            offer_id (int): Offer ID
        Raises:
            ValueError: The argument is not a valid offer
        Returns:
            details (SwapOrder): Offer details
        """

        client = AsyncClient(self.url)
        res = await client.is_connected()

        [addr, bump] = find_swap_order_address(user, order_id)
        
        acc = await SwapOrder.fetch(client, addr)
        if acc is None:
            raise ValueError("No swap found for user = ", user, ', order id = ', order_id)

        await client.close()
        return acc

    async def validate_bid(self, wallet: Wallet, bid_details: BidDetails, swap_order: SwapOrder) -> str:
        if swap_order.is_counterparty_provided and wallet.public_key != swap_order.counterparty:
            return {
                "error": "counterparty wallet pubkey doesn't match given swap order"
            }
        elif swap_order.expiry < int(time.time()):
            return {
                "error": "expiry was in the past"
            }
        # TODO: check mint of give pools and receive pools match
        # elif bid_details.counterparty_give_pool = swap_
        return {
            "error": None
        }

    async def create_offer(self, wallet: Wallet, template: SwapOrderTemplate) -> SwapOrder:
        """
        Method to create offer
        Args:
            offer (dict): Offer dictionary containing necessary parameters 
                to create a new offer
            wallet (Wallet): Wallet class instance
        Raises:
            TypeError: Offer argument is not a valid instance of Offer class
            ExecError: Transaction reverted
        Returns:
            offerId (int): OfferId of the created order
        """

        client = AsyncClient(self.url)
        await client.is_connected()

        pdas : SwapOrderAddresses = await SwapOrderAddresses.from_user(client, wallet.public_key)

        ix = create({
            "give_size": template.give_size,
            "receive_size": template.receive_size,
            "expiry": template.expiry,
            "is_counterparty_provided": template.is_counterparty_provided,
            "is_whitelisted": template.is_whitelisted
            }, {
            "payer": wallet.public_key, # signer
            "authority": wallet.public_key,
            "user_orders": pdas.user_orders_address,
            "swap_order": pdas.swap_order_address,
            "give_pool": pdas.give_pool_address,
            "give_mint": template.give_mint,
            "receive_pool": pdas.receive_pool_address,
            "receive_mint": template.receive_mint,
            "creator_give_pool": template.creator_give_pool,
            "counterparty": template.counterparty,
            "whitelist_token_mint": template.whitelist_token_mint,
            "system_program": SYS_PROGRAM_ID,
            "token_program": TOKEN_PROGRAM_ID,
            "rent": SYSVAR_RENT_PUBKEY
        })

        tx = Transaction().add(ix)

        # print('create ix data: {}'.format(ix.data))
        # print('create ix accounts: {}'.format(ix.keys))

        provider = Provider(
            client, wallet
        )

        print('sending create tx...')
        tx_resp = await provider.send(tx, [])
        print(tx_resp)

        await client.confirm_transaction(tx_resp)

        await asyncio.sleep(1)
        acc = await SwapOrder.fetch(client, pdas.swap_order_address)

        await client.close()

        return acc


    async def validate_and_exec_bid_msg(self, wallet: Wallet, bid_details: BidDetails, signed_msg: signing.SignedMessage):
        """
        Method to execute bid via signed message
        """

        client = AsyncClient(self.url)
        res = await client.is_connected()

        swap_order_owner = bid_details.swap_order_owner
        order_id = bid_details.order_id

        pdas = SwapOrderAddresses(bid_details.swap_order_owner, bid_details.order_id)

        acc = await SwapOrder.fetch(client, pdas.swap_order_address)
        if acc is None:
            raise ValueError("No swap found for user = ", swap_order_owner, ', order id = ', order_id)

        error_dict = await self.validate_bid(wallet, bid_details, acc)
        if error_dict['error'] is not None:
            await client.close()
            return error_dict
        
        ix = exec_msg({
            "signature": str(signed_msg.signature),
            "caller": wallet.public_key,
            "raw_msg": str(signed_msg.message)
        },{
            "authority": wallet.public_key, # signer
            "delegate_authority": pdas.delegate_authority_address,
            "swap_order": pdas.swap_order_address,
            "give_pool": acc.give_pool,
            "receive_pool": acc.receive_pool,
            "counterparty_give_pool": bid_details.counterparty_give_pool,
            "counterparty_receive_pool": bid_details.counterparty_receive_pool,
            # pass in a dummy value since not using whitelisting right now
            "whitelist_token_account": SYS_PROGRAM_ID,
            "instruction_sysvar": SYSVAR_INSTRUCTIONS_PUBKEY,
            "system_program": SYS_PROGRAM_ID,
            "token_program": TOKEN_PROGRAM_ID,
        })

        tx = Transaction().add(ix)

        provider = Provider(
            client, wallet
        )

        print('sending exec MSG tx...')
        
        tx_resp = await provider.send(tx, [])

        print(tx_resp)

        await client.confirm_transaction(tx_resp)
        await client.close()



    async def validate_and_exec_bid(self, wallet: Wallet, bid_details: BidDetails):
        """
        Method to validate bid
        Args:
        Returns:
            response (dict): Dictionary containing number of errors (errors)
              and the corresponding error messages (messages)
        """

        client = AsyncClient(self.url)
        res = await client.is_connected()

        swap_order_owner = bid_details.swap_order_owner
        order_id = bid_details.order_id

        seeds = [str.encode("swapOrder"), bytes(swap_order_owner), order_id.to_bytes(8, byteorder="little")]
        [swap_order_addr, _] = PublicKey.find_program_address(
            seeds,
            PROGRAM_ID
        )

        acc = await SwapOrder.fetch(client, swap_order_addr)
        if acc is None:
            raise ValueError("No swap found for user = ", swap_order_owner, ', order id = ', order_id)

        error_dict = await self.validate_bid(wallet, bid_details, acc)
        if error_dict['error'] is not None:
            await client.close()
            return error_dict
        
        ix = exec({
            "authority": wallet.public_key, # signer
            "swap_order": swap_order_addr,
            "give_pool": acc.give_pool,
            "receive_pool": acc.receive_pool,
            "counterparty_give_pool": bid_details.counterparty_give_pool,
            "counterparty_receive_pool": bid_details.counterparty_receive_pool,
            # pass in a dummy value since not using whitelisting right now
            "whitelist_token_account": SYS_PROGRAM_ID,
            "system_program": SYS_PROGRAM_ID,
            "token_program": TOKEN_PROGRAM_ID,
        })

        tx = Transaction().add(ix)

        provider = Provider(
            client, wallet
        )

        print('sending exec tx...')
        
        tx_resp = await provider.send(tx, [])

        print(tx_resp)

        await client.confirm_transaction(tx_resp)
        await client.close()

    async def reclaim_assets_post_fill(self, wallet: Wallet, template: SwapOrderTemplate) -> SwapOrder:
        """
        Method to create offer
        Args:
            offer (dict): Offer dictionary containing necessary parameters 
                to create a new offer
            wallet (Wallet): Wallet class instance
        Raises:
            TypeError: Offer argument is not a valid instance of Offer class
            ExecError: Transaction reverted
        Returns:
            offerId (int): OfferId of the created order
        """

        client = AsyncClient(self.url)
        await client.is_connected()

        pdas: SwapOrderAddresses = await SwapOrderAddresses.from_user(client, wallet.public_key)
    
        ix = create({
            "give_size": template.give_size,
            "receive_size": template.receive_size,
            "expiry": template.expiry,
            "is_counterparty_provided": template.is_counterparty_provided,
            "is_whitelisted": template.is_whitelisted
            }, {
            "payer": wallet.public_key, # signer
            "authority": wallet.public_key,
            "user_orders": pdas.user_orders_addr,
            "swap_order": pdas.swap_order_addr,
            "give_pool": pdas.give_pool_addr,
            "give_mint": template.give_mint,
            "receive_pool": pdas.receive_pool_addr,
            "receive_mint": template.receive_mint,
            "creator_give_pool": template.creator_give_pool,
            "counterparty": template.counterparty,
            "whitelist_token_mint": template.whitelist_token_mint,
            "system_program": SYS_PROGRAM_ID,
            "token_program": TOKEN_PROGRAM_ID,
            "rent": SYSVAR_RENT_PUBKEY
        })

        tx = Transaction().add(ix)

        provider = Provider(
            client, wallet
        )

        print('sending create tx...')
        tx_resp = await provider.send(tx, [])
        print(tx_resp)

        await client.confirm_transaction(tx_resp)

        await asyncio.sleep(1)
        acc = await SwapOrder.fetch(client, pdas.swap_order_address)

        await client.close()

        return acc


    async def cancel_order(self, wallet: Wallet, order_id: int, creator_give_pool: PublicKey) -> SwapOrder:

        client = AsyncClient(self.url)
        await client.is_connected()
       
        pdas : SwapOrderAddresses = await SwapOrderAddresses.from_user(client, wallet.public_key)

        ix = cancel({
        "authority": wallet.public_key,
        "swap_order": pdas.swap_order_address,
        "give_pool": pdas.give_pool_address,
        "creator_give_pool": creator_give_pool,
        "receive_pool": pdas.receive_pool_address,
        "system_program": SYS_PROGRAM_ID,
        "token_program": TOKEN_PROGRAM_ID,
        })

        tx = Transaction().add(ix)

        provider = Provider(
            client, wallet
        )

        print('sending cancel tx...')
        tx_resp = await provider.send(tx, [])
        print(tx_resp)

        await client.confirm_transaction(tx_resp)
        await client.close()
