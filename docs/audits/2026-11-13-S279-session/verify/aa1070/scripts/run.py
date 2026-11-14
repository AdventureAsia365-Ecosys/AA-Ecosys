import json, os, subprocess, sys
sec = json.loads(subprocess.run(["aws","secretsmanager","get-secret-value","--secret-id","crm/dev/e2e-test-crm/sen-vang-owner","--profile","aa365-admin","--region","us-west-1","--query","SecretString","--output","text"],capture_output=True,text=True,check=True,stdin=subprocess.DEVNULL).stdout)
env = dict(os.environ, E2ECRMPARTNER="https://portal.lumiguides.it.com", E2ECRMEMAIL=sec["email"], E2ECRMPASSWORD=sec["password"], E2ECRMTOTP=sec["totp_secret"], E2ECRMINCL="probe", S279_OUT=sys.argv[2], NODE_OPTIONS="--max-old-space-size=2048")
r = subprocess.run(["npx","playwright","test","tests/s279-inclusions.spec.ts","--config","playwright.config.ts"],cwd=sys.argv[1],env=env,capture_output=True,text=True)
out = (r.stdout + r.stderr)
for k in ("password","totp_secret"):
    out = out.replace(sec[k], "[redacted]")
print(out[-6000:]); print("exit", r.returncode)
