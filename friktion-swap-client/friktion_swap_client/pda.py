from typing import Dict, List
from friktion_swap_client.friktion_anchor.accounts.swap_order import SwapOrder
from friktion_swap_client.friktion_anchor.accounts.user_orders import UserOrders
from friktion_swap_client.friktion_anchor.program_id import PROGRAM_ID
from httpx import AsyncClient
from solana.publickey import PublicKey

def find_swap_order_address(user: PublicKey, order_id: int) -> List[PublicKey, int]:
    seeds = [str.encode("swapOrder"), bytes(user), order_id.to_bytes(8, byteorder="little")]
    return PublicKey.find_program_address(
        seeds,
        PROGRAM_ID
    )

def find_user_orders_address(user: PublicKey) -> List[PublicKey, int]:
    user_orders_seeds = [str.encode("userOrders"), bytes(user)]
    return PublicKey.find_program_address(
        user_orders_seeds,
        PROGRAM_ID
    )

def find_give_pool_address(swap_order_addr: PublicKey) -> List[PublicKey, int]:
    give_pool_seeds = [ str.encode("givePool"), bytes(swap_order_addr)]
    return PublicKey.find_program_address(
        give_pool_seeds,
        PROGRAM_ID
    )

def find_receive_pool_address(swap_order_addr: PublicKey) -> List[PublicKey, int]:
    receive_pool_seeds = [ str.encode("receivePool"), bytes(swap_order_addr)]
    return PublicKey.find_program_address(
            receive_pool_seeds,
            PROGRAM_ID
        )



class SwapOrderAddresses():
    user_orders_address: PublicKey
    swap_order_address: PublicKey
    give_pool_address: PublicKey
    receive_pool_address: PublicKey

    def __init__(self, user: PublicKey, order_id: int):
        self.user_orders_address = find_user_orders_address(user)
        self.swap_order_address = find_swap_order_address(user, order_id)
        self.give_pool_address = find_give_pool_address(self.swap_order_address)
        self.receive_pool_address = find_receive_pool_address(self.swap_order_address)

    @staticmethod
    async def from_user(client: AsyncClient, user: PublicKey, order_id: int = None):
        if order_id is None:
            user_orders_address = find_user_orders_address(user)  
            user_orders = await UserOrders.fetch(client, user_orders_address)
            if user_orders is None:
                order_id = 0
            else:
                order_id = user_orders.curr_order_id
        return SwapOrderAddresses(user, order_id)