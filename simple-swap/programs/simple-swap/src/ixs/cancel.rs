use crate::gen_swap_signer_seeds;
use crate::ErrorCode::*;
use crate::SwapOrder;
use anchor_lang::prelude::*;
use anchor_spl::token;
use anchor_spl::token::{Mint, Token, TokenAccount};
use fixed::types::I80F48;
use std::str::FromStr;

#[derive(Accounts)]
#[instruction()]
pub struct Cancel<'info> {
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

    #[account(mut, token::authority=swap_order.creator)]
    pub creator_give_pool: Box<Account<'info, TokenAccount>>,

    #[account(mut, address=swap_order.give_pool)]
    pub give_pool: Box<Account<'info, TokenAccount>>,

    #[account(mut, address=swap_order.receive_pool)]
    pub receive_pool: Box<Account<'info, TokenAccount>>,

    pub token_program: Program<'info, Token>,
    pub system_program: Program<'info, System>,
}

pub fn handler<'a, 'b, 'c, 'info>(ctx: Context<'a, 'b, 'c, 'info, Cancel<'info>>) -> Result<()> {
    let swap_order = &mut ctx.accounts.swap_order;

    swap_order.cancel(&ctx.accounts.authority)?;

    let give_pool = &ctx.accounts.give_pool;
    let receive_pool = &ctx.accounts.receive_pool;

    require!(receive_pool.amount == 0, ReceivePoolMustBeEmpty);

    if give_pool.amount > 0 {
        let seeds = gen_swap_signer_seeds!(swap_order);
        token::transfer(
            CpiContext::new_with_signer(
                ctx.accounts.token_program.to_account_info(),
                token::Transfer {
                    from: ctx.accounts.give_pool.to_account_info(),
                    to: ctx.accounts.creator_give_pool.to_account_info(),
                    authority: ctx.accounts.swap_order.to_account_info(),
                },
                &[seeds],
            ),
            give_pool.amount,
        )?;
    }

    Ok(())
}
