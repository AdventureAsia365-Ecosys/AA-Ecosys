"""Second CloudWatch batch for AA-838: per-role connections, Lambda, job backlog, whole-window stats."""
import json
import sys

START = "2026-09-28T06:00:00Z"
END = "2026-10-28T06:00:00Z"
OUT = sys.argv[1]
WIN = 30 * 86400
queries = []


def q(qid, ns, metric, dims, stat, period=3600):
    queries.append({"Id": qid, "MetricStat": {"Metric": {"Namespace": ns, "MetricName": metric,
                    "Dimensions": dims}, "Period": period, "Stat": stat}, "ReturnData": True})


DB = [{"Name": "DBInstanceIdentifier", "Value": "aa-cis-dev-db"}]
q("w_conn_p95", "AWS/RDS", "DatabaseConnections", DB, "p95", WIN)
q("w_conn_p99", "AWS/RDS", "DatabaseConnections", DB, "p99", WIN)
q("w_conn_max", "AWS/RDS", "DatabaseConnections", DB, "Maximum", WIN)
q("w_cpu_p95", "AWS/RDS", "CPUUtilization", DB, "p95", WIN)
q("w_cpu_avg", "AWS/RDS", "CPUUtilization", DB, "Average", WIN)
q("w_surplus", "AWS/RDS", "CPUSurplusCreditsCharged", DB, "Sum", WIN)
q("w_rlat_p95", "AWS/RDS", "ReadLatency", DB, "p95", WIN)
q("w_wlat_p95", "AWS/RDS", "WriteLatency", DB, "p95", WIN)
q("w_riops_p95", "AWS/RDS", "ReadIOPS", DB, "p95", WIN)
q("w_wiops_p95", "AWS/RDS", "WriteIOPS", DB, "p95", WIN)

for i, role in enumerate(["cis_app", "aa_app_user", "tripplanner", "booking", "crm_app", "db_migrator"]):
    dims = [{"Name": "Role", "Value": role}]
    q(f"role{i}_max", "AA/RDS", "RoleConnections", dims, "Maximum")
    q(f"role{i}_pctmax", "AA/RDS", "RoleConnectionLimitPct", dims, "Maximum")

for i, fn in enumerate(["aa-tripplanner-dev-browse", "aa-tripplanner-dev-assembly"]):
    dims = [{"Name": "FunctionName", "Value": fn}]
    q(f"lam{i}_conc", "AWS/Lambda", "ConcurrentExecutions", dims, "Maximum")
    q(f"lam{i}_thr", "AWS/Lambda", "Throttles", dims, "Sum")
    q(f"lam{i}_inv", "AWS/Lambda", "Invocations", dims, "Sum")
    q(f"lam{i}_err", "AWS/Lambda", "Errors", dims, "Sum")
    q(f"lam{i}_dur_p95", "AWS/Lambda", "Duration", dims, "p95")
q("lamacct_conc", "AWS/Lambda", "ConcurrentExecutions", [], "Maximum")

for i, ns in enumerate(["AA/Jobs/CIS", "AA/Jobs/Booking"]):
    q(f"job{i}_age", ns, "OldestQueuedAgeSeconds", [], "Maximum")
    q(f"job{i}_over", ns, "OverdueRunningJobs", [], "Maximum")

with open(OUT, "w") as fh:
    json.dump({"MetricDataQueries": queries, "StartTime": START, "EndTime": END,
               "ScanBy": "TimestampAscending"}, fh, indent=1)
print(len(queries), "queries")
