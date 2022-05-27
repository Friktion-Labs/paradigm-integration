# from anchorpy import Wallet
# from numpy import rec
# from solana.publickey import PublicKey
# import sys
# sys.path.insert(0, "/Users/alexwlezien/Friktion/paradigm-integration/friktion-anchor")
# from friktion_anchor.accounts import SwapOrder, UserOrders
# from friktion_anchor.program_id import PROGRAM_ID
# from friktion_anchor.instructions import create
# from solana.rpc.async_api import AsyncClient
# from .constants import WHITELIST_TOKEN_MINT

# class BidTemplate():

#     price: int


#     def __init__(self, give_size: int, receive_size: int, 
#                 expiry: int, give_mint: PublicKey,
#                 receive_mint: PublicKey, creator_give_pool: PublicKey,
#                 counterparty: PublicKey,
#                 is_counterparty_provided: bool = True, 
#                 is_whitelisted: bool = False,
#                 whitelist_token_mint: PublicKey = WHITELIST_TOKEN_MINT
#         ):
#         self.give_size = give_size
#         self.receive_size = receive_size
#         self.expiry = expiry
#         self.is_counterparty_provided = is_counterparty_provided
#         self.is_whitelisted = is_whitelisted

#         self.give_mint = give_mint
#         self.receive_mint = receive_mint
#         self.creator_give_pool = creator_give_pool
#         self.counterparty = counterparty
#         self.whitelist_token_mint = whitelist_token_mint
