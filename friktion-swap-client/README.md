# Friktion Swap Client for Paradigm Integration

This python SDK enables interaction with the on-chain Friktion swap program. This includes the ability to create, retrieve, and execute a swap order. The swap order represents the exchange of 2 assets in prerecorded static amounts.

## Testing

The following command will run a script that 1. creates an offer 2. fetches the offer (and asserts that it is available to execute), 3. fills the offer with a corresponding bid
```cd friktion-swap-client && python3 main.py```

## Basic Usage

```main.py``` should be used as a reference whenever possible. However, if it is not available below are some samples of python code using the SDK.

**Creating Offer**
```python   
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
```

**Retrieving Offer**
```python
offer_2 = await c.get_offer_details(
        wallet.public_key, offer_1.order_id
    )
```

**Executing Bid**
```python
await c.validate_and_exec_bid(
        wallet, BidDetails(
            wallet.public_key, offer_1.order_id,
            creator_give_pool_key,
            creator_receive_pool_key
        )
    )
```


## Swap Order Struct Layout

```rust
pub struct SwapOrder {
    pub creator: Pubkey,

    pub price: f64,
    pub expiry: u64,

    pub give_size: u64,
    pub give_mint: Pubkey,
    pub give_pool: Pubkey,

    pub receive_size: u64,
    pub receive_mint: Pubkey,
    pub receive_pool: Pubkey,

    pub is_counterparty_provided: bool,
    pub counterparty: Pubkey,

    pub is_whitelisted: bool,
    pub whitelist_token_mint: Pubkey,

    pub is_disabled: bool,
    pub status: OrderStatus,

    pub order_id: u64,

    pub bump: u8,
}
``