//In JS you can use web3.Ed25519Program.createInstructionWith{Public,Private}Key
// https://discord.com/channels/428295358100013066/517163444747894795/954351771155853323
use crate::{gen_swap_signer_seeds, swap_admin, SwapOrder};
use anchor_lang::prelude::*;
use anchor_spl::token::{self, Token, TokenAccount};
use bytemuck::{Pod, Zeroable};
use serde::{Deserialize, Serialize};
use solana_program::{
    ed25519_program,
    sysvar::instructions::{load_current_index_checked, load_instruction_at_checked},
};

use crate::ErrorCode;

pub const PUBKEY_SERIALIZED_SIZE: usize = 32;
pub const SIGNATURE_SERIALIZED_SIZE: usize = 64;
pub const SIGNATURE_OFFSETS_SERIALIZED_SIZE: usize = 14;
// bytemuck requires structures to be aligned
pub const SIGNATURE_OFFSETS_START: usize = 2;
pub const DATA_START: usize = SIGNATURE_OFFSETS_SERIALIZED_SIZE + SIGNATURE_OFFSETS_START;

// fn get_data_slice<'a>(
//     data: &'a [u8],
//     instruction_datas: &'a [&[u8]],
//     instruction_index: u16,
//     offset_start: u16,
//     size: usize,
// ) -> Result<&'a [u8]> {
//     let instruction = if instruction_index == u16::MAX {
//         data
//     } else {
//         let signature_index = instruction_index as usize;
//         if signature_index >= instruction_datas.len() {
//             return Err(PrecompileError::InvalidDataOffsets);
//         }
//         instruction_datas[signature_index]
//     };

//     let start = offset_start as usize;
//     let end = start.saturating_add(size);
//     if end > instruction.len() {
//         return Err(PrecompileError::InvalidDataOffsets);
//     }

//     Ok(&instruction[start..end])
// }

#[derive(Default, Debug, Serialize, Deserialize, Copy, Clone, Zeroable, Pod)]
#[repr(C)]
pub struct Ed25519SignatureOffsets {
    signature_offset: u16,             // offset to ed25519 signature of 64 bytes
    signature_instruction_index: u16,  // instruction index to find signature
    public_key_offset: u16,            // offset to public key of 32 bytes
    public_key_instruction_index: u16, // instruction index to find public key
    message_data_offset: u16,          // offset to start of message data
    message_data_size: u16,            // size of message data
    message_instruction_index: u16,    // index of instruction data to get message data
}

#[must_use]
fn make_ed25519_instruction(instruction_index: u8, message_len: u16, data_start: u16) -> Vec<u8> {
    let num_signatures: u8 = 1;
    let public_key_offset = DATA_START;
    let signature_offset = public_key_offset.saturating_add(PUBKEY_SERIALIZED_SIZE);
    let message_data_offset = signature_offset.saturating_add(SIGNATURE_SERIALIZED_SIZE);

    let offsets = Ed25519SignatureOffsets {
        signature_offset: signature_offset as u16,
        signature_instruction_index: u16::MAX,
        public_key_offset: public_key_offset as u16,
        public_key_instruction_index: u16::MAX,
        message_data_offset: message_data_offset as u16,
        message_data_size: message_len as u16,
        message_instruction_index: u16::MAX,
    };

    let bin_offsets = bincode::serialize(&offsets).unwrap();

    // let mut instruction_data = Vec::with_capacity(
    //   DATA_START
    //       .saturating_add(SIGNATURE_SERIALIZED_SIZE)
    //       .saturating_add(PUBKEY_SERIALIZED_SIZE)
    //       .saturating_add(message.len()),
    // );

    let mut instruction_data = Vec::with_capacity(1 + bin_offsets.len());
    instruction_data.push(num_signatures);
    instruction_data.extend(&bin_offsets);
    instruction_data
}

#[derive(Accounts)]
pub struct ExecMsg<'info> {
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

    /// CHECK: instruction sysvar, checked by load_instruction_at_checked
    pub instruction_sysvar: AccountInfo<'info>,
    pub system_program: Program<'info, System>,
    pub token_program: Program<'info, Token>,
}

pub fn handler<'a, 'b, 'c, 'info>(
    ctx: Context<'a, 'b, 'c, 'info, ExecMsg<'info>>,
    signature: String,
    caller: Pubkey,
    raw_msg: String,
) -> Result<()> {
    // require!(
    //     ctx.accounts.authority.key() == swap_admin::id(),
    //     InvalidSwapAdmin
    // );

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

    // let sysvar_info = &ctx.accounts.instruction_sysvar.to_account_info();
    // let current_instruction = load_current_index_checked(sysvar_info)?;
    // let current_instruction = u8::try_from(current_instruction).unwrap();

    // let index = current_instruction - 1;
    // let ix = solana_program::sysvar::instructions::load_instruction_at_checked(
    //     index.into(),
    //     sysvar_info,
    // )
    // .unwrap();

    // require!(
    //     ix.program_id == ed25519_program::id(),
    //     InvalidEd25519Program
    // );

    // if let Ok(instr) = load_instruction_at_checked(index.into(), sysvar_info) {
    //     if ed25519_program::check_id(&instr.program_id) {
    //         let reference_instruction =
    //             make_ed25519_instruction(current_instruction, raw_msg.len().try_into().unwrap(), 9);
    //         if reference_instruction != instr.data {
    //             msg!(
    //                 "wrong ed25519 instruction data, instruction={}, reference={}",
    //                 &hex::encode(&instr.data),
    //                 &hex::encode(&reference_instruction)
    //             );
    //             return Err(ProgramError::InvalidInstructionData.into());
    //         }
    //     } else {
    //         msg!(
    //             "Incorrect Program Id: index={:?}, sysvar_info={:?}, instr.program_id={:?}",
    //             index,
    //             sysvar_info,
    //             instr.program_id
    //         );
    //         return Err(ErrorCode::InvalidEd25519Program.into());
    //     }
    // }

    swap_order.fill(
        &ctx.accounts.authority,
        &ctx.accounts.whitelist_token_account,
        true,
    )?;

    Ok(())
}
