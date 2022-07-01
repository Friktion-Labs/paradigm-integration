use anchor_lang::prelude::*;
use anchor_spl::token::TokenAccount;

#[derive(Debug, Clone, Copy, AnchorSerialize, AnchorDeserialize, PartialEq)]
#[repr(u32)]
pub enum OrderStatus {
    Created,
    Canceled,
    Filled,
    Disabled,
}

#[account]
pub struct UserOrders {
    pub user: Pubkey,
    pub curr_order_id: u64,
}

impl UserOrders {
    pub const LEN: usize = 40;
}

#[account]
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

impl SwapOrder {
    pub const LEN: usize = 32 + 8 * 3 + 32 * 2 + 8 + 32 * 2 + 1 + 32 + 1 + 32 + 1 + 4 + 8 + 1;

    pub fn check_is_trading(&self) -> Result<()> {
        require!(self.status != OrderStatus::Filled, SwapOrderWasFilled);
        require!(self.status != OrderStatus::Canceled, SwapOrderWasCanceled);
        require!(!self.is_disabled, SwapOrderIsDisabled);

        let now: u64 = Clock::get()?.unix_timestamp as u64;
        require!(now < self.expiry, SwapOrderHasExpired);
        Ok(())
    }

    pub fn check_is_disabled(&self) -> Result<()> {
        require!(self.is_disabled, SwapOrderMustBeDisabledToClose);
        Ok(())
    }

    pub fn check_pools(
        &self,
        give_pool: &Account<TokenAccount>,
        receive_pool: &Account<TokenAccount>,
    ) -> Result<()> {
        require!(give_pool.key() == self.give_pool, InvalidGivePool);
        require!(receive_pool.key() == self.receive_pool, InvalidReceivePool);

        Ok(())
    }

    pub fn fill(
        &mut self,
        counterparty: &AccountInfo,
        whitelist_token_account_raw: &AccountInfo,
        msg_verified: bool,
    ) -> Result<()> {
        require!(self.status == OrderStatus::Created, OrderMustBeTrading);

        if self.is_counterparty_provided {
            require!(
                msg_verified || counterparty.is_signer,
                CounterpartyMustBeSigner
            );
            require!(counterparty.key == &self.counterparty, InvalidCounterParty);
        }

        if self.is_whitelisted {
            let whitelist_token_account =
                Account::<TokenAccount>::try_from(whitelist_token_account_raw).unwrap();
            require!(
                whitelist_token_account.mint == self.whitelist_token_mint,
                InvalidWhitelistTokenAccountMint
            );
            require!(
                whitelist_token_account.owner == counterparty.key(),
                InvalidWhitelistTokenAccountMint
            );
            require!(
                whitelist_token_account.amount > 0,
                MustHaveAtLeastOneMarketMakerAccessToken
            )
        }

        self.status = OrderStatus::Filled;
        Ok(())
    }

    pub fn check_creator(&self, creator: &AccountInfo) -> Result<()> {
        require!(creator.is_signer, CounterpartyMustBeSigner);
        require!(creator.key == &self.creator, InvalidCounterParty);

        Ok(())
    }

    pub fn cancel(&mut self, creator: &AccountInfo) -> Result<()> {
        require!(self.status == OrderStatus::Created, OrderMustBeTrading);
        self.check_creator(creator)?;

        self.status = OrderStatus::Canceled;
        Ok(())
    }

    pub fn disable(&mut self, _creator: &AccountInfo) -> Result<()> {
        self.is_disabled = true;

        Ok(())
    }
}
