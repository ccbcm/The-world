"""One-time owner setup: retain a private signing backup outside the repository.
Never print the key, password, GitHub token or encrypted payload.
"""
import base64, datetime, json, os, secrets, subprocess, sys, urllib.request
from pathlib import Path
sys.path.insert(0, str(Path(os.environ['TEMP']) / 'ccbcm-signing-tools'))
from nacl.public import PublicKey, SealedBox
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.serialization import pkcs12
from cryptography.x509.oid import NameOID

folder = Path(os.environ['LOCALAPPDATA']) / 'CCBCM' / 'Signing'
folder.mkdir(parents=True, exist_ok=True)
# The owner prepares this private directory with only their account granted access.
# Verify it before writing secrets; never weaken or silently ignore a failed ACL.
acl_script = (
 '$p=$env:LOCALAPPDATA+"/CCBCM/Signing";$a=Get-Acl -LiteralPath $p;'
 '$s=[Security.Principal.WindowsIdentity]::GetCurrent().User;'
 'if(!$a.AreAccessRulesProtected){exit 1};'
 'foreach($r in $a.GetAccessRules($true,$true,[Security.Principal.SecurityIdentifier])){'
 'if($r.AccessControlType -eq "Allow" -and $r.IdentityReference -ne $s){exit 1}}')
acl_result = subprocess.run(['pwsh', '-NoProfile', '-EncodedCommand',
    base64.b64encode(acl_script.encode('utf-16-le')).decode()], capture_output=True)
if acl_result.returncode:
    raise RuntimeError('Unable to restrict signing backup: '+acl_result.stderr.decode(errors='replace'))
store, password_file = folder / 'ccbcm-release.p12', folder / 'password.txt'
if store.exists() != password_file.exists():
    raise RuntimeError('Incomplete signing backup; do not overwrite it')
if not store.exists():
    password = secrets.token_urlsafe(36)
    key = rsa.generate_private_key(public_exponent=65537, key_size=3072)
    name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, 'CCBCM')])
    now = datetime.datetime.now(datetime.timezone.utc)
    cert = (x509.CertificateBuilder().subject_name(name).issuer_name(name)
            .public_key(key.public_key()).serial_number(x509.random_serial_number())
            .not_valid_before(now - datetime.timedelta(days=1))
            .not_valid_after(now + datetime.timedelta(days=365*30))
            .sign(key, hashes.SHA256()))
    store.write_bytes(pkcs12.serialize_key_and_certificates(b'ccbcm', key, cert, None,
                      serialization.BestAvailableEncryption(password.encode())))
    password_file.write_text(password, encoding='utf-8')
password = password_file.read_text(encoding='utf-8')
_, cert, _ = pkcs12.load_key_and_certificates(store.read_bytes(), password.encode())
credential = subprocess.run(['git','-c','credential.interactive=false','credential','fill'],
    input='protocol=https\nhost=github.com\nusername=ccbcm\n\n', text=True, capture_output=True, check=True).stdout
token = next(line[9:] for line in credential.splitlines() if line.startswith('password='))
api = 'https://api.github.com/repos/ccbcm/The-world/actions/secrets'
def request(url, data=None):
    req = urllib.request.Request(url, data=json.dumps(data).encode() if data else None,
        headers={'Authorization': 'Bearer '+token, 'Accept':'application/vnd.github+json',
                 'Content-Type':'application/json', 'User-Agent':'CCBCM-release-setup'},
        method='PUT' if data else 'GET')
    with urllib.request.urlopen(req, timeout=30) as response:
        raw = response.read()
        return json.loads(raw) if raw else None
public = request(api+'/public-key')
box = SealedBox(PublicKey(base64.b64decode(public['key'])))
for name, value in [('ANDROID_KEYSTORE', base64.b64encode(store.read_bytes()).decode()),
                    ('ANDROID_STORE_PASSWORD', password)]:
    request(api+'/'+name, {'key_id':public['key_id'],
        'encrypted_value':base64.b64encode(box.encrypt(value.encode())).decode()})
print('Signing secrets configured; private backup retained outside Git.')
print('Certificate SHA256:', cert.fingerprint(hashes.SHA256()).hex())
