import pytest
from app.core.security import encryptor, get_password_hash, verify_password
from app.services.drivers.factory import OLTDriverFactory
from app.models.models import OltVendor

def test_credentials_encryption():
    """Verify that credentials can be successfully encrypted and decrypted using AES-256-GCM."""
    secret = "my_super_secret_snmp_community_123"
    cipher_text = encryptor.encrypt(secret)
    assert cipher_text != secret
    
    decrypted = encryptor.decrypt(cipher_text)
    assert decrypted == secret

def test_password_hashing():
    """Verify password hashing and verification loops."""
    pwd = "my_noc_password"
    hashed = get_password_hash(pwd)
    assert hashed != pwd
    assert verify_password(pwd, hashed) is True
    assert verify_password("wrong_password", hashed) is False

def test_driver_factory():
    """Verify factory returns correct OLT driver classes."""
    driver = OLTDriverFactory.get_driver(
        vendor=OltVendor.HUAWEI,
        ip_address="192.168.1.100",
        snmp_community="public"
    )
    assert driver.__class__.__name__ == "HuaweiDriver"
    assert driver.ip_address == "192.168.1.100"
    assert driver.snmp_community == "public"

    generic_driver = OLTDriverFactory.get_driver(
        vendor=OltVendor.GENERIC,
        ip_address="192.168.1.200"
    )
    assert generic_driver.__class__.__name__ == "GenericSnmpDriver"
