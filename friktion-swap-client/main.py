from friktion_swap_client.swap import *
import time
import asyncio
from spl.token.async_client import AsyncToken
from friktion_swap_client.friktion_anchor.types.order_status import *
from solana.rpc.core import RPCException
from spl.token.instructions import get_associated_token_address

c = SwapContract(Network.DEVNET)

wallet = Wallet.local()

# devnet
GIVE_MINT = PublicKey("E6Z6zLzk8MWY3TY8E87mr88FhGowEPJTeMWzkqtL6qkF")
RECEIVE_MINT = PublicKey("C6kYXcaRUMqeBF5fhg165RWU7AnpT9z92fvKNoMqjmz6")

# make counterparty itself for purposes of testing
COUNTERPARTY = wallet.public_key
# dummy value for testing. not using whitelist tokens so shouldn't change much
WHITELIST_TOKEN_MINT = GIVE_MINT

# mainnet
# GIVE_MINT = PublicKey("")
# RECEIVE_MINT = PublicKey("")

async def main_def():

    client = AsyncClient(c.url)
    await client.is_connected()
    
    give_token = AsyncToken(
        client,
        GIVE_MINT,
        TOKEN_PROGRAM_ID,
        wallet.payer
    )
    receive_token = AsyncToken(
        client,
        RECEIVE_MINT,
        TOKEN_PROGRAM_ID,
        wallet.payer
    )

    ### create offer ###

    creator_give_pool_key = get_associated_token_address(
        wallet.public_key,
        GIVE_MINT
    )

    creator_receive_pool_key = get_associated_token_address(
        wallet.public_key,
        RECEIVE_MINT
    )

    counterparty_receive_pool_key = get_associated_token_address(
        wallet.public_key,
        RECEIVE_MINT
    )

    # create associated token accounts
    try:
        await give_token.create_associated_token_account(wallet.public_key)
    except RPCException as e:
        print('DEBUG: already created associated token account. Ignore this usually!\n e = {}'.format(e))

    try:
        await receive_token.create_associated_token_account(wallet.public_key)
    except RPCException as e:
        print('DEBUG: already created associated token account. Ignore this usually!\n e = {}'.format(e))
         

    try:
        print('current allowance: ', c.verify_allowance(wallet, RECEIVE_MINT, counterparty_receive_pool_key))
    except AssertionError:
        print("allowance needs to be delegated, doing...")
        c.give_allowance(wallet, counterparty_receive_pool_key, RECEIVE_MINT,  MIN_REQUIRED_ALLOWANCE)
        c.verify_allowance(wallet, RECEIVE_MINT, counterparty_receive_pool_key)

    print('1. creator initializes swap offer...')

    offer = await c.create_offer(
        wallet, SwapOrderTemplate(
            1, 1, int(time.time()) + 10000,
            GIVE_MINT, RECEIVE_MINT,
            creator_give_pool_key,
            COUNTERPARTY,
            True,
            False,
            WHITELIST_TOKEN_MINT,
        )
    )

    assert offer.status == Created()

    print('2. taker executes bid against offer...')

    bid_details =  BidDetails(
            wallet.public_key, offer.order_id,
            creator_give_pool_key,
            creator_receive_pool_key
        )
    # fill offer via bid
    await c.validate_bid(
        wallet,
        bid_details,
        offer
    )

    bid_msg = bid_details.as_signed_msg(wallet, 1, 1)

    await c.validate_and_exec_bid_msg(wallet, bid_details, bid_msg)

    offer_3 = await c.get_offer_details(
        wallet.public_key, offer.order_id
    )

    assert offer_3.status == Filled()

    print('order post fill: {}'.format(offer_3))

    print('3. creator reclaims assets...')

    print('Finished!')
    
    await client.close()
    
asyncio.run(main_def())