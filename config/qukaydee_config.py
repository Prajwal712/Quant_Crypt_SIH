from src.qkd.qukaydee_provider import QuKayDeeConfig

QUKAYDEE_CONFIG = QuKayDeeConfig(
    account_id="YOUR_ACCOUNT_ID",
    kme_id="kme-1",
    sae_id="sae-1",
    server_ca_cert="certs/server-ca.crt",
    sae_cert="certs/sae-1.crt",
    sae_key="certs/sae-1.key",
)