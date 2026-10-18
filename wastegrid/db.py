"""
Database Architecture and Persistence Layer for WasteGrid 2.0.
Uses SQLite for local development with PostgreSQL-compatible schema architecture.
Manages users, facilities, waste sources, vehicles, allocations, alerts, citizen reports,
scenarios, and system audit logs.
"""

import hashlib
import json
import os
import sqlite3
from datetime import datetime, timezone

DB_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "wastegrid.db"
)


def get_connection():
    """Get a thread-safe connection to the SQLite database."""
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def hash_password(password, salt=None):
    """Secure password hashing using PBKDF2-HMAC-SHA256 with 100,000 iterations."""
    if not salt:
        salt = os.urandom(16).hex()
    hashed = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        100000,
    ).hex()
    return hashed, salt


def verify_password(password, hashed_password, salt):
    """Verify password against stored hash and salt."""
    recomputed, _ = hash_password(password, salt)
    return recomputed == hashed_password


def init_db():
    """Initialize all database tables and seed default records if first run."""
    conn = get_connection()
    c = conn.cursor()

    # 1. Users Table
    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        salt TEXT NOT NULL,
        role TEXT NOT NULL, -- state, district, municipality, factory, admin
        authority_title TEXT NOT NULL,
        jurisdiction TEXT NOT NULL,
        full_name TEXT NOT NULL,
        email TEXT NOT NULL,
        is_active INTEGER DEFAULT 1,
        created_at TEXT NOT NULL,
        last_login TEXT
    )
    """)

    # 2. Facilities Table (Dynamic, unlimited)
    c.execute("""
    CREATE TABLE IF NOT EXISTS facilities (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        type TEXT NOT NULL, -- biocompost, anaerobic_digester, mrf, waste_to_energy
        accepts TEXT NOT NULL, -- wet, dry, mixed
        capacity_kg REAL NOT NULL,
        current_load_kg REAL DEFAULT 0,
        distance_km REAL NOT NULL,
        latitude REAL NOT NULL,
        longitude REAL NOT NULL,
        status TEXT DEFAULT 'online', -- online, offline, maintenance
        operating_hours TEXT DEFAULT '06:00 - 22:00',
        efficiency_pct REAL DEFAULT 95.0,
        cost_per_ton REAL DEFAULT 350.0,
        carbon_factor_kg REAL DEFAULT 0.05
    )
    """)

    # 3. Waste Sources / Wards Table
    c.execute("""
    CREATE TABLE IF NOT EXISTS waste_sources (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        ward_code TEXT NOT NULL,
        zone TEXT NOT NULL,
        baseline_kg REAL NOT NULL,
        waste_type TEXT NOT NULL, -- wet, dry
        latitude REAL NOT NULL,
        longitude REAL NOT NULL,
        active_spike_kg REAL DEFAULT 0,
        modifier REAL DEFAULT 1.0
    )
    """)

    # 4. Vehicles / Truck Fleet Table
    c.execute("""
    CREATE TABLE IF NOT EXISTS vehicles (
        id TEXT PRIMARY KEY,
        driver_name TEXT NOT NULL,
        phone TEXT NOT NULL,
        capacity_kg REAL NOT NULL,
        current_payload_kg REAL DEFAULT 0,
        waste_type TEXT NOT NULL, -- wet, dry, mixed
        target_facility_id TEXT,
        status TEXT DEFAULT 'available', -- available, assigned, in_transit, weighbridge, diverted, maintenance
        current_lat REAL,
        current_lon REAL,
        speed_kmh REAL DEFAULT 0,
        eta_mins INTEGER DEFAULT 15,
        assigned_zone TEXT,
        last_ping TEXT
    )
    """)

    # 5. Allocations History & Runs Table
    c.execute("""
    CREATE TABLE IF NOT EXISTS allocations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT NOT NULL,
        objective TEXT NOT NULL, -- min_overflow, min_cost, min_carbon, balanced
        total_waste_kg REAL NOT NULL,
        total_capacity_kg REAL NOT NULL,
        total_overflow_kg REAL NOT NULL,
        plan_json TEXT NOT NULL,
        status TEXT DEFAULT 'approved', -- proposed, approved, rejected
        approved_by TEXT,
        cost_inr REAL DEFAULT 0,
        carbon_avoided_kg REAL DEFAULT 0
    )
    """)

    # 6. Alerts & Notifications Table
    c.execute("""
    CREATE TABLE IF NOT EXISTS alerts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        facility_id TEXT,
        severity TEXT NOT NULL, -- normal, moderate, warning, critical
        utilization_pct REAL NOT NULL,
        message TEXT NOT NULL,
        recommended_action TEXT NOT NULL,
        timestamp TEXT NOT NULL,
        status TEXT DEFAULT 'pending', -- pending, acknowledged, resolved
        resolved_by TEXT,
        resolved_at TEXT
    )
    """)

    # 7. Citizen Reports Table
    c.execute("""
    CREATE TABLE IF NOT EXISTS citizen_reports (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tracking_id TEXT UNIQUE NOT NULL,
        category TEXT NOT NULL, -- overflowing_bin, illegal_dumping, missed_collection, segregation_issue
        description TEXT NOT NULL,
        location_name TEXT NOT NULL,
        ward TEXT NOT NULL,
        latitude REAL,
        longitude REAL,
        photo_name TEXT,
        citizen_name TEXT,
        citizen_phone TEXT,
        status TEXT DEFAULT 'submitted', -- submitted, in_progress, resolved, rejected
        reported_at TEXT NOT NULL,
        assigned_to TEXT,
        resolution_notes TEXT,
        resolved_at TEXT
    )
    """)

    # 8. Saved Scenarios Table
    c.execute("""
    CREATE TABLE IF NOT EXISTS scenarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        description TEXT,
        parameters_json TEXT NOT NULL,
        results_json TEXT NOT NULL,
        created_at TEXT NOT NULL,
        created_by TEXT NOT NULL
    )
    """)

    # 9. Audit Logs Table
    c.execute("""
    CREATE TABLE IF NOT EXISTS audit_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT NOT NULL,
        username TEXT NOT NULL,
        action TEXT NOT NULL,
        details TEXT
    )
    """)

    # 10. Facility Machines Table (Dynamic Processing Units & Machinery)
    c.execute("""
    CREATE TABLE IF NOT EXISTS facility_machines (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        facility_id TEXT NOT NULL,
        machine_name TEXT NOT NULL,
        machine_type TEXT NOT NULL, -- shredder, digester, trommel, baler, optical_sorter, boiler
        model_number TEXT,
        capacity_kg_day REAL NOT NULL,
        power_kw REAL DEFAULT 45.0,
        status TEXT DEFAULT 'operational', -- operational, maintenance, standby
        installed_date TEXT,
        last_serviced TEXT,
        FOREIGN KEY(facility_id) REFERENCES facilities(id)
    )
    """)

    conn.commit()

    # Seed initial machines if table is empty
    c.execute("SELECT COUNT(*) FROM facility_machines")
    if c.fetchone()[0] == 0:
        seed_machines = [
            (
                "A",
                "Rotary Biomass Shredder Mk-II",
                "shredder",
                "SHR-402",
                2000.0,
                55.0,
                "operational",
                "2025-08-10",
                "2026-09-15",
            ),
            (
                "A",
                "High-Volume Trommel Screen 12mm",
                "trommel",
                "TRM-101",
                2000.0,
                30.0,
                "operational",
                "2025-09-01",
                "2026-10-01",
            ),
            (
                "B",
                "Continuous Anaerobic Digester Reactor #1",
                "digester",
                "CSTR-800",
                3500.0,
                75.0,
                "operational",
                "2025-05-20",
                "2026-08-20",
            ),
            (
                "B",
                "Continuous Anaerobic Digester Reactor #2",
                "digester",
                "CSTR-801",
                3500.0,
                75.0,
                "operational",
                "2025-06-15",
                "2026-09-10",
            ),
            (
                "C",
                "NIR Automated Optical Polymer Sorter",
                "optical_sorter",
                "OPT-920",
                1200.0,
                40.0,
                "operational",
                "2025-11-05",
                "2026-09-28",
            ),
            (
                "C",
                "Continuous Hydraulic Two-Ram Baler",
                "baler",
                "BLR-550",
                1300.0,
                35.0,
                "operational",
                "2025-10-12",
                "2026-10-02",
            ),
        ]
        for fid, mname, mtype, mod, cap, pwr, stat, idate, lserv in seed_machines:
            c.execute(
                """
                INSERT INTO facility_machines (facility_id, machine_name, machine_type, model_number, capacity_kg_day, power_kw, status, installed_date, last_serviced)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (fid, mname, mtype, mod, cap, pwr, stat, idate, lserv),
            )
        conn.commit()

    # Seed initial data if users table is empty or missing authority roles
    c.execute("SELECT COUNT(*) FROM users")
    if c.fetchone()[0] == 0:
        _seed_initial_data(conn)
    else:
        _ensure_authority_users(conn)

    conn.close()


