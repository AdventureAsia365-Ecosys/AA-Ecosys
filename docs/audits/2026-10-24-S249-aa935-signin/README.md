# AA-935 live sign-in check (S249, 24/10/2026)

Seeded synthetic agency owner `e2e-test-crm-sen-vang-owner` (e-mail code, managed login on `auth.lumiguides.it.com`, partner host `https://partner-dev.lumiguides.it.com`, web `aa-crm-dev-web:5`, API ready crm-005). Script: Playwright, 1440×900 + 390 px, code read from the SES e2e mailbox (never logged or screenshotted).

Before the fixes: managed login 403 (no branding on EXTERNAL clients → AA-CIS-Infra #336), sign-out 403 + settings date empty (AA-Partner #14), container health check failing (Fargate HOSTNAME → AA-Partner #15).

## Checks (13/13 pass)

```
[PASS] redirect to managed login :: chain: auth.lumiguides.it.com/login -> auth.lumiguides.it.com/login
[PASS] managed login asks for e-mail code :: heading "Check your email" at https://auth.lumiguides.it.com/verifyCode
[PASS] code mail arrived in SES bucket :: new mail for e2e-test-crm-sen-vang-owner@e2e-mail.lumiguides.it.com found within 3 s
[PASS] signed in, back on partner host :: https://partner-dev.lumiguides.it.com/
[PASS] sidebar shows "Lữ hành Sen Vàng" :: agency card: "Lữ hành Sen Vàng Chủ đại lý · Đại lý thử nghiệm"
[PASS] single agency lands on Home (/) :: landing path /; switch-agency link present: 0
[PASS] Content studio link in sidebar :: text "Mở Content studio" href https://portal.lumiguides.it.com/portal/dashboard
[PASS] theme toggle switches to dark :: aria-label "Giao diện: dark", body bg rgb(15, 20, 27)
[PASS] /settings date reads in vi-VN / en-AU style :: typed "03/04/2026" (placeholder "DD/MM/YYYY") -> "Hiểu là: 3 thg 4, 2026"; agency "Lữ hành Sen Vàng"; url /settings
[PASS] 390 px: shell renders, drawer opens with agency card :: drawer agency visible true; horizontal overflow 0px
[PASS] /robots.txt 200 without a session :: status 200 body "User-agent: * | Disallow: / | "
[PASS] sign out :: landed https://partner-dev.lumiguides.it.com/signed-out; heading "You are signed out"; partner cookies with value: []
[PASS] protected page after sign-out -> sign-in (asks e-mail again) :: chain: auth.lumiguides.it.com/login -> auth.lumiguides.it.com/login -> auth.lumiguides.it.com/login; email field visible true
```

Screenshots: the PNG files in this folder.
