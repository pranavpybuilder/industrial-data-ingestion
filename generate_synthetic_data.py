#!/usr/bin/env python
"""
Synthetic Data Generator for Offline Endurance Intelligence System.

Generates realistic test data for all data sources:
- PLC (sensor data)
- SAP (maintenance orders)
- RFID (tag scans)
- Report Excel (production metrics)
- Operational Excel (operational logs)
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import csv
import json

# Set random seed for reproducibility
np.random.seed(42)

DATA_DIR = "synthetic_data"


def generate_plc_data(rows: int = 50) -> pd.DataFrame:
    """
    Generate PLC sensor data matching schema.
    
    Schema expects: machine_id, event_time, parameter_name, parameter_value
    This is LONG FORMAT - one row per parameter per timestamp
    """
    now = datetime.now()
    
    machine_ids = ["MACH001", "MACH002"]
    parameter_names = ["temperature", "pressure", "vibration", "energy", "rpm"]
    
    records = []
    
    for i in range(rows):
        # Generate past timestamps (going back 250 hours)
        timestamp = (now - timedelta(hours=250-i)).isoformat()
        machine_id = np.random.choice(machine_ids)
        
        for param_name in parameter_names:
            # Generate realistic values per parameter type
            if param_name == "temperature":
                value = np.random.normal(loc=65, scale=5)
                value = np.clip(value, 40, 100)
            elif param_name == "pressure":
                value = np.random.normal(loc=6.5, scale=1.0)
                value = np.clip(value, 4.0, 9.0)
            elif param_name == "vibration":
                value = np.random.exponential(scale=0.8)
                value = np.clip(value, 0.1, 7.5)
            elif param_name == "energy":
                value = np.random.normal(loc=2800, scale=400)
                value = np.clip(value, 1500, 4500)
            else:  # rpm
                value = np.random.normal(loc=1200, scale=100)
                value = np.clip(value, 800, 1600)
            
            records.append({
                "machine_id": machine_id,
                "event_time": timestamp,
                "parameter_name": param_name,
                "parameter_value": round(value, 3),
            })
    
    # Shuffle records
    np.random.shuffle(records)
    return pd.DataFrame(records)


def generate_sap_data(rows: int = 30) -> pd.DataFrame:
    """
    Generate SAP maintenance order data matching schema.
    
    Required: order_number, equipment_id, start_date
    Optional: finish_date, order_type, breakdown_indicator, etc.
    """
    now = datetime.now()
    
    order_numbers = [f"PM{100000+i}" for i in range(rows)]
    equipment_ids = [f"EQ{np.random.randint(1, 20):03d}" for _ in range(rows)]
    
    # Dates going back (past dates)
    start_dates = [
        (now - timedelta(days=rows-i)).isoformat()
        for i in range(rows)
    ]
    
    # Some orders overdue, some completed
    finish_dates = []
    for i, start_date in enumerate(start_dates):
        if i % 3 == 0:
            # Overdue orders (no finish date)
            finish_dates.append(None)
        else:
            # Completed orders
            days_to_complete = np.random.randint(1, 10)
            finish_dates.append(
                (datetime.fromisoformat(start_date) + timedelta(days=days_to_complete)).isoformat()
            )
    
    order_types = [np.random.choice(["PM", "CM", "OP"]) for _ in range(rows)]
    
    breakdown_indicators = [
        True if np.random.random() > 0.7 else False
        for _ in range(rows)
    ]
    
    return pd.DataFrame({
        "order_number": order_numbers,
        "equipment_id": equipment_ids,
        "start_date": start_dates,
        "finish_date": finish_dates,
        "order_type": order_types,
        "breakdown_indicator": breakdown_indicators,
    })


def generate_rfid_data(rows: int = 100) -> pd.DataFrame:
    """
    Generate RFID tag scan data matching schema.
    
    Required: tag_id, event_time, reader_id
    Optional: event_type, location, signal_strength
    """
    now = datetime.now()
    
    timestamps = [
        (now - timedelta(minutes=rows-i)).isoformat()
        for i in range(rows)
    ]
    
    tag_ids = [f"TAG{np.random.randint(1000, 9999)}" for _ in range(rows)]
    reader_ids = [f"READER{np.random.randint(1, 5)}" for _ in range(rows)]
    
    event_types = [np.random.choice(["scan", "read", "detection"]) for _ in range(rows)]
    locations = [np.random.choice(["zone_a", "zone_b", "zone_c"]) for _ in range(rows)]
    
    signal_strength = np.random.normal(loc=-60, scale=10, size=rows)
    signal_strength = np.clip(signal_strength, -95, -30)
    
    # Add some data gaps (reader offline periods)
    gap_indices = np.random.choice(rows, size=int(rows * 0.05), replace=False)
    for idx in gap_indices:
        signal_strength[idx] = -100  # Out of range
    
    return pd.DataFrame({
        "tag_id": tag_ids,
        "event_time": timestamps,
        "reader_id": reader_ids,
        "event_type": event_types,
        "location": locations,
        "signal_strength": signal_strength.round(1),
    })


def generate_report_excel_data(rows: int = 25) -> pd.DataFrame:
    """
    Generate Report Excel data matching SAP-derived schema.
    
    Required: date, equipment_number, machine_name, downtime
    Optional: machine_description, user_state, why1-5, etc.
    """
    now = datetime.now()
    
    dates = [
        (now - timedelta(days=rows-i)).isoformat()
        for i in range(rows)
    ]
    
    equipment_numbers = [f"EQ{np.random.randint(1000, 9999)}" for _ in range(rows)]
    machine_names = [f"MACHINE_{np.random.randint(1, 15)}" for _ in range(rows)]
    machine_descriptions = [f"Production Unit {chr(65 + i%10)}" for i in range(rows)]
    
    downtimes = np.random.exponential(scale=2.0, size=rows)
    downtimes = np.clip(downtimes, 0, 16)
    
    user_states = [np.random.choice(["RUL", "RUNNING", "STOPPED"]) for _ in range(rows)]
    
    why_categories = ["Mechanical Failure", "Electrical Issue", "Software Bug", "Maintenance", "Unknown"]
    why1 = [np.random.choice(why_categories) for _ in range(rows)]
    
    return pd.DataFrame({
        "date": dates,
        "equipment_number": equipment_numbers,
        "machine_name": machine_names,
        "machine_description": machine_descriptions,
        "user_state": user_states,
        "downtime": downtimes.round(2),
        "why1": why1,
    })


def generate_operational_excel_data(rows: int = 40) -> pd.DataFrame:
    """
    Generate Operational Excel data (schema-less).
    
    Flexible format for operational logs with no strict schema validation:
    - Timestamps
    - Event types
    - Equipment IDs
    - Event descriptions
    - Status codes
    """
    now = datetime.now()
    
    timestamps = [
        (now - timedelta(hours=i//4)).isoformat()
        for i in range(rows)
    ]
    
    event_types = ["startup", "shutdown", "alert", "maintenance", "idle", "running"]
    events = [np.random.choice(event_types) for _ in range(rows)]
    
    equipment_ids = [f"EQ{np.random.randint(1, 15):03d}" for _ in range(rows)]
    
    descriptions = [
        f"{event.upper()}: Equipment {eid} - Status OK" if np.random.random() > 0.1
        else f"{event.upper()}: Equipment {eid} - ANOMALY DETECTED"
        for event, eid in zip(events, equipment_ids)
    ]
    
    status_codes = [np.random.choice([200, 201, 400, 500]) for _ in range(rows)]
    
    return pd.DataFrame({
        "timestamp": timestamps,
        "event_type": events,
        "equipment_id": equipment_ids,
        "description": descriptions,
        "status_code": status_codes,
    })


def save_all_datasets():
    """Generate and save all synthetic datasets."""
    
    print("=" * 60)
    print("SYNTHETIC DATA GENERATION")
    print("=" * 60)
    
    # Generate PLC data
    print("\n[1/5] Generating PLC data...")
    plc_df = generate_plc_data(rows=50)
    plc_path = f"{DATA_DIR}/plc_sample.csv"
    plc_df.to_csv(plc_path, index=False)
    print(f"✓ Saved {plc_path} ({len(plc_df)} rows)")
    print(f"  Columns: {', '.join(plc_df.columns)}")
    
    # Generate SAP data
    print("\n[2/5] Generating SAP data...")
    sap_df = generate_sap_data(rows=30)
    sap_path = f"{DATA_DIR}/sap_orders.csv"
    sap_df.to_csv(sap_path, index=False)
    print(f"✓ Saved {sap_path} ({len(sap_df)} rows)")
    print(f"  Columns: {', '.join(sap_df.columns)}")
    
    # Generate RFID data
    print("\n[3/5] Generating RFID data...")
    rfid_df = generate_rfid_data(rows=100)
    rfid_path = f"{DATA_DIR}/rfid_scans.csv"
    rfid_df.to_csv(rfid_path, index=False)
    print(f"✓ Saved {rfid_path} ({len(rfid_df)} rows)")
    print(f"  Columns: {', '.join(rfid_df.columns)}")
    
    # Generate Report Excel data
    print("\n[4/5] Generating Report Excel data...")
    report_df = generate_report_excel_data(rows=25)
    report_path = f"{DATA_DIR}/report_excel_sample.csv"
    report_df.to_csv(report_path, index=False)
    print(f"✓ Saved {report_path} ({len(report_df)} rows)")
    print(f"  Columns: {', '.join(report_df.columns)}")
    
    # Generate Operational Excel data
    print("\n[5/5] Generating Operational Excel data...")
    ops_df = generate_operational_excel_data(rows=40)
    ops_path = f"{DATA_DIR}/operational_excel_sample.csv"
    ops_df.to_csv(ops_path, index=False)
    print(f"✓ Saved {ops_path} ({len(ops_df)} rows)")
    print(f"  Columns: {', '.join(ops_df.columns)}")
    
    print("\n" + "=" * 60)
    print("ALL SYNTHETIC DATA GENERATED")
    print("=" * 60)
    print(f"\nLocation: {DATA_DIR}/")
    print("\nTest with:")
    print("  .\venv\Scripts\python -m app.main synthetic_data/plc_sample.csv plc")
    print("  .\venv\Scripts\python -m app.main synthetic_data/sap_orders.csv sap")
    print("  .\venv\Scripts\python -m app.main synthetic_data/rfid_scans.csv rfid")
    print("  .\venv\Scripts\python -m app.main synthetic_data/report_excel_sample.csv report_excel")
    print("  .\venv\Scripts\python -m app.main synthetic_data/operational_excel_sample.csv operational_excel")


if __name__ == "__main__":
    save_all_datasets()
