"""Summarize measured JTL by sampler and by sequential thread-group stage."""
import csv
import json
import math
import re
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]/"evidence"/"tooling"


def stats(records):
    values=sorted(int(row["elapsed"]) for row in records)
    start=min(int(row["timeStamp"]) for row in records)
    end=max(int(row["timeStamp"])+int(row["elapsed"]) for row in records)
    return {"samples":len(values),"average_ms":round(sum(values)/len(values),3),
            "p90_ms":values[math.ceil(.90*len(values))-1],"p95_ms":values[math.ceil(.95*len(values))-1],"max_ms":max(values),
            "error_percent":round(100*sum(row["success"]!="true" for row in records)/len(records),4),
            "throughput_per_second":round(len(values)/((end-start)/1000),4),
            "started_utc":datetime.fromtimestamp(start/1000,timezone.utc).isoformat(),
            "finished_utc":datetime.fromtimestamp(end/1000,timezone.utc).isoformat(),"sample_window_seconds":round((end-start)/1000,3)}


def main():
    all_metrics={}
    for name in ("load","step"):
        folder=ROOT/f"jmeter-{name}"
        source=folder/"results.jtl"
        if not source.exists():continue
        with source.open(encoding="utf-8-sig",newline="") as stream:rows=list(csv.DictReader(stream))
        groups=defaultdict(list)
        for row in rows:
            stage=re.sub(r"\s+\d+-\d+$","",row["threadName"])
            groups[stage].append(row)
        result={"source":str(source),"percentile_method":"nearest-rank, all samples including failures","overall":stats(rows),"stages":{}}
        for stage,records in groups.items():
            labels=defaultdict(list)
            for row in records:labels[row["label"]].append(row)
            result["stages"][stage]={"overall":stats(records),"samplers":{label:stats(values) for label,values in labels.items()}}
        (folder/"metrics-by-stage.json").write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
        all_metrics[name]=result
    checks=[]
    if "load" in all_metrics:
        for requirement,label,threshold in [("NFR-01","Search",800),("NFR-02","Notifications",900)]:
            metrics=next(iter(all_metrics["load"]["stages"].values()))["samplers"][label]
            checks.append({"requirement":requirement,"scenario":"load 2 users / 300s","sampler":label,"threshold_ms":threshold,"p95_ms":metrics["p95_ms"],"error_percent":metrics["error_percent"],"result":"Pass" if metrics["p95_ms"]<=threshold and metrics["error_percent"]<1 else "Fail"})
    if "step" in all_metrics:
        for stage,values in all_metrics["step"]["stages"].items():
            for label in ("List","Types"):
                metrics=values["samplers"][label]
                checks.append({"requirement":"NFR-03","scenario":stage,"sampler":label,"threshold_ms":1000,"p95_ms":metrics["p95_ms"],"error_percent":metrics["error_percent"],"result":"Pass" if metrics["p95_ms"]<=1000 and metrics["error_percent"]<1 else "Fail"})
    (ROOT/"nfr-comparison.json").write_text(json.dumps({"scope":"Local ShiloSkin automated evaluation; not VPS or partner testing","checks":checks},ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps(checks,ensure_ascii=False,indent=2))


if __name__=="__main__":main()
