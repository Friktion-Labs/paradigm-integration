#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------------
""" Module to call Swap contract """
# ---------------------------------------------------------------------------
# Imports
# ---------------------------------------------------------------------------
from dataclasses import asdict

from shutil import ExecError
from anchorpy import Wallet
from anchorpy import Provider

from solana.publickey import PublicKey
import sys
sys.path.insert(0, "/Users/alexwlezien/Friktion/paradigm-integration/friktion-anchor")
from friktion_anchor.accounts import SwapOrder, UserOrders
from friktion_anchor.program_id import PROGRAM_ID
from solana.sysvar import SYSVAR_RENT_PUBKEY
from friktion_anchor.instructions import create
from solana.rpc.async_api import AsyncClient
from solana.system_program import SYS_PROGRAM_ID
from .swap_order_template import SwapOrderTemplate
from spl.token.constants import ASSOCIATED_TOKEN_PROGRAM_ID, TOKEN_PROGRAM_ID
from solana.transaction import Transaction


# ---------------------------------------------------------------------------
# Swap Program
# ---------------------------------------------------------------------------
class SwapContract():
    """
    Object used to interact with swap contract
    Args:
        config (ContractConfig): Configuration to setup the Contract
    """

    async def get_offer_details(self, user: PublicKey, order_id: int) -> dict:
        """
        Method to get bid details
        Args:
            offer_id (int): Offer ID
        Raises:
            ValueError: The argument is not a valid offer
        Returns:
            details (SwapOrder): Offer details
        """

        client = AsyncClient("https://api.mainnet-beta.solana.com")
        res = await client.is_connected()

        seeds = [bytes("swapOrder"), bytes(user), bytes(order_id)]
        [addr, bump] = PublicKey.find_program_address(
            seeds,
            PROGRAM_ID
        )
        
        acc = await SwapOrder.fetch(client, addr)
        if acc is None:
            raise ValueError("No swap found for user = ", user, ', order id = ', order_id)

        await client.close()
        return acc

    async def validate_bid(self, wallet: Wallet, swap_order_owner: PublicKey, order_id: int) -> str:
        """
        Method to validate bid
        Args:
        Returns:
            response (dict): Dictionary containing number of errors (errors)
              and the corresponding error messages (messages)
        """

        client = AsyncClient("https://api.mainnet-beta.solana.com")
        res = await client.is_connected()

        seeds = [bytes("swapOrder"), bytes(user), bytes(order_id)]
        [addr, bump] = PublicKey.find_program_address(
            seeds,
            PROGRAM_ID
        )
        

        # ix = exec({
        # "give_size": template.give_size,
        # "receive_size": template.receive_size,
        # "expiry": template.expiry,
        # "is_counterparty_provided": template.is_counterparty_provided,
        # "is_whitelisted": template.is_whitelisted
        # }, {
        # "payer": wallet.public_key, # signer
        # "authority": wallet.public_key,
        # "user_orders": user_orders_addr,
        # "swap_order": swap_order_addr,
        # "give_pool": give_pool_addr,
        # "give_mint": template.give_mint,
        # "receive_pool": receive_pool_addr,
        # "receive_mint": template.receive_mint,
        # "creator_give_pool": template.creator_give_pool,
        # "counterparty": template.counterparty,
        # "whitelist_token_mint": template.whitelist_token_mint,
        # "system_program": SYS_PROGRAM_ID,
        # "token_program": TOKEN_PROGRAM_ID,
        # "rent": SYSVAR_RENT_PUBKEY
        # })

        tx = Transaction().add(ix)

        # provider = Provider.local()
        provider = Provider(
            client, wallet
        )

        tx_resp = await provider.send(tx, [])

        await client.close()
        # response = self.contract.functions.check(asdict(bid)).call()

    async def create_offer(self, wallet: Wallet, template: SwapOrderTemplate) -> str:
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

        client = AsyncClient("https://api.mainnet-beta.solana.com")
        res = await client.is_connected()

        user_orders_seeds = [bytes("userOrders"), bytes(wallet.public_key)]
        [user_orders_addr, _] = PublicKey.find_program_address(
            user_orders_seeds,
            PROGRAM_ID
        )

        acc = await UserOrders.fetch(client, user_orders_addr)
        if acc is None:
            order_id = 0
        else:
            order_id = acc.curr_order_id


        swap_order_seeds = [bytes("swapOrder"), bytes(wallet.public_key), bytes(order_id)]
        [swap_order_addr, _] = PublicKey.find_program_address(
            swap_order_seeds,
            PROGRAM_ID
        )

        give_pool_seeds = [ bytes("givePool"), bytes(swap_order_addr)]
        [give_pool_addr, _] = PublicKey.find_program_address(
            give_pool_seeds,
            PROGRAM_ID
        )
    
        receive_pool_seeds = [ bytes("receivePool"), bytes(swap_order_addr)]
        [receive_pool_addr, _] = PublicKey.find_program_address(
            receive_pool_seeds,
            PROGRAM_ID
        )
    



        ix = create({
        "give_size": template.give_size,
        "receive_size": template.receive_size,
        "expiry": template.expiry,
        "is_counterparty_provided": template.is_counterparty_provided,
        "is_whitelisted": template.is_whitelisted
        }, {
        "payer": wallet.public_key, # signer
        "authority": wallet.public_key,
        "user_orders": user_orders_addr,
        "swap_order": swap_order_addr,
        "give_pool": give_pool_addr,
        "give_mint": template.give_mint,
        "receive_pool": receive_pool_addr,
        "receive_mint": template.receive_mint,
        "creator_give_pool": template.creator_give_pool,
        "counterparty": template.counterparty,
        "whitelist_token_mint": template.whitelist_token_mint,
        "system_program": SYS_PROGRAM_ID,
        "token_program": TOKEN_PROGRAM_ID,
        "rent": SYSVAR_RENT_PUBKEY
        })

        tx = Transaction().add(ix)

        # provider = Provider.local()
        provider = Provider(
            client, wallet
        )

        tx_resp = await provider.send(tx, [])

        # need to convert this to string
        await client.confirm_transaction(tx_resp)

        await client.close()