def _ensure_authority_users(conn):
    """Ensure all 6 official authority accounts exist in the database."""
    c = conn.cursor()
    now_str = datetime.now(timezone.utc).isoformat()
    official_accounts = [
        (
            "state_authority",
            "Waste@123",
            "state_authority",
            "State Waste Management Authority",
            "Statewide Urban Municipal Solid-Waste Command",
            "E. Ramesh Rao, IAS",
            "state.authority@wastegrid.gov.in",
        ),
        (
            "commissioner",
            "Waste@123",
            "commissioner",
            "Municipal Commissioner",
            "Bruhat Bengaluru Mahanagara Palike (BBMP)",
            "Tushar Giri Nath, IAS",
            "commissioner@bbmp.gov.in",
        ),
        (
            "waste_officer",
            "Waste@123",
            "waste_officer",
            "Municipal Waste Officer",
            "Central Solid-Waste Operations Command",
            "K. Parameshwar, KAS",
            "waste.officer@bbmp.gov.in",
        ),
        (
            "zonal_officer",
            "Waste@123",
            "zonal_officer",
            "Zonal Officer",
            "East & South Urban Collection Zones",
            "Dr. Shailaja V.",
            "zonal.officer@smartcity.gov.in",
        ),
        (
            "processing_facility",
            "Waste@123",
            "processing_facility",
            "Waste Processing Facility",
            "Biocompost Plant A & Anaerobic Digester B",
            "S. Manjunath",
            "plant.head@wastegrid-consortium.org",
        ),
        (
            "recycling_facility",
            "Waste@123",
            "recycling_facility",
            "Recycling Facility",
            "Material Recovery Facility C (MRF)",
            "Anita Deshmukh",
            "recycling.director@wastegrid-consortium.org",
        ),
        (
            "admin",
            "Admin@123",
            "admin",
            "System Administrator",
            "Full System Administration & Governance",
            "WasteGrid Super Administrator",
            "admin@wastegrid.gov.in",
        ),
        (
            "state_admin",
            "Waste@123",
            "state",
            "State Waste Management Authority",
            "Statewide Urban Municipal Solid-Waste Command",
            "E. Ramesh Rao, IAS",
            "state.admin@smartcity.gov.in",
        ),
        (
            "district_admin",
            "District@123",
            "district",
            "Zonal Officer",
            "Bengaluru Urban District",
            "Dr. Rajendra Kumar IAS",
            "district.admin@smartcity.gov.in",
        ),
        (
            "municipality_admin",
            "Municipality@123",
            "municipality",
            "Municipal Commissioner",
            "BBMP Central Municipal Wards",
            "Tushar Giri Nath",
            "commissioner@bbmp.gov.in",
        ),
        (
            "driver_ramesh",
            "Driver@123",
            "truck_driver",
            "Compactor Truck Driver (In-Cab Logistics)",
            "Central Collection Route · Vehicle KA-01-EA-101",
            "Ramesh Kumar",
            "driver.ramesh@wastegrid.gov.in",
        ),
        (
            "ramya_zonal",
            "Waste@123",
            "zonal_officer",
            "Zonal Officer",
            "East & South Urban Collection Zones",
            "Ramya V",
            "ramya@wastegrid.in.com",
        ),
        (
            "kiran.raj123",
            "Waste@123",
            "commissioner",
            "Municipal Commissioner",
            "Bruhat Bengaluru Mahanagara Palike (BBMP)",
            "R V Kiran Kumar",
            "kiranraj@wastegrid.com",
        ),
    ]

    for uname, pw, role, auth_title, juris, fname, email in official_accounts:
        c.execute("SELECT id FROM users WHERE username = ?", (uname,))
        row = c.fetchone()
        if not row:
            h, s = hash_password(pw)
            c.execute(
                """
                INSERT OR IGNORE INTO users (username, password_hash, salt, role, authority_title, jurisdiction, full_name, email, is_active, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1, ?)
            """,
                (uname, h, s, role, auth_title, juris, fname, email, now_str),
            )
        else:
            c.execute(
                """
                UPDATE users SET authority_title = ?, jurisdiction = ? WHERE username = ?
            """,
                (auth_title, juris, uname),
            )
    conn.commit()


