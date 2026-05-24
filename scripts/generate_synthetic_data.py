"""Generate enterprise-grade synthetic warranty datasets.

Produces three artefacts under ``data/synthetic/``:

    * warranty_claims.csv      ~10k rows of warranty claim records
    * vehicle_telemetry.csv    ~50k rows of operational telemetry
    * technical_documents/     ~15 markdown service/troubleshooting manuals

The schemas mirror what an OEM warranty data lake would look like, so the
RAG / agent pipelines can be exercised end-to-end without any external
dataset licensing.
"""

from __future__ import annotations

import csv
import random
import string
from datetime import datetime, timedelta, timezone
from pathlib import Path

from faker import Faker

RNG_SEED = 7
random.seed(RNG_SEED)
faker = Faker()
Faker.seed(RNG_SEED)

ROOT = Path(__file__).resolve().parents[1] / "data" / "synthetic"
DOCS_DIR = ROOT / "technical_documents"

COMPONENTS = [
    "Battery", "Alternator", "Starter Motor", "Brake Pads", "Brake Rotors",
    "ABS Module", "Transmission", "Drive Shaft", "Wheel Bearing",
    "Air Conditioning Compressor", "Cooling Fan", "Water Pump", "Radiator",
    "Engine Control Unit", "Fuel Pump", "Fuel Injector", "Turbocharger",
    "Catalytic Converter", "Oxygen Sensor", "Spark Plug", "Ignition Coil",
    "Suspension Strut", "CV Joint", "Power Steering Pump", "Infotainment Unit",
]
FAILURE_MODES = {
    "Battery": ["premature discharge", "internal short", "swollen cell", "terminal corrosion"],
    "Alternator": ["voltage regulator failure", "bearing seizure", "diode failure"],
    "Starter Motor": ["solenoid failure", "brush wear", "intermittent engagement"],
    "Brake Pads": ["premature wear", "uneven wear", "noise/squeal"],
    "Brake Rotors": ["warping", "scoring", "corrosion"],
    "ABS Module": ["sensor fault", "control unit failure", "wiring harness short"],
    "Transmission": ["slipping", "harsh shifting", "fluid leak", "torque converter failure"],
    "Drive Shaft": ["vibration", "U-joint failure"],
    "Wheel Bearing": ["roar at speed", "play in wheel", "seizure"],
    "Air Conditioning Compressor": ["clutch failure", "no cooling", "noise"],
    "Cooling Fan": ["motor failure", "blade damage"],
    "Water Pump": ["coolant leak", "bearing failure"],
    "Radiator": ["coolant leak", "internal blockage"],
    "Engine Control Unit": ["CAN bus fault", "firmware corruption"],
    "Fuel Pump": ["pressure loss", "intermittent operation"],
    "Fuel Injector": ["clogging", "leak", "stuck open"],
    "Turbocharger": ["wastegate stuck", "oil leak", "shaft play"],
    "Catalytic Converter": ["efficiency below threshold", "physical damage"],
    "Oxygen Sensor": ["slow response", "heater circuit failure"],
    "Spark Plug": ["fouling", "electrode wear"],
    "Ignition Coil": ["primary winding failure", "secondary insulation breakdown"],
    "Suspension Strut": ["fluid leak", "noise over bumps"],
    "CV Joint": ["clicking under load", "boot tear"],
    "Power Steering Pump": ["whine", "loss of assist"],
    "Infotainment Unit": ["bootloop", "touchscreen unresponsive", "Bluetooth pairing failure"],
}
MAKES = ["Maple", "Northwind", "Apex", "Vanguard", "Helix", "Cobalt", "Solstice"]
MODEL_BY_MAKE = {
    m: [f"{m} {n}" for n in ["S100", "S200", "X500", "EV1", "EV2", "T800"]] for m in MAKES
}
STATUSES = ["closed", "closed", "closed", "in_progress", "open", "denied"]
RESOLUTIONS = [
    "Component replaced under warranty.",
    "Diagnostic performed; software updated.",
    "Customer-induced damage — claim denied.",
    "TSB applied; recalibration performed.",
    "Replaced and aligned; road-tested.",
]
TECHNICIAN_NOTES = [
    "Verified DTC and confirmed customer concern. Replaced affected unit and reflashed module.",
    "Found wiring chafe; repaired harness and resealed grommet.",
    "Pressure tested; replaced seal and torqued to spec.",
    "No fault duplicated; performed extended road test; cleared adaptive learning.",
    "Replaced under campaign 24V-103; functional check complete.",
]


