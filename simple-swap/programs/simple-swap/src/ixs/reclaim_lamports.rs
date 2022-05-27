use std::str::FromStr;

use crate::{gen_swap_signer_seeds, SwapOrder};

use anchor_lang::prelude::*;
use anchor_spl::token::{self, Mint, Token, TokenAccount};
use fixed::types::I80F48;

#[derive(Accounts)]
#[instruction()]
pub struct ReclaimLamportsSwapOrder<'info> {
    #[account(mut, address=swap_order.creator)]
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

    #[account(mut, address=swap_order.give_pool)]
    pub give_pool: Box<Account<'info, TokenAccount>>,

    #[account(mut, address=swap_order.receive_pool)]
    pub receive_pool: Box<Account<'info, TokenAccount>>,

    pub token_program: Program<'info, Token>,

    pub system_program: Program<'info, System>,
}

pub fn handler<'a, 'b, 'c, 'info>(
    ctx: Context<'a, 'b, 'c, 'info, ReclaimLamportsSwapOrder<'info>>,
) -> Result<()> {
    let swap_order = &ctx.accounts.swap_order;
    swap_order.check_is_disabled()?;

    swap_order.check_creator(&ctx.accounts.authority)?;

    let give_pool = &ctx.accounts.give_pool;
    let receive_pool = &ctx.accounts.receive_pool;

    require!(give_pool.amount == 0, GivePoolMustBeEmpty);
    require!(receive_pool.amount == 0, ReceivePoolMustBeEmpty);

    let seeds = gen_swap_signer_seeds!(&ctx.accounts.swap_order);
    token::close_account(CpiContext::new_with_signer(
        ctx.accounts.token_program.to_account_info(),
        token::CloseAccount {
            account: ctx.accounts.give_pool.to_account_info(),
            authority: ctx.accounts.swap_order.to_account_info(),
            destination: ctx.accounts.authority.to_account_info(),
        },
        &[seeds],
    ))?;

    token::close_account(CpiContext::new_with_signer(
        ctx.accounts.token_program.to_account_info(),
        token::CloseAccount {
            account: ctx.accounts.receive_pool.to_account_info(),
            authority: ctx.accounts.swap_order.to_account_info(),
            destination: ctx.accounts.authority.to_account_info(),
        },
        &[seeds],
    ))?;

    // TODO: close SwapOrder PDA account

    Ok(())
}