def _seed_initial_data(conn):
    """Seed initial credentials, facilities, sources, and vehicles."""
    c = conn.cursor()
    now_str = datetime.now(timezone.utc).isoformat()

    # 1. Seed Users (All 6 Official Authority Roles + Admin + Legacy)
    seed_users = [
        (
            "state_authority",
            "Waste@123",
            "state_authority",
            "State Waste Management Authority",
            "Statewide Urban Municipal Solid-Waste Command",
            "E. Ramesh Rao, IAS",
            "state.authority@wastegrid.gov.in",
        ),
        (
            "commissioner",
            "Waste@123",
            "commissioner",
            "Municipal Commissioner",
            "Bruhat Bengaluru Mahanagara Palike (BBMP)",
            "Tushar Giri Nath, IAS",
            "commissioner@bbmp.gov.in",
        ),
        (
            "waste_officer",
            "Waste@123",
            "waste_officer",
            "Municipal Waste Officer",
            "Central Solid-Waste Operations Command",
            "K. Parameshwar, KAS",
            "waste.officer@bbmp.gov.in",
        ),
        (
            "zonal_officer",
            "Waste@123",
            "zonal_officer",
            "Zonal Officer",
            "East & South Urban Collection Zones",
            "Dr. Shailaja V.",
            "zonal.officer@smartcity.gov.in",
        ),
        (
            "processing_facility",
            "Waste@123",
            "processing_facility",
            "Waste Processing Facility",
            "Biocompost Plant A & Anaerobic Digester B",
            "S. Manjunath",
            "plant.head@wastegrid-consortium.org",
        ),
        (
            "recycling_facility",
            "Waste@123",
            "recycling_facility",
            "Recycling Facility",
            "Material Recovery Facility C (MRF)",
            "Anita Deshmukh",
            "recycling.director@wastegrid-consortium.org",
        ),
        (
            "admin",
            "Admin@123",
            "admin",
            "System Administrator",
            "Full System Access & User Governance",
            "WasteGrid Root Administrator",
            "admin@wastegrid.gov.in",
        ),
        (
            "state_admin",
            "Waste@123",
            "state",
            "State Waste Management Authority",
            "Statewide Urban Municipal Solid-Waste Command",
            "E. Ramesh Rao, IAS",
            "state.admin@smartcity.gov.in",
        ),
        (
            "district_admin",
            "District@123",
            "district",
            "Zonal Officer",
            "Bengaluru Urban District",
            "Dr. Rajendra Kumar IAS",
            "district.admin@smartcity.gov.in",
        ),
        (
            "municipality_admin",
            "Municipality@123",
            "municipality",
            "Municipal Commissioner",
            "BBMP Central Municipal Wards",
            "Tushar Giri Nath",
            "commissioner@bbmp.gov.in",
        ),
        (
            "factory_admin",
            "Factory@123",
            "factory",
            "Waste Processing Facility",
            "Processing Plants A, B, C & D",
            "S. Manjunath",
            "plant.head@wastegrid-consortium.org",
        ),
        (
            "driver_ramesh",
            "Driver@123",
            "truck_driver",
            "Compactor Truck Driver (In-Cab Logistics)",
            "Central Collection Route · Vehicle KA-01-EA-101",
            "Ramesh Kumar",
            "driver.ramesh@wastegrid.gov.in",
        ),
    ]

    for uname, pw, role, auth_title, juris, fname, email in seed_users:
        h, s = hash_password(pw)
        c.execute(
            """
            INSERT OR IGNORE INTO users (username, password_hash, salt, role, authority_title, jurisdiction, full_name, email, is_active, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1, ?)
        """,
            (uname, h, s, role, auth_title, juris, fname, email, now_str),
        )

    # 2. Seed Facilities (Dynamic facilities: A, B, C, D, E)
    # Real Bengaluru / peri-urban coordinates for accurate GIS rendering
    seed_facilities = [
        (
            "A",
            "Organic Biocompost Plant A",
            "biocompost",
            "wet",
            3000.0,
            0.0,
            5.2,
            12.9279,
            77.6271,
            "online",
            "06:00 - 22:00",
            96.5,
            320.0,
            0.04,
        ),
        (
            "B",
            "Anaerobic Digester & Biogas B",
            "anaerobic_digester",
            "wet",
            1500.0,
            0.0,
            8.4,
            12.9716,
            77.5946,
            "online",
            "24/7 Continuous",
            94.0,
            280.0,
            0.02,
        ),
        (
            "C",
            "Material Recovery Facility C (MRF)",
            "mrf",
            "dry",
            2500.0,
            0.0,
            6.1,
            13.0033,
            77.5891,
            "online",
            "07:00 - 20:00",
            98.0,
            240.0,
            0.03,
        ),
        (
            "D",
            "Regional Waste-to-Energy Plant D",
            "waste_to_energy",
            "mixed",
            3500.0,
            0.0,
            14.2,
            12.8399,
            77.6770,
            "online",
            "24/7 Continuous",
            91.0,
            420.0,
            0.06,
        ),
        (
            "E",
            "South Organic Eco-Yard E",
            "biocompost",
            "wet",
            2000.0,
            0.0,
            11.0,
            12.8800,
            77.5500,
            "online",
            "06:00 - 18:00",
            95.0,
            300.0,
            0.035,
        ),
    ]

    for (
        fid,
        name,
        ftype,
        accepts,
        cap,
        load,
        dist,
        lat,
        lon,
        stat,
        hours,
        eff,
        cost,
        carb,
    ) in seed_facilities:
        c.execute(
            """
            INSERT INTO facilities (id, name, type, accepts, capacity_kg, current_load_kg, distance_km, latitude, longitude, status, operating_hours, efficiency_pct, cost_per_ton, carbon_factor_kg)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                fid,
                name,
                ftype,
                accepts,
                cap,
                load,
                dist,
                lat,
                lon,
                stat,
                hours,
                eff,
                cost,
                carb,
            ),
        )

    # 3. Seed Waste Sources (Realistic Wards with Coordinates)
    seed_sources = [
        (
            "household",
            "Downtown Residential Hub",
            "WARD-112",
            "Central",
            1400.0,
            "wet",
            12.9750,
            77.6050,
        ),
        (
            "villas",
            "Suburban Green Villas",
            "WARD-145",
            "South",
            600.0,
            "wet",
            12.9180,
            77.5930,
        ),
        (
            "restaurant",
            "Culinary District & Food Market",
            "WARD-088",
            "Central",
            1800.0,
            "wet",
            12.9680,
            77.6010,
        ),
        (
            "office",
            "Silicon Tech Park Offices",
            "WARD-174",
            "East",
            500.0,
            "dry",
            12.9850,
            77.7280,
        ),
        (
            "mall",
            "Metropolitan Shopping Mall",
            "WARD-062",
            "North",
            400.0,
            "dry",
            13.0120,
            77.5550,
        ),
        (
            "college",
            "University Campus & Hostels",
            "WARD-099",
            "West",
            500.0,
            "dry",
            12.9340,
            77.5320,
        ),
        (
            "hospital",
            "Metro Super Specialty Hospital",
            "WARD-104",
            "Central",
            650.0,
            "wet",
            12.9610,
            77.5850,
        ),
        (
            "event",
            "Civic Event / Cultural Grounds",
            "WARD-077",
            "Central",
            0.0,
            "wet",
            12.9980,
            77.5920,
        ),
    ]

    for sid, sname, wcode, zone, base_kg, wtype, lat, lon in seed_sources:
        c.execute(
            """
            INSERT INTO waste_sources (id, name, ward_code, zone, baseline_kg, waste_type, latitude, longitude, active_spike_kg, modifier)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0, 1.0)
        """,
            (sid, sname, wcode, zone, base_kg, wtype, lat, lon),
        )

    # 4. Seed Vehicles (8 Active Compactor Trucks)
    seed_vehicles = [
        (
            "KA-01-EA-101",
            "Ramesh Kumar",
            "+91 98450 11001",
            3000.0,
            2400.0,
            "wet",
            "A",
            "in_transit",
            12.9450,
            77.6120,
            32.0,
            8,
            "Central",
        ),
        (
            "KA-01-EA-102",
            "Shivakumar N.",
            "+91 98450 11002",
            2500.0,
            1800.0,
            "wet",
            "B",
            "in_transit",
            12.9320,
            77.5810,
            28.0,
            14,
            "South",
        ),
        (
            "KA-04-MB-204",
            "Mohammed Rafiq",
            "+91 98450 11003",
            3500.0,
            2200.0,
            "wet",
            "A",
            "weighbridge",
            12.9280,
            77.6270,
            0.0,
            0,
            "Central",
        ),
        (
            "KA-04-MB-312",
            "Anand Vardhan",
            "+91 98450 11004",
            2000.0,
            950.0,
            "dry",
            "C",
            "in_transit",
            12.9920,
            77.6540,
            38.0,
            11,
            "East",
        ),
        (
            "KA-05-AB-405",
            "Venkatesh Murthy",
            "+91 98450 11005",
            2500.0,
            1200.0,
            "dry",
            "C",
            "in_transit",
            13.0080,
            77.5720,
            22.0,
            19,
            "North",
        ),
        (
            "KA-05-AB-512",
            "Syed Imran",
            "+91 98450 11006",
            2000.0,
            750.0,
            "dry",
            "C",
            "available",
            12.9410,
            77.5450,
            0.0,
            0,
            "West",
        ),
        (
            "KA-01-EA-601",
            "Basavaraj Patil",
            "+91 98450 11007",
            2000.0,
            550.0,
            "dry",
            "C",
            "assigned",
            12.9710,
            77.5920,
            0.0,
            25,
            "Central",
        ),
        (
            "KA-02-EM-999",
            "Guru Prasad (Surge Taskforce)",
            "+91 98450 11008",
            5000.0,
            0.0,
            "wet",
            "A",
            "available",
            12.9550,
            77.6010,
            0.0,
            0,
            "Standby",
        ),
    ]

    for (
        vid,
        dname,
        ph,
        cap,
        payl,
        wtype,
        tfid,
        stat,
        lat,
        lon,
        spd,
        eta,
        z,
    ) in seed_vehicles:
        c.execute(
            """
            INSERT INTO vehicles (id, driver_name, phone, capacity_kg, current_payload_kg, waste_type, target_facility_id, status, current_lat, current_lon, speed_kmh, eta_mins, assigned_zone, last_ping)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                vid,
                dname,
                ph,
                cap,
                payl,
                wtype,
                tfid,
                stat,
                lat,
                lon,
                spd,
                eta,
                z,
                now_str,
            ),
        )

    # 5. Seed Sample Citizen Reports
    seed_reports = [
        (
            "WG-REP-2026-9041",
            "overflowing_bin",
            "Commercial bins near 8th Cross overflowing onto roadway; stench spreading.",
            "Indiranagar 100ft Road",
            "WARD-112",
            12.9720,
            77.6410,
            "bin_overflow_1.jpg",
            "Pooja Hegde",
            "+91 98451 22334",
            "in_progress",
            now_str,
            "Ramesh Kumar (KA-01-EA-101)",
            "Truck dispatched on priority",
        ),
        (
            "WG-REP-2026-9042",
            "illegal_dumping",
            "Night dumping of demolition debris and mixed wet packaging behind tech park.",
            "Bellandur Outer Ring Road",
            "WARD-174",
            12.9290,
            77.6810,
            "debris_dump.jpg",
            "Arun Kulkarni",
            "+91 98452 33445",
            "submitted",
            now_str,
            None,
            None,
        ),
        (
            "WG-REP-2026-9043",
            "missed_collection",
            "Door-to-door green compactor truck did not arrive for 2 consecutive days.",
            "Jayanagar 4th Block",
            "WARD-145",
            12.9290,
            77.5820,
            None,
            "Sunita Rao",
            "+91 98453 44556",
            "resolved",
            now_str,
            "Shivakumar N.",
            "Cleared during morning shift",
        ),
    ]

    for (
        trk_id,
        cat,
        desc,
        loc,
        ward,
        lat,
        lon,
        photo,
        cname,
        cphone,
        stat,
        rep_at,
        assto,
        notes,
    ) in seed_reports:
        c.execute(
            """
            INSERT INTO citizen_reports (tracking_id, category, description, location_name, ward, latitude, longitude, photo_name, citizen_name, citizen_phone, status, reported_at, assigned_to, resolution_notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                trk_id,
                cat,
                desc,
                loc,
                ward,
                lat,
                lon,
                photo,
                cname,
                cphone,
                stat,
                rep_at,
                assto,
                notes,
            ),
        )

    # 6. Seed Sample Alerts
    seed_alerts = [
        (
            "A",
            "normal",
            64.0,
            "Facility A operating at standard capacity threshold.",
            "Routine intake maintained.",
            now_str,
            "resolved",
            "system",
        ),
        (
            "B",
            "moderate",
            78.5,
            "Facility B receiving higher organic slurry flow.",
            "Monitor digester pressure hourly.",
            now_str,
            "acknowledged",
            "factory_admin",
        ),
    ]
    for fid, sev, util, msg, act, ts, stat, res_by in seed_alerts:
        c.execute(
            """
            INSERT INTO alerts (facility_id, severity, utilization_pct, message, recommended_action, timestamp, status, resolved_by)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (fid, sev, util, msg, act, ts, stat, res_by),
        )

    conn.commit()


