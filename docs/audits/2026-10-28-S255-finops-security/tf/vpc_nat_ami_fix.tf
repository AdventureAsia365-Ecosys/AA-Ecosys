# =============================================================================
# DRAFT (S255, finding S-4) — NOT applied. Target: infra/AA-CIS-Infra/modules/vpc/main.tf, data "aws_ami" "nat_al2023".
#
# Bug: the name filter "al2023-ami-*-arm64" also matches the ECS-optimized image, and most_recent picked it:
# the running NAT instance (t4g.nano) runs al2023-ami-ecs-hvm-2023.0.20260701-kernel-6.1-arm64. Its ECS agent then
# calls ecs:RegisterContainerInstance with the NAT instance role in a loop: 3,586 CloudTrail events on 26/10/2026
# (~0.11 M/month, ~0.5 USD/month of GuardDuty once AA-873 enables it, plus a useless agent on a 0.5 GB host).
#
# Fix, two parts:
#   a) Today (no replacement): stop the agent on the running instance through SSM Run Command
#      (document AWS-RunShellScript, target tag Name = aa-cis-dev-nat-instance, command
#      "systemctl disable --now ecs"; orchestrator step, single-line CLI). Verify: the next day's CloudTrail has no
#      RegisterContainerInstance by aa-cis-nat-instance-role.
#   b) Code: pin the plain AL2023 image through the public SSM parameter (resolves to ami-097a0378c5bf95711 on
#      28/10/2026). aws_instance.nat already has lifecycle { ignore_changes = [ami] } (line ~184), so this is a
#      no-op for the running instance and only applies to the next deliberate replacement. Also add
#      "systemctl disable --now ecs || true" to user_data as a guard.
# =============================================================================

data "aws_ssm_parameter" "nat_al2023_arm64" {
  name = "/aws/service/ami-amazon-linux-latest/al2023-ami-kernel-6.1-arm64"
}

# In aws_instance.nat (modules/vpc/main.tf line ~153):
#   ami = data.aws_ssm_parameter.nat_al2023_arm64.value   # was data.aws_ami.nat_al2023.id (keep ignore_changes = [ami])
#
# Alternative with the existing data source: tighten the filter to the minimal-kernel name
#   values = ["al2023-ami-2023.*-kernel-6.1-arm64"]
