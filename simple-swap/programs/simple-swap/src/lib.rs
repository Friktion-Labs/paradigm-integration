use anchor_lang::prelude::*;

pub mod ixs;
pub mod macros;
pub mod swap;

pub use ixs::*;
pub use swap::*;

declare_id!("SwpWEbAhitpix22gbX28zah7g8JiA1FRwVdPe4XohQb");
#[program]
pub mod simple_swap {
    use crate::{
        ixs::{self, Cancel, Create, Exec},
        Claim,
    };
    use anchor_lang::prelude::*;
    pub fn create<'a, 'b, 'c, 'info>(
        ctx: Context<'a, 'b, 'c, 'info, Create<'info>>,
        give_size: u64,
        receive_size: u64,
        expiry: u64,
        is_counterparty_provided: bool,
        is_whitelisted: bool,
    ) -> Result<u64> {
        ixs::create::handler(
            ctx,
            give_size,
            receive_size,
            expiry,
            is_counterparty_provided,
            is_whitelisted,
        )
    }

    pub fn exec<'a, 'b, 'c, 'info>(ctx: Context<'a, 'b, 'c, 'info, Exec<'info>>) -> Result<()> {
        ixs::exec::handler(ctx)
    }

    pub fn cancel<'a, 'b, 'c, 'info>(ctx: Context<'a, 'b, 'c, 'info, Cancel<'info>>) -> Result<()> {
        ixs::cancel::handler(ctx)
    }

    pub fn claim<'a, 'b, 'c, 'info>(ctx: Context<'a, 'b, 'c, 'info, Claim<'info>>) -> Result<()> {
        ixs::claim::handler(ctx)
    }
}

#[error_code]
pub enum ErrorCode {
    // swap errors
    #[msg("invalid counter party")]
    InvalidCounterParty,

    #[msg("invalid give pool")]
    InvalidGivePool,
    #[msg("invalid receive pool")]
    InvalidReceivePool,
    #[msg("counterparty must be signer")]
    CounterpartyMustBeSigner,
    #[msg("swap order was filled")]
    SwapOrderWasFilled,
    #[msg("swap order was canceled")]
    SwapOrderWasCanceled,
    #[msg("swap order is disabled")]
    SwapOrderIsDisabled,
    #[msg("swap order has expired")]
    SwapOrderHasExpired,
    #[msg("swap order must be disabled to close")]
    SwapOrderMustBeDisabledToClose,
    #[msg("order already filled")]
    OrderAlreadyFilled,
    #[msg("order already cancelled")]
    OrderAlreadyCancelled,

    #[msg("invalid whitelist token account mint")]
    InvalidWhitelistTokenAccountMint,
    #[msg("min 1 mm token")]
    MustHaveAtLeastOneMarketMakerAccessToken,

    #[msg("receive pool must be empty")]
    ReceivePoolMustBeEmpty,
    #[msg("give pool must be empty")]
    GivePoolMustBeEmpty,
    #[msg("order must be filled")]
    OrderMustBeFilled,

    #[msg("order must be trading")]
    OrderMustBeTrading,
}