# =========================================================================
# CRUD OPERATIONS & QUERY INTERFACES
# =========================================================================


def get_user_by_username(username):
    """Fetch user record by username."""
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username = ?", (username.strip().lower(),))
    row = c.fetchone()
    conn.close()
    return dict(row) if row else None


def update_user_password(username, new_password):
    """Update user password with new salt and hash."""
    h, s = hash_password(new_password)
    conn = get_connection()
    c = conn.cursor()
    c.execute(
        "UPDATE users SET password_hash = ?, salt = ? WHERE username = ?",
        (h, s, username.strip().lower()),
    )
    conn.commit()
    conn.close()
    return True


def create_user(
    username, password, role, authority_title, jurisdiction, full_name, email
):
    """Admin creates a new user."""
    h, s = hash_password(password)
    now_str = datetime.now(timezone.utc).isoformat()
    conn = get_connection()
    c = conn.cursor()
    try:
        c.execute(
            """
            INSERT INTO users (username, password_hash, salt, role, authority_title, jurisdiction, full_name, email, is_active, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1, ?)
        """,
            (
                username.strip().lower(),
                h,
                s,
                role,
                authority_title,
                jurisdiction,
                full_name,
                email,
                now_str,
            ),
        )
        conn.commit()
        return True, "User created successfully."
    except sqlite3.IntegrityError:
        return False, f"Username '{username}' already exists."
    finally:
        conn.close()


