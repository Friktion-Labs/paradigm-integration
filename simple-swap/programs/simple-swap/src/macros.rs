#[macro_export]
macro_rules! gen_swap_signer_seeds {
    ($swap:expr) => {
        &[
            b"swapOrder" as &[u8],
            &$swap.creator.to_bytes(),
            &$swap.order_id.to_le_bytes(),
            &[$swap.bump],
        ]
    };
}