def _vin() -> str:
    alphabet = "".join(c for c in string.ascii_uppercase + string.digits if c not in "IOQ")
    return "".join(random.choices(alphabet, k=17))


def _claim_id(i: int) -> str:
    return f"CLM-{datetime.now(tz=timezone.utc).year}-{i:06d}"


def generate_claims(n_rows: int = 10_000) -> Path:
    out = ROOT / "warranty_claims.csv"
    out.parent.mkdir(parents=True, exist_ok=True)

    with out.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow([
            "claim_id", "vin", "make", "model", "model_year", "fleet_id",
            "component", "failure_mode", "description",
            "repair_cost_usd", "status", "opened_at", "closed_at",
            "mileage_km", "resolution", "technician_notes",
        ])
        for i in range(n_rows):
            comp = random.choice(COMPONENTS)
            mode = random.choice(FAILURE_MODES[comp])
            make = random.choice(MAKES)
            model = random.choice(MODEL_BY_MAKE[make])
            opened = datetime.now(tz=timezone.utc) - timedelta(days=random.randint(1, 720))
            closed = opened + timedelta(days=random.randint(0, 30)) if random.random() < 0.85 else None
            status = random.choice(STATUSES)
            desc = (
                f"Customer reports {mode} on the {comp.lower()}. "
                f"{faker.sentence(nb_words=10)}"
            )
            w.writerow([
                _claim_id(i),
                _vin(),
                make,
                model,
                random.randint(2018, 2026),
                f"FLT-{random.randint(100, 999)}",
                comp,
                mode,
                desc,
                round(random.uniform(50, 4500), 2),
                status,
                opened.isoformat(),
                closed.isoformat() if closed else "",
                round(random.uniform(1_000, 220_000), 1),
                random.choice(RESOLUTIONS),
                random.choice(TECHNICIAN_NOTES),
            ])
    print(f"  ✓ claims  → {out}  ({n_rows:,} rows)")
    return out


def generate_telemetry(n_rows: int = 50_000) -> Path:
    out = ROOT / "vehicle_telemetry.csv"
    metrics = [
        ("battery_voltage", 11.5, 14.6, "P0562"),
        ("engine_temp_c", 70.0, 110.0, "P0217"),
        ("rpm", 600.0, 6500.0, "P0506"),
        ("fuel_pressure_kpa", 250.0, 450.0, "P0087"),
        ("oil_pressure_kpa", 150.0, 600.0, "P0521"),
    ]
    with out.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["vin", "timestamp", "metric", "value", "diagnostic_code", "anomaly_flag"])
        # Pre-allocate a small VIN pool so telemetry can join with claims realistically.
        pool = [_vin() for _ in range(2_000)]
        for _ in range(n_rows):
            vin = random.choice(pool)
            m, low, high, code = random.choice(metrics)
            anomaly = random.random() < 0.04
            if anomaly:
                value = random.choice([low - random.uniform(0.5, 2.0), high + random.uniform(0.5, 5.0)])
            else:
                value = random.uniform(low, high)
            w.writerow([
                vin,
                (datetime.now(tz=timezone.utc) - timedelta(seconds=random.randint(0, 86400 * 30))).isoformat(),
                m,
                round(value, 3),
                code if anomaly else "",
                int(anomaly),
            ])
    print(f"  ✓ telemetry → {out}  ({n_rows:,} rows)")
    return out


