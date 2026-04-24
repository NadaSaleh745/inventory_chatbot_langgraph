import sqlite3
from datetime import date
import os

DB_PATH = '../../inventory_chatbot.db'

SCHEMA_SQL = """
PRAGMA foreign_keys = ON;

-- Customers
CREATE TABLE Customers (
    CustomerId        INTEGER PRIMARY KEY AUTOINCREMENT,
    CustomerCode      TEXT UNIQUE NOT NULL,
    CustomerName      TEXT NOT NULL,
    Email             TEXT NULL,
    Phone             TEXT NULL,
    BillingAddress1   TEXT NULL,
    BillingCity       TEXT NULL,
    BillingCountry    TEXT NULL,
    CreatedAt         TEXT NOT NULL DEFAULT (datetime('now')),
    UpdatedAt         TEXT NULL,
    IsActive          INTEGER NOT NULL DEFAULT 1
);

-- Vendors
CREATE TABLE Vendors (
    VendorId      INTEGER PRIMARY KEY AUTOINCREMENT,
    VendorCode    TEXT UNIQUE NOT NULL,
    VendorName    TEXT NOT NULL,
    Email         TEXT NULL,
    Phone         TEXT NULL,
    AddressLine1  TEXT NULL,
    City          TEXT NULL,
    Country       TEXT NULL,
    CreatedAt     TEXT NOT NULL DEFAULT (datetime('now')),
    UpdatedAt     TEXT NULL,
    IsActive      INTEGER NOT NULL DEFAULT 1
);

-- Sites
CREATE TABLE Sites (
    SiteId      INTEGER PRIMARY KEY AUTOINCREMENT,
    SiteCode    TEXT UNIQUE NOT NULL,
    SiteName    TEXT NOT NULL,
    AddressLine1 TEXT NULL,
    City        TEXT NULL,
    Country     TEXT NULL,
    TimeZone    TEXT NULL,
    CreatedAt   TEXT NOT NULL DEFAULT (datetime('now')),
    UpdatedAt   TEXT NULL,
    IsActive    INTEGER NOT NULL DEFAULT 1
);

-- Locations (self-referencing)
CREATE TABLE Locations (
    LocationId       INTEGER PRIMARY KEY AUTOINCREMENT,
    SiteId           INTEGER NOT NULL,
    LocationCode     TEXT NOT NULL,
    LocationName     TEXT NOT NULL,
    ParentLocationId INTEGER NULL,
    CreatedAt        TEXT NOT NULL DEFAULT (datetime('now')),
    UpdatedAt        TEXT NULL,
    IsActive         INTEGER NOT NULL DEFAULT 1,
    CONSTRAINT UQ_Locations_SiteCode UNIQUE (SiteId, LocationCode),
    CONSTRAINT FK_Locations_Site FOREIGN KEY (SiteId) REFERENCES Sites(SiteId),
    CONSTRAINT FK_Locations_Parent FOREIGN KEY (ParentLocationId) REFERENCES Locations(LocationId)
);

-- Items
CREATE TABLE Items (
    ItemId         INTEGER PRIMARY KEY AUTOINCREMENT,
    ItemCode       TEXT UNIQUE NOT NULL,
    ItemName       TEXT NOT NULL,
    Category       TEXT NULL,
    UnitOfMeasure  TEXT NULL,
    CreatedAt      TEXT NOT NULL DEFAULT (datetime('now')),
    UpdatedAt      TEXT NULL,
    IsActive       INTEGER NOT NULL DEFAULT 1
);

-- Assets
CREATE TABLE Assets (
    AssetId       INTEGER PRIMARY KEY AUTOINCREMENT,
    AssetTag      TEXT UNIQUE NOT NULL,
    AssetName     TEXT NOT NULL,
    SiteId        INTEGER NOT NULL,
    LocationId    INTEGER NULL,
    SerialNumber  TEXT NULL,
    Category      TEXT NULL,
    Status        TEXT NOT NULL DEFAULT 'Active',
    Cost          NUMERIC NULL,
    PurchaseDate  TEXT NULL,
    VendorId      INTEGER NULL,
    CreatedAt     TEXT NOT NULL DEFAULT (datetime('now')),
    UpdatedAt     TEXT NULL,
    CONSTRAINT FK_Assets_Site FOREIGN KEY (SiteId) REFERENCES Sites(SiteId),
    CONSTRAINT FK_Assets_Location FOREIGN KEY (LocationId) REFERENCES Locations(LocationId),
    CONSTRAINT FK_Assets_Vendor FOREIGN KEY (VendorId) REFERENCES Vendors(VendorId)
);

-- Bills
CREATE TABLE Bills (
    BillId       INTEGER PRIMARY KEY AUTOINCREMENT,
    VendorId     INTEGER NOT NULL,
    BillNumber   TEXT NOT NULL,
    BillDate     TEXT NOT NULL,
    DueDate      TEXT NULL,
    TotalAmount  NUMERIC NOT NULL,
    Currency     TEXT NOT NULL DEFAULT 'USD',
    Status       TEXT NOT NULL DEFAULT 'Open',
    CreatedAt    TEXT NOT NULL DEFAULT (datetime('now')),
    UpdatedAt    TEXT NULL,
    CONSTRAINT UQ_Bills_Vendor_BillNumber UNIQUE (VendorId, BillNumber),
    CONSTRAINT FK_Bills_Vendor FOREIGN KEY (VendorId) REFERENCES Vendors(VendorId)
);

-- Purchase Orders
CREATE TABLE PurchaseOrders (
    POId        INTEGER PRIMARY KEY AUTOINCREMENT,
    PONumber    TEXT NOT NULL,
    VendorId    INTEGER NOT NULL,
    PODate      TEXT NOT NULL,
    Status      TEXT NOT NULL DEFAULT 'Open',
    SiteId      INTEGER NULL,
    CreatedAt   TEXT NOT NULL DEFAULT (datetime('now')),
    UpdatedAt   TEXT NULL,
    CONSTRAINT UQ_PurchaseOrders_Number UNIQUE (PONumber),
    CONSTRAINT FK_PurchaseOrders_Vendor FOREIGN KEY (VendorId) REFERENCES Vendors(VendorId),
    CONSTRAINT FK_PurchaseOrders_Site FOREIGN KEY (SiteId) REFERENCES Sites(SiteId)
);

-- Purchase Order Lines
CREATE TABLE PurchaseOrderLines (
    POLineId    INTEGER PRIMARY KEY AUTOINCREMENT,
    POId        INTEGER NOT NULL,
    LineNumber  INTEGER NOT NULL,
    ItemId      INTEGER NULL,
    ItemCode    TEXT NOT NULL,
    Description TEXT NULL,
    Quantity    NUMERIC NOT NULL,
    UnitPrice   NUMERIC NOT NULL,
    CONSTRAINT UQ_PurchaseOrderLines UNIQUE (POId, LineNumber),
    CONSTRAINT FK_PurchaseOrderLines_PO FOREIGN KEY (POId) REFERENCES PurchaseOrders(POId),
    CONSTRAINT FK_PurchaseOrderLines_Item FOREIGN KEY (ItemId) REFERENCES Items(ItemId)
);

-- Sales Orders
CREATE TABLE SalesOrders (
    SOId        INTEGER PRIMARY KEY AUTOINCREMENT,
    SONumber    TEXT NOT NULL,
    CustomerId  INTEGER NOT NULL,
    SODate      TEXT NOT NULL,
    Status      TEXT NOT NULL DEFAULT 'Open',
    SiteId      INTEGER NULL,
    CreatedAt   TEXT NOT NULL DEFAULT (datetime('now')),
    UpdatedAt   TEXT NULL,
    CONSTRAINT UQ_SalesOrders_Number UNIQUE (SONumber),
    CONSTRAINT FK_SalesOrders_Customer FOREIGN KEY (CustomerId) REFERENCES Customers(CustomerId),
    CONSTRAINT FK_SalesOrders_Site FOREIGN KEY (SiteId) REFERENCES Sites(SiteId)
);

-- Sales Order Lines
CREATE TABLE SalesOrderLines (
    SOLineId    INTEGER PRIMARY KEY AUTOINCREMENT,
    SOId        INTEGER NOT NULL,
    LineNumber  INTEGER NOT NULL,
    ItemId      INTEGER NULL,
    ItemCode    TEXT NOT NULL,
    Description TEXT NULL,
    Quantity    NUMERIC NOT NULL,
    UnitPrice   NUMERIC NOT NULL,
    CONSTRAINT UQ_SalesOrderLines UNIQUE (SOId, LineNumber),
    CONSTRAINT FK_SalesOrderLines_SO FOREIGN KEY (SOId) REFERENCES SalesOrders(SOId),
    CONSTRAINT FK_SalesOrderLines_Item FOREIGN KEY (ItemId) REFERENCES Items(ItemId)
);

-- Asset Transactions
CREATE TABLE AssetTransactions (
    AssetTxnId     INTEGER PRIMARY KEY AUTOINCREMENT,
    AssetId        INTEGER NOT NULL,
    FromLocationId INTEGER NULL,
    ToLocationId   INTEGER NULL,
    TxnType        TEXT NOT NULL,
    Quantity       INTEGER NOT NULL DEFAULT 1,
    TxnDate        TEXT NOT NULL DEFAULT (datetime('now')),
    Note           TEXT NULL,
    CONSTRAINT FK_AssetTransactions_Asset FOREIGN KEY (AssetId) REFERENCES Assets(AssetId),
    CONSTRAINT FK_AssetTransactions_FromLoc FOREIGN KEY (FromLocationId) REFERENCES Locations(LocationId),
    CONSTRAINT FK_AssetTransactions_ToLoc FOREIGN KEY (ToLocationId) REFERENCES Locations(LocationId)
);
"""