def get_all_users():
    """Get list of all users for admin management."""
    conn = get_connection()
    c = conn.cursor()
    c.execute(
        "SELECT id, username, role, authority_title, jurisdiction, full_name, email, is_active, created_at, last_login FROM users ORDER BY id ASC"
    )
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def toggle_user_active(user_id, is_active):
    """Activate or deactivate a user."""
    conn = get_connection()
    c = conn.cursor()
    c.execute(
        "UPDATE users SET is_active = ? WHERE id = ?", (1 if is_active else 0, user_id)
    )
    conn.commit()
    conn.close()


def get_all_facilities(include_offline=True):
    """Retrieve all facilities from database."""
    conn = get_connection()
    c = conn.cursor()
    if include_offline:
        c.execute("SELECT * FROM facilities ORDER BY id ASC")
    else:
        c.execute("SELECT * FROM facilities WHERE status != 'offline' ORDER BY id ASC")
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def add_facility(
    fid,
    name,
    ftype,
    accepts,
    capacity_kg,
    distance_km,
    lat,
    lon,
    hours,
    eff,
    cost,
    carb,
):
    """Add a new processing facility to the database."""
    conn = get_connection()
    c = conn.cursor()
    try:
        c.execute(
            """
            INSERT INTO facilities (id, name, type, accepts, capacity_kg, current_load_kg, distance_km, latitude, longitude, status, operating_hours, efficiency_pct, cost_per_ton, carbon_factor_kg)
            VALUES (?, ?, ?, ?, ?, 0, ?, ?, ?, 'online', ?, ?, ?, ?)
        """,
            (
                fid.upper(),
                name,
                ftype,
                accepts,
                capacity_kg,
                distance_km,
                lat,
                lon,
                hours,
                eff,
                cost,
                carb,
            ),
        )
        conn.commit()
        return True, f"Facility {fid} added successfully."
    except sqlite3.IntegrityError:
        return False, f"Facility ID '{fid}' already exists."
    finally:
        conn.close()