_DOC_TEMPLATE = """# {title}

**Document ID:** {doc_id}
**Component:** {component}
**Kind:** {kind}
**Revision:** {rev}
**Published:** {published}

## 1. Purpose

This document defines the diagnostic and repair procedure for failures of the
**{component}** with the symptom pattern: *{symptom}*.

## 2. Applicable Vehicles

- Makes: {makes}
- Model years: 2019 – 2026
- Trim levels: all unless otherwise noted

## 3. Symptoms

- {sym1}
- {sym2}
- {sym3}

## 4. Diagnostic Procedure

1. Connect approved diagnostic scan tool and read all stored DTCs.
2. Verify customer concern and capture a freeze-frame data snapshot.
3. Inspect related wiring harnesses for chafing or corrosion at the connectors.
4. Measure {measurement} using a calibrated multimeter; spec: {spec}.
5. If reading is out of spec, proceed to **Section 5 – Repair Procedure**.
   Otherwise perform extended road test and clear adaptive memory.

## 5. Repair Procedure

> **Safety:** Disconnect the 12V negative battery terminal and wait 90 s
> before working on the affected circuit.

1. Remove fasteners (torque on reinstall: {torque} Nm).
2. Replace the {component} assembly with part number **{part_no}**.
3. Reconnect harness and verify pin retention.
4. Reinstall trim panels and battery terminal.
5. Perform module relearn via the scan tool.

## 6. Verification

- Clear all DTCs and perform a 15-minute mixed-cycle road test.
- Confirm no return of original concern and no new DTCs.
- Document repair on warranty claim {claim_ref}.

## 7. Warranty Coding

- Labour code: **{labour_code}**
- Failure code: **{failure_code}**
- Cause code: **{cause_code}**

## 8. Related Bulletins

- TSB-{tsb1}: Updated calibration for {component} controller
- TSB-{tsb2}: Field action for early-build harnesses

## 9. Revision History

| Rev | Date       | Author          | Notes                       |
|-----|------------|-----------------|-----------------------------|
| A   | 2024-04-12 | Eng. Smith      | Initial release             |
| B   | 2024-09-03 | Eng. Park       | Added freeze-frame guidance |
| C   | 2025-01-21 | Eng. Mendez     | Updated torque spec         |
"""


def generate_documents(n_docs: int = 15) -> list[Path]:
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    components = random.sample(COMPONENTS, k=min(n_docs, len(COMPONENTS)))
    for i, comp in enumerate(components, start=1):
        symptom = random.choice(FAILURE_MODES[comp])
        doc_id = f"SM-{i:03d}"
        path = DOCS_DIR / f"{doc_id.lower()}_{comp.lower().replace(' ', '_')}.md"
        path.write_text(
            _DOC_TEMPLATE.format(
                title=f"{comp} — Diagnostic & Repair Procedure ({symptom})",
                doc_id=doc_id,
                component=comp,
                kind="service_manual" if i % 3 else "troubleshooting_guide",
                rev=random.choice(["A", "B", "C"]),
                published=(datetime.now(tz=timezone.utc) - timedelta(days=random.randint(30, 700))).date(),
                symptom=symptom,
                makes=", ".join(random.sample(MAKES, k=3)),
                sym1=faker.sentence(nb_words=8),
                sym2=faker.sentence(nb_words=8),
                sym3=faker.sentence(nb_words=8),
                measurement=random.choice(["resistance", "voltage", "pressure", "frequency"]),
                spec=random.choice(["0.4 – 0.8 Ω", "11.8 – 14.6 V", "250 – 450 kPa", "0.5 – 1.0 ms"]),
                torque=random.choice([8, 12, 18, 22, 35]),
                part_no=f"{random.randint(10000, 99999)}-{random.choice(['A','B','C'])}{random.randint(10,99)}",
                claim_ref=_claim_id(random.randint(1, 9999)),
                labour_code=f"L{random.randint(100, 999)}",
                failure_code=f"F{random.randint(10, 99)}",
                cause_code=f"C{random.randint(10, 99)}",
                tsb1=f"24V-{random.randint(100, 999)}",
                tsb2=f"25S-{random.randint(100, 999)}",
            ),
            encoding="utf-8",
        )
        written.append(path)
    print(f"  ✓ documents → {DOCS_DIR}  ({len(written)} files)")
    return written


def main() -> None:
    print("Generating synthetic enterprise warranty dataset…")
    ROOT.mkdir(parents=True, exist_ok=True)
    generate_claims()
    generate_telemetry()
    generate_documents()

    # Drop a small sample of each so the repo demonstrates schema even if
    # the full files are .gitignored.
    sample_dir = ROOT / "samples"
    sample_dir.mkdir(exist_ok=True)
    for name in ("warranty_claims.csv", "vehicle_telemetry.csv"):
        src = ROOT / name
        dst = sample_dir / f"sample_{name}"
        with src.open("r", encoding="utf-8") as fi, dst.open("w", encoding="utf-8") as fo:
            for i, line in enumerate(fi):
                if i > 50:
                    break
                fo.write(line)
    print(f"  ✓ samples → {sample_dir}")
    print("Done.")


if __name__ == "__main__":
    main()
