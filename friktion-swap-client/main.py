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
    res = await client.is_connected()
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

    # create associated token accounts
    try:
        await give_token.create_associated_token_account(wallet.public_key)
    except RPCException as e:
        print('rpc exception, e = {}'.format(e))

    try:
        await receive_token.create_associated_token_account(wallet.public_key)
    except RPCException as e:
        print('rpc exception, e = {}'.format(e))
         

    offer_1 = await c.create_offer(
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

    # retrieve offer, check values match as expected
    offer_2 = await c.get_offer_details(
        wallet.public_key, offer_1.order_id
    )

    print('swap order 1 = ', offer_1)
    print('swap order 2 = ', offer_2)
    print('should be equal!')
    assert offer_1.status == Created()
    assert offer_2.status == Created()
    assert offer_1.give_size == offer_2.give_size
    assert offer_1.receive_size == offer_2.receive_size
    assert offer_1 == offer_2

    # fill offer via bid
    await c.validate_and_exec_bid(
        wallet, BidDetails(
            wallet.public_key, offer_1.order_id,
            creator_give_pool_key,
            creator_receive_pool_key
        )
    )

    offer_3 = await c.get_offer_details(
        wallet.public_key, offer_1.order_id
    )

    assert offer_3.status == Filled()

    print('Finished!')
    
    print('order post fill: {}'.format(offer_3))

    await client.close()
    
asyncio.run(main_def())