def create_facility(
    fid,
    name,
    ftype="biocompost",
    accepts="wet",
    capacity_kg=2000.0,
    distance_km=5.0,
    latitude=12.9,
    longitude=77.6,
    operating_hours="06:00 - 22:00",
    efficiency_pct=95.0,
    cost_per_ton=300.0,
    co2_per_ton_km=0.04,
):
    """Convenience alias for adding a facility."""
    success, _ = add_facility(
        fid,
        name,
        ftype,
        accepts,
        capacity_kg,
        distance_km,
        latitude,
        longitude,
        operating_hours,
        efficiency_pct,
        cost_per_ton,
        co2_per_ton_km,
    )
    return success


def get_facility_by_id(fid):
    """Retrieve a single facility by ID or None."""
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM facilities WHERE id = ?", (fid.upper(),))
    row = c.fetchone()
    conn.close()
    return dict(row) if row else None


def set_facility_status(fid, status):
    """Update operating status of a facility."""
    conn = get_connection()
    c = conn.cursor()
    c.execute(
        "UPDATE facilities SET status = ? WHERE id = ?", (status.lower(), fid.upper())
    )
    conn.commit()
    conn.close()
    return True


def update_facility(
    fid, name, ftype, accepts, capacity_kg, status, distance_km, cost, eff
):
    """Update facility attributes."""
    conn = get_connection()
    c = conn.cursor()
    c.execute(
        """
        UPDATE facilities
        SET name = ?, type = ?, accepts = ?, capacity_kg = ?, status = ?, distance_km = ?, cost_per_ton = ?, efficiency_pct = ?
        WHERE id = ?
    """,
        (name, ftype, accepts, capacity_kg, status, distance_km, cost, eff, fid),
    )
    conn.commit()
    conn.close()
    return True


def delete_facility(fid):
    """Delete a facility."""
    conn = get_connection()
    c = conn.cursor()
    c.execute("DELETE FROM facilities WHERE id = ?", (fid.upper(),))
    conn.commit()
    conn.close()
    return True


def update_facility_load(fid, load_kg):
    """Update current allocated load on a facility."""
    conn = get_connection()
    c = conn.cursor()
    c.execute("UPDATE facilities SET current_load_kg = ? WHERE id = ?", (load_kg, fid))
    conn.commit()
    conn.close()


def get_all_waste_sources():
    """Get all waste sources / wards."""
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM waste_sources ORDER BY id ASC")
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_all_vehicles():
    """Retrieve all vehicles."""
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM vehicles ORDER BY id ASC")
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def add_vehicle(
    vid,
    driver_name,
    phone,
    capacity_kg,
    waste_type="wet",
    target_facility_id="A",
    status="available",
    assigned_zone="Central",
):
    """Commission a new compactor truck to the municipal fleet."""
    now_str = datetime.now(timezone.utc).isoformat()
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT id FROM vehicles WHERE id = ?", (vid.strip().upper(),))
    if c.fetchone():
        conn.close()
        return False, f"Vehicle registration plate '{vid}' is already in fleet."
    c.execute(
        """
        INSERT INTO vehicles (id, driver_name, phone, capacity_kg, current_payload_kg, waste_type, target_facility_id, status, current_lat, current_lon, speed_kmh, eta_mins, assigned_zone, last_ping)
        VALUES (?, ?, ?, ?, 0.0, ?, ?, ?, 12.9550, 77.6010, 0.0, 0, ?, ?)
    """,
        (
            vid.strip().upper(),
            driver_name.strip(),
            phone.strip(),
            float(capacity_kg),
            waste_type,
            target_facility_id,
            status,
            assigned_zone,
            now_str,
        ),
    )
    conn.commit()
    conn.close()
    add_audit_log(
        "fleet_ops",
        "VEHICLE_COMMISSIONED",
        f"Added compactor {vid} ({driver_name}, {capacity_kg:,.0f} kg)",
    )
    return True, f"Vehicle '{vid}' successfully commissioned to municipal fleet!"


def update_vehicle_dispatch(vid, target_facility_id, status):
    """Update vehicle route target and status."""
    conn = get_connection()
    c = conn.cursor()
    c.execute(
        "UPDATE vehicles SET target_facility_id = ?, status = ? WHERE id = ?",
        (target_facility_id, status, vid),
    )
    conn.commit()
    conn.close()


