use anchor_lang::prelude::*;
use anchor_spl::token;
use anchor_spl::token::{Mint, Token, TokenAccount};
use fixed::types::I80F48;

use crate::{SwapOrder, UserOrders};

#[derive(Accounts)]
#[instruction(
    give_size: u64,
    receive_size: u64,
    expiry: u64,
    is_counterparty_provided: bool,
    is_whitelisted: bool,
)]
pub struct Create<'info> {
    #[account(mut, 
        constraint = payer.owner != &crate::id()
    )]
    /// CHECK: just pays for stuff, can be any account. checked by macro that it's not owned by this program haha
    pub payer: AccountInfo<'info>,

    pub authority: Signer<'info>,

    #[account(init_if_needed,
        space=UserOrders::LEN + 8,
        seeds = [
            b"userOrders",
            authority.key().to_bytes().as_ref(),
        ],
        bump,
        payer=payer
    )]
    pub user_orders: Box<Account<'info, UserOrders>>,

    #[account(
      init,
      space=SwapOrder::LEN + 8,
      seeds = [
        b"swapOrder",
        &authority.key().to_bytes()[..],
        user_orders.curr_order_id.to_le_bytes().as_ref()
      ],
      bump,
      payer=payer
    )]
    pub swap_order: Box<Account<'info, SwapOrder>>,

    // volt is maker in this case
    #[account(init, seeds = [
         b"givePool",
        &swap_order.key().to_bytes()[..],
        ], 
        bump,
        payer=payer,
        token::mint=give_mint,
        token::authority=swap_order
    )]
    pub give_pool: Box<Account<'info, TokenAccount>>,
    pub give_mint: Box<Account<'info, Mint>>,

    // counterparty is taker
    #[account(init, seeds = [
         b"receivePool",
        &swap_order.key().to_bytes()[..],
        ], 
        bump,
        payer=payer,
        token::mint=receive_mint,
        token::authority=swap_order
    )]
    pub receive_pool: Box<Account<'info, TokenAccount>>,
    pub receive_mint: Box<Account<'info, Mint>>,

    #[account(mut, token::authority=authority.key())]
    pub creator_give_pool: Box<Account<'info, TokenAccount>>,

    /// CHECK: none necessary since this should just be the pubkey of keypair or pda or counterparty
    pub counterparty: AccountInfo<'info>,

    pub whitelist_token_mint: Box<Account<'info, Mint>>,

    pub system_program: Program<'info, System>,
    pub token_program: Program<'info, Token>,
    pub rent: Sysvar<'info, Rent>,
}

pub fn handler<'a, 'b, 'c, 'info>(
    ctx: Context<'a, 'b, 'c, 'info, Create<'info>>,
    give_size: u64,
    receive_size: u64,
    expiry: u64,
    is_counterparty_provided: bool,
    is_whitelisted: bool,
) -> Result<u64> {
    let give_pool = &ctx.accounts.give_pool;
    let swap_order = &mut ctx.accounts.swap_order;

    swap_order.creator = ctx.accounts.authority.key();
    swap_order.give_size = give_size;
    swap_order.price = I80F48::from_num(receive_size)
        .checked_div(I80F48::from_num(give_size))
        .unwrap()
        .checked_to_num::<f64>()
        .unwrap();
    swap_order.expiry = expiry;
    swap_order.give_mint = ctx.accounts.give_mint.key();
    swap_order.give_pool = give_pool.key();
    swap_order.receive_mint = ctx.accounts.receive_mint.key();
    swap_order.receive_pool = ctx.accounts.receive_pool.key();
    swap_order.receive_size = receive_size;

    swap_order.order_id = ctx.accounts.user_orders.curr_order_id;
    swap_order.bump = *ctx.bumps.get("swap_order").unwrap();

    let possible_cp = ctx.accounts.counterparty.key();
    if is_counterparty_provided {
        swap_order.is_counterparty_provided = true;
        swap_order.counterparty = possible_cp;
    } else {
        swap_order.is_counterparty_provided = false;
    }

    if is_whitelisted {
        swap_order.is_whitelisted = true;
        swap_order.whitelist_token_mint = ctx.accounts.whitelist_token_mint.key();
    } else {
        swap_order.is_whitelisted = false;
    }

    
    token::transfer(
        CpiContext::new(
            ctx.accounts.token_program.to_account_info(),
            token::Transfer {
                from: ctx.accounts.creator_give_pool.to_account_info(),
                to: ctx.accounts.give_pool.to_account_info(),
                authority: ctx.accounts.authority.to_account_info(),
            },
        ),
        swap_order.give_size,
    )?;

    if ctx.accounts.user_orders.curr_order_id == 0 {
        msg!("initializing user orders account");
        ctx.accounts.user_orders.user = ctx.accounts.authority.key();
        ctx.accounts.user_orders.curr_order_id = 0;
    }

    ctx.accounts.user_orders.curr_order_id = ctx
        .accounts
        .user_orders
        .curr_order_id
        .checked_add(1)
        .unwrap();

    msg!("order id = {:?}", ctx.accounts.user_orders.curr_order_id);

    Ok(swap_order.order_id)
}
