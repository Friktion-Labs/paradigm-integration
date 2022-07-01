use crate::{gen_swap_signer_seeds, SwapOrder};
use anchor_lang::prelude::*;
use anchor_spl::token::{self, Token, TokenAccount};

#[derive(Accounts)]
pub struct Exec<'info> {
    #[account(mut)]
    pub authority: Signer<'info>,

    #[account(
      mut,
      seeds = [
        b"swapOrder",
        &swap_order.creator.key().to_bytes()[..],
        swap_order.order_id.to_le_bytes().as_ref()
      ],
      bump,
    )]
    pub swap_order: Box<Account<'info, SwapOrder>>,

    // volt is maker in this case
    #[account(mut, address=swap_order.give_pool)]
    pub give_pool: Box<Account<'info, TokenAccount>>,

    // counterparty is taker
    #[account(mut, address=swap_order.receive_pool)]
    pub receive_pool: Box<Account<'info, TokenAccount>>,

    #[account(mut)]
    pub counterparty_receive_pool: Box<Account<'info, TokenAccount>>,
    #[account(mut)]
    pub counterparty_give_pool: Box<Account<'info, TokenAccount>>,

    /// CHECK: may not be necessary to use if swap order isnt' whitelisted,
    ///  so pass in as account info and later validate
    pub whitelist_token_account: AccountInfo<'info>,

    pub system_program: Program<'info, System>,
    pub token_program: Program<'info, Token>,
}

pub fn handler<'a, 'b, 'c, 'info>(ctx: Context<'a, 'b, 'c, 'info, Exec<'info>>) -> Result<()> {
    let swap_order = &mut ctx.accounts.swap_order;

    swap_order.check_is_trading()?;

    swap_order.check_pools(&ctx.accounts.give_pool, &ctx.accounts.receive_pool)?;

    token::transfer(
        CpiContext::new(
            ctx.accounts.token_program.to_account_info(),
            token::Transfer {
                from: ctx.accounts.counterparty_receive_pool.to_account_info(),
                to: ctx.accounts.receive_pool.to_account_info(),
                authority: ctx.accounts.authority.to_account_info(),
            },
        ),
        swap_order.receive_size,
    )?;

    let seeds = gen_swap_signer_seeds!(swap_order);
    token::transfer(
        CpiContext::new_with_signer(
            ctx.accounts.token_program.to_account_info(),
            token::Transfer {
                from: ctx.accounts.give_pool.to_account_info(),
                to: ctx.accounts.counterparty_give_pool.to_account_info(),
                authority: swap_order.to_account_info(),
            },
            &[seeds],
        ),
        swap_order.give_size,
    )?;

    swap_order.fill(
        &ctx.accounts.authority,
        &ctx.accounts.whitelist_token_account,
        false,
    )?;

    Ok(())
}