def assign_on_demand_job(vid, ward_name, waste_type, payload_kg, target_facility_id):
    """Assign an on-demand pickup job to an available free truck driver."""
    now_str = datetime.now(timezone.utc).isoformat()
    conn = get_connection()
    c = conn.cursor()
    c.execute(
        """
        UPDATE vehicles
        SET status = 'in_transit',
            current_payload_kg = ?,
            waste_type = ?,
            target_facility_id = ?,
            eta_mins = 14,
            speed_kmh = 32.0,
            last_ping = ?
        WHERE id = ?
    """,
        (float(payload_kg), waste_type, target_facility_id, now_str, vid),
    )
    conn.commit()
    conn.close()
    add_audit_log(
        vid,
        "ON_DEMAND_JOB_ACCEPTED",
        f"Accepted {payload_kg:,.0f} kg pickup from {ward_name} to Plant {target_facility_id}",
    )
    return (
        True,
        f"Job accepted! Dispatched to {ward_name} ➔ Plant {target_facility_id} ({payload_kg:,.0f} kg).",
    )


# =========================================================================
# FACILITY MACHINE & HARDWARE UNIT MANAGEMENT
# =========================================================================


def get_facility_machines(facility_id=None):
    """Retrieve machines for a specific facility or all facilities across the grid."""
    conn = get_connection()
    c = conn.cursor()
    if facility_id:
        c.execute(
            """
            SELECT m.*, f.name as facility_name
            FROM facility_machines m
            JOIN facilities f ON m.facility_id = f.id
            WHERE m.facility_id = ?
            ORDER BY m.id ASC
        """,
            (facility_id,),
        )
    else:
        c.execute("""
            SELECT m.*, f.name as facility_name
            FROM facility_machines m
            JOIN facilities f ON m.facility_id = f.id
            ORDER BY m.facility_id ASC, m.id ASC
        """)
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def add_facility_machine(
    facility_id,
    machine_name,
    machine_type,
    model_number,
    capacity_kg_day,
    power_kw=45.0,
    status="operational",
):
    """
    Install a new machine/processing unit to a factory.
    Directly increments the parent facility's daily intake capacity in the database
    so the LP optimization solver automatically accounts for the higher throughput ceiling.
    """
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    conn = get_connection()
    c = conn.cursor()
    c.execute(
        """
        INSERT INTO facility_machines (facility_id, machine_name, machine_type, model_number, capacity_kg_day, power_kw, status, installed_date, last_serviced)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """,
        (
            facility_id,
            machine_name,
            machine_type,
            model_number,
            float(capacity_kg_day),
            float(power_kw),
            status,
            now_str,
            now_str,
        ),
    )

    # Dynamically increment facility intake capacity in SQLite
    c.execute(
        """
        UPDATE facilities
        SET capacity_kg = capacity_kg + ?
        WHERE id = ?
    """,
        (float(capacity_kg_day), facility_id),
    )
    conn.commit()
    conn.close()
    add_audit_log(
        "plant_manager",
        "MACHINE_ADDED",
        f"Installed machine '{machine_name}' (+{capacity_kg_day:,.0f} kg/day) at Plant {facility_id}",
    )
    return (
        True,
        f"Machine '{machine_name}' installed! Plant {facility_id} intake capacity expanded by +{capacity_kg_day:,.0f} kg/day.",
    )


def delete_facility_machine(machine_id):
    """Decommission a machine unit and adjust facility daily capacity accordingly."""
    conn = get_connection()
    c = conn.cursor()
    c.execute(
        "SELECT facility_id, machine_name, capacity_kg_day FROM facility_machines WHERE id = ?",
        (machine_id,),
    )
    m = c.fetchone()
    if not m:
        conn.close()
        return False, "Machine not found."
    fid = m["facility_id"]
    mname = m["machine_name"]
    cap = float(m["capacity_kg_day"])
    c.execute("DELETE FROM facility_machines WHERE id = ?", (machine_id,))
    c.execute(
        "UPDATE facilities SET capacity_kg = MAX(500.0, capacity_kg - ?) WHERE id = ?",
        (cap, fid),
    )
    conn.commit()
    conn.close()
    add_audit_log(
        "plant_manager",
        "MACHINE_DECOMMISSIONED",
        f"Decommissioned '{mname}' (-{cap:,.0f} kg/day) from Plant {fid}",
    )
    return (
        True,
        f"Machine '{mname}' decommissioned. Plant {fid} intake capacity updated.",
    )


def get_active_alerts(status_filter=None):
    """Retrieve alerts with optional status filter."""
    conn = get_connection()
    c = conn.cursor()
    if status_filter:
        c.execute(
            "SELECT * FROM alerts WHERE status = ? ORDER BY id DESC", (status_filter,)
        )
    else:
        c.execute("SELECT * FROM alerts ORDER BY id DESC")
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def create_alert(
    facility_id,
    severity,
    util_pct=None,
    message="",
    rec_action="",
    utilization_pct=None,
    recommended_action=None,
):
    """Create a new predictive or operational alert."""
    pct = (
        util_pct
        if util_pct is not None
        else (utilization_pct if utilization_pct is not None else 0.0)
    )
    action = rec_action or recommended_action or "Monitor system capacity."
    now_str = datetime.now(timezone.utc).isoformat()
    conn = get_connection()
    c = conn.cursor()
    c.execute(
        """
        INSERT INTO alerts (facility_id, severity, utilization_pct, message, recommended_action, timestamp, status)
        VALUES (?, ?, ?, ?, ?, ?, 'pending')
    """,
        (facility_id, severity, pct, message, action, now_str),
    )
    alert_id = c.lastrowid
    conn.commit()
    conn.close()
    return alert_id


def update_alert_status(alert_id, new_status, resolved_by=None):
    """Acknowledge or resolve an alert."""
    now_str = (
        datetime.now(timezone.utc).isoformat() if new_status == "resolved" else None
    )
    conn = get_connection()
    c = conn.cursor()
    c.execute(
        """
        UPDATE alerts
        SET status = ?, resolved_by = ?, resolved_at = ?
        WHERE id = ?
    """,
        (new_status, resolved_by, now_str, alert_id),
    )
    conn.commit()
    conn.close()


