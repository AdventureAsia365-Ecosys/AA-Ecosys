"""Build CloudWatch GetMetricData inputs for the AA-838 capacity review (read-only)."""
import json
import sys

START = "2026-09-28T06:00:00Z"
END = "2026-10-28T06:00:00Z"
OUT = sys.argv[1]

DB = [{"Name": "DBInstanceIdentifier", "Value": "aa-cis-dev-db"}]
CLUSTER = "aa-cis-dev-cluster"
SERVICES = [
    "aa-cis-dev-api",
    "aa-cis-dev-worker",
    "aa-booking-dev-api",
    "aa-crm-dev-api",
    "aa-crm-dev-web",
    "aa-crm-dev-portal",
]

queries = []


def q(qid, ns, metric, dims, stat, period=3600):
    queries.append({
        "Id": qid,
        "MetricStat": {
            "Metric": {"Namespace": ns, "MetricName": metric, "Dimensions": dims},
            "Period": period,
            "Stat": stat,
        },
        "ReturnData": True,
    })


rds = [
    ("cpu_avg", "CPUUtilization", "Average"),
    ("cpu_max", "CPUUtilization", "Maximum"),
    ("mem_min", "FreeableMemory", "Minimum"),
    ("mem_avg", "FreeableMemory", "Average"),
    ("stor_min", "FreeStorageSpace", "Minimum"),
    ("conn_max", "DatabaseConnections", "Maximum"),
    ("conn_avg", "DatabaseConnections", "Average"),
    ("conn_p95", "DatabaseConnections", "p95"),
    ("riops_avg", "ReadIOPS", "Average"),
    ("riops_max", "ReadIOPS", "Maximum"),
    ("wiops_avg", "WriteIOPS", "Average"),
    ("wiops_max", "WriteIOPS", "Maximum"),
    ("rlat_avg", "ReadLatency", "Average"),
    ("rlat_max", "ReadLatency", "Maximum"),
    ("wlat_avg", "WriteLatency", "Average"),
    ("wlat_max", "WriteLatency", "Maximum"),
    ("dqd_max", "DiskQueueDepth", "Maximum"),
    ("credit_bal_min", "CPUCreditBalance", "Minimum"),
    ("surplus_charged", "CPUSurplusCreditsCharged", "Sum"),
    ("surplus_bal_max", "CPUSurplusCreditBalance", "Maximum"),
    ("swap_max", "SwapUsage", "Maximum"),
    ("txid_max", "MaximumUsedTransactionIDs", "Maximum"),
    ("rthr_avg", "ReadThroughput", "Average"),
    ("wthr_avg", "WriteThroughput", "Average"),
]
for qid, metric, stat in rds:
    q(qid, "AWS/RDS", metric, DB, stat)

for i, svc in enumerate(SERVICES):
    dims = [{"Name": "ClusterName", "Value": CLUSTER}, {"Name": "ServiceName", "Value": svc}]
    q(f"ecs{i}_cpu_avg", "AWS/ECS", "CPUUtilization", dims, "Average")
    q(f"ecs{i}_cpu_max", "AWS/ECS", "CPUUtilization", dims, "Maximum")
    q(f"ecs{i}_mem_avg", "AWS/ECS", "MemoryUtilization", dims, "Average")
    q(f"ecs{i}_mem_max", "AWS/ECS", "MemoryUtilization", dims, "Maximum")

with open(OUT, "w") as fh:
    json.dump({"MetricDataQueries": queries, "StartTime": START, "EndTime": END,
               "ScanBy": "TimestampAscending"}, fh, indent=1)
print(len(queries), "queries")
