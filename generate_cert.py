"""Generate a self-signed SSL certificate for local HTTPS access."""
import subprocess
import pathlib
import os

ROOT = pathlib.Path(__file__).parent
cert_file = ROOT / "cert.pem"
key_file = ROOT / "key.pem"

print("Generating self-signed SSL certificate for local HTTPS...")
print("(This is safe for local network use)")

try:
    # Generate self-signed certificate valid for 365 days
    cmd = [
        "openssl", "req", "-x509", "-newkey", "rsa:2048",
        "-keyout", str(key_file),
        "-out", str(cert_file),
        "-days", "365",
        "-nodes",
        "-subj", "/CN=localhost"
    ]
    
    subprocess.run(cmd, check=True, capture_output=True)
    print(f"✅ Certificate created: {cert_file}")
    print(f"✅ Key created: {key_file}")
    print("\nNow you can run: python web_app.py")
    print("Access at: https://YOUR_COMPUTER_IP:5000")
    print("(Accept the security warning on iPhone)")
    
except FileNotFoundError:
    print("❌ OpenSSL not found. Trying with Python cryptography library...")
    try:
        from cryptography import x509
        from cryptography.x509.oid import NameOID
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.backends import default_backend
        from cryptography.hazmat.primitives.asymmetric import rsa
        from cryptography.hazmat.primitives import serialization
        import datetime
        
        # Generate private key
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend()
        )
        
        # Generate certificate
        subject = issuer = x509.Name([
            x509.NameAttribute(NameOID.COMMON_NAME, u"localhost"),
        ])
        
        cert = x509.CertificateBuilder().subject_name(
            subject
        ).issuer_name(
            issuer
        ).public_key(
            private_key.public_key()
        ).serial_number(
            x509.random_serial_number()
        ).not_valid_before(
            datetime.datetime.utcnow()
        ).not_valid_after(
            datetime.datetime.utcnow() + datetime.timedelta(days=365)
        ).add_extension(
            x509.SubjectAlternativeName([
                x509.DNSName(u"localhost"),
                x509.DNSName(u"127.0.0.1"),
            ]),
            critical=False,
        ).sign(private_key, hashes.SHA256(), default_backend())
        
        # Write certificate
        with open(cert_file, "wb") as f:
            f.write(cert.public_bytes(serialization.Encoding.PEM))
        
        # Write private key
        with open(key_file, "wb") as f:
            f.write(private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.TraditionalOpenSSL,
                encryption_algorithm=serialization.NoEncryption()
            ))
        
        print(f"✅ Certificate created: {cert_file}")
        print(f"✅ Key created: {key_file}")
        print("\nNow you can run: python web_app.py")
        print("Access at: https://YOUR_COMPUTER_IP:5000")
        print("(Accept the security warning on iPhone)")
        
    except ImportError:
        print("❌ cryptography library not found.")
        print("Install it with: pip install cryptography")
        print("Then run this script again.")