def acknowledge_alert(alert_id):
    """Mark an alert as acknowledged."""
    update_alert_status(alert_id, "acknowledged")


def resolve_alert(alert_id, resolved_by="admin"):
    """Mark an alert as resolved."""
    update_alert_status(alert_id, "resolved", resolved_by=resolved_by)


def get_all_citizen_reports(status_filter=None):
    """Retrieve citizen reports."""
    conn = get_connection()
    c = conn.cursor()
    if status_filter and status_filter != "all":
        c.execute(
            "SELECT * FROM citizen_reports WHERE status = ? ORDER BY id DESC",
            (status_filter,),
        )
    else:
        c.execute("SELECT * FROM citizen_reports ORDER BY id DESC")
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_citizen_report_by_ticket(tracking_id):
    """Retrieve a single citizen report by its unique tracking ID."""
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM citizen_reports WHERE tracking_id = ?", (tracking_id,))
    row = c.fetchone()
    conn.close()
    return dict(row) if row else None


def add_citizen_report(
    category,
    description,
    location_name,
    ward,
    lat=12.97,
    lon=77.59,
    photo_name=None,
    citizen_name="",
    citizen_phone="",
):
    """Submit a new citizen report."""
    now_str = datetime.now(timezone.utc).isoformat()
    tracking_id = (
        f"WG-REP-{datetime.now().strftime('%Y')}-{os.urandom(2).hex().upper()}"
    )
    conn = get_connection()
    c = conn.cursor()
    c.execute(
        """
        INSERT INTO citizen_reports (tracking_id, category, description, location_name, ward, latitude, longitude, photo_name, citizen_name, citizen_phone, status, reported_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending', ?)
    """,
        (
            tracking_id,
            category,
            description,
            location_name,
            ward,
            lat,
            lon,
            photo_name,
            citizen_name,
            citizen_phone,
            now_str,
        ),
    )
    conn.commit()
    conn.close()
    return tracking_id


def create_citizen_report(
    category,
    description,
    location_name="",
    ward="",
    lat=12.97,
    lon=77.59,
    photo_name=None,
    citizen_name="",
    citizen_phone="",
    location=None,
    contact_name=None,
    contact_phone=None,
):
    """Convenience alias for citizen report creation with flexible parameter aliases."""
    loc = location or location_name
    cname = contact_name or citizen_name
    cphone = contact_phone or citizen_phone
    return add_citizen_report(
        category, description, loc, ward, lat, lon, photo_name, cname, cphone
    )


def update_citizen_report_status(
    report_identifier,
    new_status,
    assigned_to=None,
    assigned_vehicle=None,
    resolution_notes=None,
):
    """Update status of a citizen complaint by integer ID or string tracking ID."""
    now_str = (
        datetime.now(timezone.utc).isoformat() if new_status == "resolved" else None
    )
    assignee = assigned_vehicle or assigned_to
    conn = get_connection()
    c = conn.cursor()
    if isinstance(report_identifier, str) and report_identifier.startswith("WG-REP-"):
        c.execute(
            """
            UPDATE citizen_reports
            SET status = ?, assigned_to = COALESCE(?, assigned_to), resolution_notes = ?, resolved_at = COALESCE(?, resolved_at)
            WHERE tracking_id = ?
        """,
            (new_status, assignee, resolution_notes, now_str, report_identifier),
        )
    else:
        c.execute(
            """
            UPDATE citizen_reports
            SET status = ?, assigned_to = COALESCE(?, assigned_to), resolution_notes = ?, resolved_at = COALESCE(?, resolved_at)
            WHERE id = ?
        """,
            (new_status, assignee, resolution_notes, now_str, report_identifier),
        )
    conn.commit()
    conn.close()


def save_allocation_run(
    objective,
    total_waste,
    total_capacity,
    total_overflow,
    plan_dict,
    approved_by,
    cost_inr,
    carbon_avoided,
):
    """Record an allocation optimization run."""
    now_str = datetime.now(timezone.utc).isoformat()
    plan_json = json.dumps(plan_dict)
    conn = get_connection()
    c = conn.cursor()
    c.execute(
        """
        INSERT INTO allocations (timestamp, objective, total_waste_kg, total_capacity_kg, total_overflow_kg, plan_json, status, approved_by, cost_inr, carbon_avoided_kg)
        VALUES (?, ?, ?, ?, ?, ?, 'approved', ?, ?, ?)
    """,
        (
            now_str,
            objective,
            total_waste,
            total_capacity,
            total_overflow,
            plan_json,
            approved_by,
            cost_inr,
            carbon_avoided,
        ),
    )
    conn.commit()
    conn.close()


def save_scenario(name, description, parameters, results, created_by):
    """Save a what-if simulation scenario."""
    now_str = datetime.now(timezone.utc).isoformat()
    conn = get_connection()
    c = conn.cursor()
    c.execute(
        """
        INSERT INTO scenarios (name, description, parameters_json, results_json, created_at, created_by)
        VALUES (?, ?, ?, ?, ?, ?)
    """,
        (
            name,
            description,
            json.dumps(parameters),
            json.dumps(results),
            now_str,
            created_by,
        ),
    )
    conn.commit()
    conn.close()


def get_all_scenarios():
    """Retrieve all saved simulation scenarios."""
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM scenarios ORDER BY id DESC")
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def add_audit_log(username, action, details=""):
    """Write an entry to the audit log."""
    now_str = datetime.now(timezone.utc).isoformat()
    conn = get_connection()
    c = conn.cursor()
    c.execute(
        """
        INSERT INTO audit_logs (timestamp, username, action, details)
        VALUES (?, ?, ?, ?)
    """,
        (now_str, username, action, details),
    )
    conn.commit()
    conn.close()


# Ensure DB tables and seed data exist at import time
init_db()
