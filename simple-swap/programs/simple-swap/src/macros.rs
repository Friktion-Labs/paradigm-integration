#[macro_export]
macro_rules! gen_swap_signer_seeds {
    ($swap:expr) => {
        &[
            b"swapOrder" as &[u8],
            &$swap.creator.to_bytes(),
            &$swap.give_size.to_le_bytes(),
            &$swap.receive_size.to_le_bytes(),
            &$swap.expiry.to_le_bytes(),
            &$swap.give_mint.to_bytes(),
            &$swap.receive_mint.to_bytes(),
            &[$swap.bump],
        ]
    };
}