def reset_db(path: str = DB_PATH):
    if os.path.exists(path):
        os.remove(path)


def create_schema(conn: sqlite3.Connection):
    conn.executescript(SCHEMA_SQL)

def seed_data(conn: sqlite3.Connection):
    cur = conn.cursor()
    # Sites
    sites = [
        ("NYC", "New York HQ", "350 5th Ave", "New York", "USA", "America/New_York"),
        ("SFO", "San Francisco Branch", "1 Market St", "San Francisco", "USA", "America/Los_Angeles"),
        ("LON", "London Office", "221B Baker St", "London", "UK", "Europe/London"),
        ("BER", "Berlin Hub", "Pariser Platz", "Berlin", "Germany", "Europe/Berlin"),
        ("TOK", "Tokyo DC", "1-1 Chiyoda", "Tokyo", "Japan", "Asia/Tokyo"),
    ]
    cur.executemany(
        """
        INSERT INTO Sites (SiteCode, SiteName, AddressLine1, City, Country, TimeZone)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        sites,
    )

    # Locations
    # Build a map of SiteCode -> SiteId
    site_map = {row[0]: row[1] for row in cur.execute("SELECT SiteCode, SiteId FROM Sites").fetchall()}
    nyc_id = site_map["NYC"]
    sfo_id = site_map["SFO"]

    # Create one warehouse and two aisles per site
    loc_root_ids = {}
    loc_aisle_a_ids = {}
    loc_aisle_b_ids = {}
    for code, sid in site_map.items():
        # warehouse
        cur.execute(
            "INSERT INTO Locations (SiteId, LocationCode, LocationName) VALUES (?, ?, ?)",
            (sid, f"{code}-WH", f"{code} Warehouse"),
        )
        wh_id = cur.lastrowid
        loc_root_ids[code] = wh_id
        # aisle A1
        cur.execute(
            "INSERT INTO Locations (SiteId, LocationCode, LocationName, ParentLocationId) VALUES (?, ?, ?, ?)",
            (sid, f"{code}-WH-A1", f"{code} Aisle A1", wh_id),
        )
        loc_aisle_a_ids[code] = cur.lastrowid
        # aisle B1
        cur.execute(
            "INSERT INTO Locations (SiteId, LocationCode, LocationName, ParentLocationId) VALUES (?, ?, ?, ?)",
            (sid, f"{code}-WH-B1", f"{code} Aisle B1", wh_id),
        )
        loc_aisle_b_ids[code] = cur.lastrowid

    # Backwards-compatible handles for NYC/SFO specific IDs
    nyc_wh_id = loc_root_ids["NYC"]
    sfo_wh_id = loc_root_ids["SFO"]
    nyc_a1_id = loc_aisle_a_ids["NYC"]
    sfo_b1_id = loc_aisle_b_ids["SFO"]

    # Vendors
    vendors = [
        ("VEND-ACME", "ACME Supplies", "sales@acme.test", "+1-212-000-0000", "100 Main St", "New York", "USA"),
        ("VEND-GLOB", "Global Industrial", "hello@glob.test", "+1-415-000-0000", "200 Market St", "San Francisco",
         "USA"),
        ("VEND-OMEG", "Omega Tools", "contact@omega.test", "+44-20-0000-0001", "10 Fleet St", "London", "UK"),
        ("VEND-BER1", "Berliner Technik", "verkauf@ber1.test", "+49-30-0000-0002", "Unter den Linden 5", "Berlin",
         "Germany"),
        ("VEND-TOK1", "Tokyo Parts Co.", "sales@tok1.test", "+81-3-0000-0003", "2-2-2 Shibuya", "Tokyo", "Japan"),
        ("VEND-NOVA", "Nova Components", "hi@nova.test", "+1-917-000-0004", "5 Broadway", "New York", "USA"),
        ("VEND-PACF", "Pacific Gear", "sales@pacific.test", "+1-650-000-0005", "600 Embarcadero", "San Francisco",
         "USA"),
    ]
    cur.executemany(
        """
        INSERT INTO Vendors (VendorCode, VendorName, Email, Phone, AddressLine1, City, Country)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        vendors,
    )

    # Customers
    customers = [
        ("CUST-ALPHA", "Alpha Corp", "ap@alpha.test", "+1-646-111-1111", "10 Alpha Rd", "New York", "USA"),
        ("CUST-BETA", "Beta LLC", "ap@beta.test", "+1-628-222-2222", "20 Beta Ave", "San Francisco", "USA"),
        ("CUST-GAMMA", "Gamma Industries", "ap@gamma.test", "+44-20-1234-5678", "30 Gamma St", "London", "UK"),
        ("CUST-DELTA", "Delta GmbH", "ap@delta.test", "+49-30-2345-6789", "40 Delta Platz", "Berlin", "Germany"),
        ("CUST-EPS", "Epsilon KK", "ap@epsilon.test", "+81-3-4567-8901", "50 Epsilon Dori", "Tokyo", "Japan"),
        ("CUST-OMEGA", "Omega Retail", "ap@omegaretail.test", "+1-212-555-0100", "60 Omega Rd", "New York", "USA"),
        ("CUST-SIGMA", "Sigma Stores", "ap@sigma.test", "+1-415-555-0101", "70 Sigma Blvd", "San Francisco", "USA"),
        ("CUST-THETA", "Theta BV", "ap@theta.test", "+31-20-555-0102", "80 Theta Straat", "Amsterdam", "Netherlands"),
        ("CUST-LAMBDA", "Lambda SA", "ap@lambda.test", "+33-1-555-0103", "90 Lambda Rue", "Paris", "France"),
        ("CUST-PI", "Pi SpA", "ap@pi.test", "+39-06-555-0104", "100 Pi Via", "Rome", "Italy"),
    ]
    cur.executemany(
        """
        INSERT INTO Customers (CustomerCode, CustomerName, Email, Phone, BillingAddress1, BillingCity, BillingCountry)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        customers,
    )

    # Items
    items = [
        ("ITM-100", "Widget A", "Widgets", "EA"),
        ("ITM-200", "Gadget B", "Gadgets", "EA"),
        ("ITM-300", "Spare Part C", "Parts", "EA"),
        ("ITM-400", "Widget Pro", "Widgets", "EA"),
        ("ITM-401", "Widget Mini", "Widgets", "EA"),
        ("ITM-402", "Widget Ultra", "Widgets", "EA"),
        ("ITM-410", "Gadget Lite", "Gadgets", "EA"),
        ("ITM-411", "Gadget Max", "Gadgets", "EA"),
        ("ITM-412", "Gadget Plus", "Gadgets", "EA"),
        ("ITM-420", "Part D", "Parts", "EA"),
        ("ITM-421", "Part E", "Parts", "EA"),
        ("ITM-422", "Part F", "Parts", "EA"),
        ("ITM-430", "Component X", "Components", "EA"),
        ("ITM-431", "Component Y", "Components", "EA"),
        ("ITM-432", "Component Z", "Components", "EA"),
        ("ITM-440", "Consumable A", "Consumables", "BX"),
        ("ITM-441", "Consumable B", "Consumables", "BX"),
        ("ITM-442", "Consumable C", "Consumables", "BX"),
        ("ITM-450", "Spare Kit 1", "Kits", "KT"),
        ("ITM-451", "Spare Kit 2", "Kits", "KT"),
    ]
    cur.executemany(
        "INSERT INTO Items (ItemCode, ItemName, Category, UnitOfMeasure) VALUES (?, ?, ?, ?)",
        items,
    )

    # Lookup some IDs
    def get_id(table: str, key_col: str, key_val: str, id_col: str = None) -> int:
        if id_col is None:
            id_col = table[:-1] + "Id"  # naive plural to singular (works with our names)
        row = cur.execute(
            f"SELECT {id_col} FROM {table} WHERE {key_col} = ?",
            (key_val,),
        ).fetchone()
        return row[0]

    acme_id = get_id("Vendors", "VendorCode", "VEND-ACME", "VendorId")
    glob_id = get_id("Vendors", "VendorCode", "VEND-GLOB", "VendorId")
    omega_vendor_id = get_id("Vendors", "VendorCode", "VEND-OMEG", "VendorId")
    ber1_vendor_id = get_id("Vendors", "VendorCode", "VEND-BER1", "VendorId")
    tok1_vendor_id = get_id("Vendors", "VendorCode", "VEND-TOK1", "VendorId")
    nova_vendor_id = get_id("Vendors", "VendorCode", "VEND-NOVA", "VendorId")
    pacf_vendor_id = get_id("Vendors", "VendorCode", "VEND-PACF", "VendorId")

    alpha_id = get_id("Customers", "CustomerCode", "CUST-ALPHA", "CustomerId")
    beta_id = get_id("Customers", "CustomerCode", "CUST-BETA", "CustomerId")
    gamma_id = get_id("Customers", "CustomerCode", "CUST-GAMMA", "CustomerId")
    delta_id = get_id("Customers", "CustomerCode", "CUST-DELTA", "CustomerId")
    eps_id = get_id("Customers", "CustomerCode", "CUST-EPS", "CustomerId")
    omega_cust_id = get_id("Customers", "CustomerCode", "CUST-OMEGA", "CustomerId")
    sigma_id = get_id("Customers", "CustomerCode", "CUST-SIGMA", "CustomerId")
    theta_id = get_id("Customers", "CustomerCode", "CUST-THETA", "CustomerId")
    lambda_id = get_id("Customers", "CustomerCode", "CUST-LAMBDA", "CustomerId")
    pi_id = get_id("Customers", "CustomerCode", "CUST-PI", "CustomerId")

    # Build item code -> id map
    item_id_by_code = {code: iid for code, iid in cur.execute("SELECT ItemCode, ItemId FROM Items").fetchall()}
    itm100_id = item_id_by_code["ITM-100"]
    itm200_id = item_id_by_code["ITM-200"]
    itm300_id = item_id_by_code["ITM-300"]

    # Assets
    assets = [
        ("AST-0001", "Forklift 1", nyc_id, nyc_a1_id, "SN-FL-001", "Vehicle", "Active", 12500.00,
         date(2024, 5, 1).isoformat(), acme_id),
        ("AST-0002", "Conveyor A", sfo_id, sfo_b1_id, "SN-CNV-101", "Equipment", "Active", 8500.00,
         date(2024, 6, 15).isoformat(), glob_id),
        ("AST-0003", "Pallet Jack", nyc_id, nyc_wh_id, "SN-PJ-900", "Tool", "Maintenance", 600.00,
         date(2024, 7, 20).isoformat(), acme_id),
    ]
    # Generate additional assets up to 30
    asset_categories = ["Vehicle", "Equipment", "Tool", "IT", "Furniture"]
    asset_statuses = ["Active", "Maintenance", "Inactive"]
    vendor_cycle = [acme_id, glob_id, omega_vendor_id, ber1_vendor_id, tok1_vendor_id, nova_vendor_id, pacf_vendor_id]
    # deterministic site and location cycles
    site_cycle = [site_map[k] for k in sorted(site_map.keys())]
    loc_cycle = []
    for code in sorted(site_map.keys()):
        loc_cycle.extend([loc_root_ids[code], loc_aisle_a_ids[code], loc_aisle_b_ids[code]])
    base_num = 4
    for i in range(30 - len(assets)):
        tag = f"AST-{base_num + i:04d}"
        site_id_pick = site_cycle[i % len(site_cycle)]
        loc_id_pick = loc_cycle[i % len(loc_cycle)]
        name = f"Asset {base_num + i}"
        cat = asset_categories[i % len(asset_categories)]
        stat = asset_statuses[i % len(asset_statuses)]
        cost = float(500 + (i * 137) % 15000)
        purch_date = date(2024 + ((i // 12) % 2), ((i % 12) + 1), ((i % 27) + 1)).isoformat()
        vend = vendor_cycle[i % len(vendor_cycle)]
        serial = f"SN-{(1000 + i)}"
        assets.append((tag, name, site_id_pick, loc_id_pick, serial, cat, stat, cost, purch_date, vend))
    cur.executemany(
        """
        INSERT INTO Assets (AssetTag, AssetName, SiteId, LocationId, SerialNumber, Category, Status, Cost, PurchaseDate, VendorId)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        assets,
    )

    # Bills
    bills = [
        (acme_id, "BILL-1001", date(2024, 5, 5).isoformat(), date(2024, 6, 5).isoformat(), 12500.00, "USD", "Open"),
        (glob_id, "BILL-2001", date(2024, 6, 20).isoformat(), date(2024, 7, 20).isoformat(), 8500.00, "USD", "Open"),
    ]
    # add 8 more bills
    more_bills_vendors = [omega_vendor_id, ber1_vendor_id, tok1_vendor_id, nova_vendor_id, pacf_vendor_id, acme_id,
                          glob_id, omega_vendor_id]
    for i, v in enumerate(more_bills_vendors, start=1):
        num = f"BILL-{3000 + i}"
        bdate = date(2024 + (i % 2), ((i % 12) + 1), ((i % 27) + 1)).isoformat()
        dday = min(((i % 27) + 1) + 20, 28)
        ddate = date(2024 + (i % 2), ((i % 12) + 1), dday).isoformat()
        amt = float(2000 + i * 450)
        status = "Open" if i % 3 else "Closed"
        bills.append((v, num, bdate, ddate, amt, "USD", status))
    cur.executemany(
        """
        INSERT INTO Bills (VendorId, BillNumber, BillDate, DueDate, TotalAmount, Currency, Status)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        bills,
    )

    # Purchase Orders
    pos = [
        ("PO-10001", acme_id, date(2024, 5, 1).isoformat(), "Open", nyc_id),
        ("PO-10002", glob_id, date(2024, 6, 10).isoformat(), "Closed", sfo_id),
    ]
    # add 6 more POs
    po_vendors = [omega_vendor_id, ber1_vendor_id, tok1_vendor_id, nova_vendor_id, pacf_vendor_id, acme_id]
    po_sites = [site_map[code] for code in ["NYC", "SFO", "LON", "BER", "TOK", "NYC"]]
    for i in range(6):
        po_num = f"PO-100{3 + i:02d}"
        pos.append((po_num, po_vendors[i], date(2024 + (i % 2), (i % 12) + 1, (i % 27) + 1).isoformat(),
                    "Open" if i % 2 == 0 else "Closed", po_sites[i]))
    cur.executemany(
        """
        INSERT INTO PurchaseOrders (PONumber, VendorId, PODate, Status, SiteId)
        VALUES (?, ?, ?, ?, ?)
        """,
        pos,
    )

    po1_id = get_id("PurchaseOrders", "PONumber", "PO-10001", "POId")
    po2_id = get_id("PurchaseOrders", "PONumber", "PO-10002", "POId")

    polines = [
        (po1_id, 1, itm100_id, "ITM-100", "Widget A bulk", 100, 25.50),
        (po1_id, 2, itm300_id, "ITM-300", "Spare Part C", 50, 5.75),
        (po2_id, 1, itm200_id, "ITM-200", "Gadget B", 20, 99.99),
    ]
    # Add more PO lines for the newly created POs (2-3 lines each)
    extra_item_codes = [
        "ITM-400", "ITM-401", "ITM-402", "ITM-410", "ITM-411", "ITM-412",
        "ITM-420", "ITM-421", "ITM-422", "ITM-430", "ITM-431", "ITM-432",
        "ITM-440", "ITM-441", "ITM-442", "ITM-450", "ITM-451"
    ]
    po_numbers = [row[0] for row in cur.execute(
        "SELECT PONumber FROM PurchaseOrders WHERE PONumber NOT IN ('PO-10001','PO-10002') ORDER BY PONumber").fetchall()]
    for idx, pon in enumerate(po_numbers):
        po_id = get_id("PurchaseOrders", "PONumber", pon, "POId")
        lines_for_po = 2 + (idx % 2)
        for j in range(lines_for_po):
            code = extra_item_codes[(idx + j) % len(extra_item_codes)]
            iid = item_id_by_code[code]
            qty = float(10 + ((idx + j) * 5) % 120)
            price = float(5 + ((idx + j) * 3) % 200)
            line_no = j + 1
            polines.append((po_id, line_no, iid, code, f"{code} bulk", qty, price))
    cur.executemany(
        """
        INSERT INTO PurchaseOrderLines (POId, LineNumber, ItemId, ItemCode, Description, Quantity, UnitPrice)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        polines,
    )

    # Sales Orders
    sos = [
        ("SO-50001", alpha_id, date(2024, 7, 1).isoformat(), "Open", nyc_id),
        ("SO-50002", beta_id, date(2024, 7, 15).isoformat(), "Open", sfo_id),
    ]
    # Add 8 more SOs
    so_customers = [gamma_id, delta_id, eps_id, omega_cust_id, sigma_id, theta_id, lambda_id, pi_id]
    so_sites = [site_map[code] for code in ["LON", "BER", "TOK", "NYC", "SFO", "LON", "BER", "TOK"]]
    for i in range(8):
        so_num = f"SO-500{3 + i:02d}"
        sos.append((so_num, so_customers[i], date(2024 + (i % 2), (i % 12) + 1, (i % 27) + 1).isoformat(),
                    "Open" if i % 3 else "Closed", so_sites[i]))
    cur.executemany(
        """
        INSERT INTO SalesOrders (SONumber, CustomerId, SODate, Status, SiteId)
        VALUES (?, ?, ?, ?, ?)
        """,
        sos,
    )

    so1_id = get_id("SalesOrders", "SONumber", "SO-50001", "SOId")
    so2_id = get_id("SalesOrders", "SONumber", "SO-50002", "SOId")

    solines = [
        (so1_id, 1, itm100_id, "ITM-100", "Widget A", 10, 45.00),
        (so1_id, 2, itm300_id, "ITM-300", "Spare Part C", 5, 9.50),
        (so2_id, 1, itm200_id, "ITM-200", "Gadget B", 3, 149.99),
    ]
    # Additional SO lines (~25 total)
    so_numbers = [row[0] for row in cur.execute(
        "SELECT SONumber FROM SalesOrders WHERE SONumber NOT IN ('SO-50001','SO-50002') ORDER BY SONumber").fetchall()]
    so_item_codes = [
        "ITM-400", "ITM-401", "ITM-410", "ITM-411", "ITM-420", "ITM-430",
        "ITM-431", "ITM-440", "ITM-441", "ITM-450"
    ]
    for idx, son in enumerate(so_numbers):
        so_id = get_id("SalesOrders", "SONumber", son, "SOId")
        lines_for_so = 2 + (idx % 2)
        for j in range(lines_for_so):
            code = so_item_codes[(idx + j) % len(so_item_codes)]
            iid = item_id_by_code[code]
            qty = float(1 + ((idx + j) % 9))
            price = float(10 + ((idx + j) * 7) % 250)
            line_no = j + 1
            solines.append((so_id, line_no, iid, code, f"{code}", qty, price))
    cur.executemany(
        """
        INSERT INTO SalesOrderLines (SOId, LineNumber, ItemId, ItemCode, Description, Quantity, UnitPrice)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        solines,
    )

    # Asset Transactions
    asset_ids = [row[0] for row in cur.execute("SELECT AssetId FROM Assets ORDER BY AssetId").fetchall()]
    # all location ids for cycling
    all_loc_ids = [row[0] for row in cur.execute("SELECT LocationId FROM Locations ORDER BY LocationId").fetchall()]
    transactions = []
    # Seed initial receives for first 10 assets
    for i, aid in enumerate(asset_ids[:10]):
        to_loc = all_loc_ids[i % len(all_loc_ids)]
        transactions.append((aid, None, to_loc, "Receive", 1, "Initial receipt"))
    # Add more moves/adjusts to reach ~50 transactions
    txn_types = ["Move", "Adjust", "Repair"]
    count_target = 50
    idx = 0
    while len(transactions) < count_target:
        aid = asset_ids[idx % len(asset_ids)]
        from_loc = all_loc_ids[(idx + 1) % len(all_loc_ids)]
        to_loc = all_loc_ids[(idx + 2) % len(all_loc_ids)]
        ttype = txn_types[idx % len(txn_types)]
        transactions.append((aid, from_loc, to_loc, ttype, 1, f"Auto {ttype.lower()} #{idx + 1}"))
        idx += 1
    cur.executemany(
        """
        INSERT INTO AssetTransactions (AssetId, FromLocationId, ToLocationId, TxnType, Quantity, Note)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        transactions,
    )

    conn.commit()


def main():
    reset_db(DB_PATH)
    with sqlite3.connect(DB_PATH) as conn:
        # ensure foreign keys are on for this connection
        conn.execute("PRAGMA foreign_keys = ON;")
        create_schema(conn)
        seed_data(conn)
    print(f"SQLite database created and seeded at: {DB_PATH}")

if __name__ == '__main__':
    main()