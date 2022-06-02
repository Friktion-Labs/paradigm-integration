# Friktion/Paradigm Intregration

## Environment Setup

1. Install solana 1.9.15 and anchor 0.24.2 (solana dev tooling). For instructions regarding this see here: https://project-serum.github.io/anchor/getting-started/installation.html
    (NOTE: if you're using M1 macOS, it's possible you'll have some trouble when running solana programs locally.)

2. Make sure you have python3.9+ setup. The SDK requires 3.9+

## Testing

if you're running into weird errors check you've run through the below steps
- Create a keypair in ~/.config/solana/id.json
- set ANCHOR_PROVIDER_URL (rpc url) and ANCHOR_WALLET (file that has keypair of wallet) bash env variables (export them in terminal)
