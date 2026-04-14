import os
import json
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()

# Connect to Neo4j
driver = GraphDatabase.driver(
    os.getenv("NEO4J_URI"),
    auth=(os.getenv("NEO4J_USERNAME"), os.getenv("NEO4J_PASSWORD"))
)


def clear_database(session):
    """Clear all nodes and relationships from the database"""
    print("Clearing existing data...")
    session.run("MATCH (n) DETACH DELETE n")
    print("Database cleared.")


def create_constraints(session):
    """Create unique constraints for better performance and data integrity"""
    print("Creating constraints...")
    constraints = [
        "CREATE CONSTRAINT customer_id IF NOT EXISTS FOR (c:Customer) REQUIRE c.customerId IS UNIQUE",
        "CREATE CONSTRAINT vendor_id IF NOT EXISTS FOR (v:Vendor) REQUIRE v.vendorId IS UNIQUE",
        "CREATE CONSTRAINT site_id IF NOT EXISTS FOR (s:Site) REQUIRE s.siteId IS UNIQUE",
        "CREATE CONSTRAINT location_id IF NOT EXISTS FOR (l:Location) REQUIRE l.locationId IS UNIQUE",
        "CREATE CONSTRAINT item_id IF NOT EXISTS FOR (i:Item) REQUIRE i.itemId IS UNIQUE",
        "CREATE CONSTRAINT asset_id IF NOT EXISTS FOR (a:Asset) REQUIRE a.assetId IS UNIQUE",
        "CREATE CONSTRAINT bill_id IF NOT EXISTS FOR (b:Bill) REQUIRE b.billId IS UNIQUE",
        "CREATE CONSTRAINT po_id IF NOT EXISTS FOR (po:PurchaseOrder) REQUIRE po.poId IS UNIQUE",
        "CREATE CONSTRAINT so_id IF NOT EXISTS FOR (so:SalesOrder) REQUIRE so.soId IS UNIQUE",
        "CREATE CONSTRAINT pol_id IF NOT EXISTS FOR (pol:PurchaseOrderLine) REQUIRE pol.poLineId IS UNIQUE",
        "CREATE CONSTRAINT sol_id IF NOT EXISTS FOR (sol:SalesOrderLine) REQUIRE sol.soLineId IS UNIQUE",
        "CREATE CONSTRAINT asset_txn_id IF NOT EXISTS FOR (at:AssetTransaction) REQUIRE at.assetTxnId IS UNIQUE",
    ]

    for constraint in constraints:
        try:
            session.run(constraint)
        except Exception as e:
            print(f"Constraint already exists or error: {e}")

    print("Constraints created.")


def load_customers(session, customers):
    """Load customer nodes"""
    print(f"Loading {len(customers)} customers...")
    query = """
    UNWIND $customers AS customer
    CREATE (c:Customer {
        customerId: customer.customerId,
        customerCode: customer.customerCode,
        customerName: customer.customerName,
        email: customer.email,
        phone: customer.phone,
        billingAddress1: customer.billingAddress1,
        billingCity: customer.billingCity,
        billingCountry: customer.billingCountry,
        isActive: customer.isActive
    })
    """
    session.run(query, customers=customers)
    print(f"✓ {len(customers)} customers loaded")


def load_vendors(session, vendors):
    """Load vendor nodes"""
    print(f"Loading {len(vendors)} vendors...")
    query = """
    UNWIND $vendors AS vendor
    CREATE (v:Vendor {
        vendorId: vendor.vendorId,
        vendorCode: vendor.vendorCode,
        vendorName: vendor.vendorName,
        email: vendor.email,
        phone: vendor.phone,
        addressLine1: vendor.addressLine1,
        city: vendor.city,
        country: vendor.country,
        isActive: vendor.isActive
    })
    """
    session.run(query, vendors=vendors)
    print(f"✓ {len(vendors)} vendors loaded")


def load_sites(session, sites):
    """Load site nodes"""
    print(f"Loading {len(sites)} sites...")
    query = """
    UNWIND $sites AS site
    CREATE (s:Site {
        siteId: site.siteId,
        siteCode: site.siteCode,
        siteName: site.siteName,
        addressLine1: site.addressLine1,
        city: site.city,
        country: site.country,
        timeZone: site.timeZone,
        isActive: site.isActive
    })
    """
    session.run(query, sites=sites)
    print(f"✓ {len(sites)} sites loaded")


def load_locations(session, locations):
    """Load location nodes and relationships"""
    print(f"Loading {len(locations)} locations...")
    query = """
    UNWIND $locations AS location
    CREATE (l:Location {
        locationId: location.locationId,
        locationCode: location.locationCode,
        locationName: location.locationName,
        isActive: location.isActive
    })
    """
    session.run(query, locations=locations)

    # Create Location -> Site relationships
    print("Creating Location -> Site relationships...")
    query = """
    UNWIND $locations AS location
    MATCH (l:Location {locationId: location.locationId})
    MATCH (s:Site {siteId: location.siteId})
    CREATE (l)-[:LOCATED_AT]->(s)
    """
    session.run(query, locations=locations)

    # Create Location -> Parent Location relationships
    print("Creating Location -> Parent Location relationships...")
    query = """
    UNWIND $locations AS location
    WITH location WHERE location.parentLocationId IS NOT NULL
    MATCH (l:Location {locationId: location.locationId})
    MATCH (p:Location {locationId: location.parentLocationId})
    CREATE (l)-[:PARENT_LOCATION]->(p)
    """
    session.run(query, locations=locations)
    print(f"✓ {len(locations)} locations loaded")


def load_items(session, items):
    """Load item nodes"""
    print(f"Loading {len(items)} items...")
    query = """
    UNWIND $items AS item
    CREATE (i:Item {
        itemId: item.itemId,
        itemCode: item.itemCode,
        itemName: item.itemName,
        category: item.category,
        unitOfMeasure: item.unitOfMeasure,
        isActive: item.isActive
    })
    """
    session.run(query, items=items)
    print(f"✓ {len(items)} items loaded")


def load_assets(session, assets):
    """Load asset nodes and relationships"""
    print(f"Loading {len(assets)} assets...")
    query = """
    UNWIND $assets AS asset
    CREATE (a:Asset {
        assetId: asset.assetId,
        assetTag: asset.assetTag,
        assetName: asset.assetName,
        serialNumber: asset.serialNumber,
        category: asset.category,
        status: asset.status,
        cost: asset.cost,
        purchaseDate: asset.purchaseDate
    })
    """
    session.run(query, assets=assets)

    # Create Asset relationships
    print("Creating Asset -> Site relationships...")
    query = """
    UNWIND $assets AS asset
    MATCH (a:Asset {assetId: asset.assetId})
    MATCH (s:Site {siteId: asset.siteId})
    CREATE (a)-[:LOCATED_AT_SITE]->(s)
    """
    session.run(query, assets=assets)

    print("Creating Asset -> Location relationships...")
    query = """
    UNWIND $assets AS asset
    WITH asset WHERE asset.locationId IS NOT NULL
    MATCH (a:Asset {assetId: asset.assetId})
    MATCH (l:Location {locationId: asset.locationId})
    CREATE (a)-[:LOCATED_AT]->(l)
    """
    session.run(query, assets=assets)

    print("Creating Asset -> Vendor relationships...")
    query = """
    UNWIND $assets AS asset
    WITH asset WHERE asset.vendorId IS NOT NULL
    MATCH (a:Asset {assetId: asset.assetId})
    MATCH (v:Vendor {vendorId: asset.vendorId})
    CREATE (a)-[:SUPPLIED_BY]->(v)
    """
    session.run(query, assets=assets)
    print(f"✓ {len(assets)} assets loaded")


def load_bills(session, bills):
    """Load bill nodes and relationships"""
    print(f"Loading {len(bills)} bills...")
    query = """
    UNWIND $bills AS bill
    CREATE (b:Bill {
        billId: bill.billId,
        billNumber: bill.billNumber,
        billDate: bill.billDate,
        dueDate: bill.dueDate,
        totalAmount: bill.totalAmount,
        currency: bill.currency,
        status: bill.status
    })
    """
    session.run(query, bills=bills)

    # Create Bill -> Vendor relationships
    print("Creating Bill -> Vendor relationships...")
    query = """
    UNWIND $bills AS bill
    MATCH (b:Bill {billId: bill.billId})
    MATCH (v:Vendor {vendorId: bill.vendorId})
    CREATE (b)-[:BILLED_BY]->(v)
    """
    session.run(query, bills=bills)
    print(f"✓ {len(bills)} bills loaded")


def load_purchase_orders(session, pos, po_lines):
    """Load purchase order nodes and relationships"""
    print(f"Loading {len(pos)} purchase orders...")
    query = """
    UNWIND $pos AS po
    CREATE (p:PurchaseOrder {
        poId: po.poId,
        poNumber: po.poNumber,
        poDate: po.poDate,
        status: po.status
    })
    """
    session.run(query, pos=pos)

    # Create PO relationships
    print("Creating PurchaseOrder -> Vendor relationships...")
    query = """
    UNWIND $pos AS po
    MATCH (p:PurchaseOrder {poId: po.poId})
    MATCH (v:Vendor {vendorId: po.vendorId})
    CREATE (p)-[:ORDERED_FROM]->(v)
    """
    session.run(query, pos=pos)

    print("Creating PurchaseOrder -> Site relationships...")
    query = """
    UNWIND $pos AS po
    WITH po WHERE po.siteId IS NOT NULL
    MATCH (p:PurchaseOrder {poId: po.poId})
    MATCH (s:Site {siteId: po.siteId})
    CREATE (p)-[:DELIVERS_TO]->(s)
    """
    session.run(query, pos=pos)

    # Load PO Lines
    if po_lines:
        print(f"Loading {len(po_lines)} purchase order lines...")
        query = """
        UNWIND $po_lines AS pol
        CREATE (p:PurchaseOrderLine {
            poLineId: pol.poLineId,
            lineNumber: pol.lineNumber,
            itemCode: pol.itemCode,
            description: pol.description,
            quantity: pol.quantity,
            unitPrice: pol.unitPrice
        })
        """
        session.run(query, po_lines=po_lines)

        # Create POLine relationships
        print("Creating PurchaseOrderLine -> PurchaseOrder relationships...")
        query = """
        UNWIND $po_lines AS pol
        MATCH (p:PurchaseOrderLine {poLineId: pol.poLineId})
        MATCH (po:PurchaseOrder {poId: pol.poId})
        CREATE (p)-[:LINE_OF]->(po)
        """
        session.run(query, po_lines=po_lines)

        print("Creating PurchaseOrderLine -> Item relationships...")
        query = """
        UNWIND $po_lines AS pol
        WITH pol WHERE pol.itemId IS NOT NULL
        MATCH (p:PurchaseOrderLine {poLineId: pol.poLineId})
        MATCH (i:Item {itemId: pol.itemId})
        CREATE (p)-[:ORDERS_ITEM]->(i)
        """
        session.run(query, po_lines=po_lines)

    print(f"✓ {len(pos)} purchase orders loaded")


def load_sales_orders(session, sos, so_lines):
    """Load sales order nodes and relationships"""
    print(f"Loading {len(sos)} sales orders...")
    query = """
    UNWIND $sos AS so
    CREATE (s:SalesOrder {
        soId: so.soId,
        soNumber: so.soNumber,
        soDate: so.soDate,
        status: so.status
    })
    """
    session.run(query, sos=sos)

    # Create SO relationships
    print("Creating SalesOrder -> Customer relationships...")
    query = """
    UNWIND $sos AS so
    MATCH (s:SalesOrder {soId: so.soId})
    MATCH (c:Customer {customerId: so.customerId})
    CREATE (s)-[:ORDERED_BY]->(c)
    """
    session.run(query, sos=sos)

    print("Creating SalesOrder -> Site relationships...")
    query = """
    UNWIND $sos AS so
    WITH so WHERE so.siteId IS NOT NULL
    MATCH (s:SalesOrder {soId: so.soId})
    MATCH (site:Site {siteId: so.siteId})
    CREATE (s)-[:SHIPS_FROM]->(site)
    """
    session.run(query, sos=sos)

    # Load SO Lines
    if so_lines:
        print(f"Loading {len(so_lines)} sales order lines...")
        query = """
        UNWIND $so_lines AS sol
        CREATE (s:SalesOrderLine {
            soLineId: sol.soLineId,
            lineNumber: sol.lineNumber,
            itemCode: sol.itemCode,
            description: sol.description,
            quantity: sol.quantity,
            unitPrice: sol.unitPrice
        })
        """
        session.run(query, so_lines=so_lines)

        # Create SOLine relationships
        print("Creating SalesOrderLine -> SalesOrder relationships...")
        query = """
        UNWIND $so_lines AS sol
        MATCH (s:SalesOrderLine {soLineId: sol.soLineId})
        MATCH (so:SalesOrder {soId: sol.soId})
        CREATE (s)-[:LINE_OF]->(so)
        """
        session.run(query, so_lines=so_lines)

        print("Creating SalesOrderLine -> Item relationships...")
        query = """
        UNWIND $so_lines AS sol
        WITH sol WHERE sol.itemId IS NOT NULL
        MATCH (s:SalesOrderLine {soLineId: sol.soLineId})
        MATCH (i:Item {itemId: sol.itemId})
        CREATE (s)-[:SELLS_ITEM]->(i)
        """
        session.run(query, so_lines=so_lines)

    print(f"✓ {len(sos)} sales orders loaded")


def load_asset_transactions(session, asset_txns):
    """Load asset transaction nodes and relationships"""
    if not asset_txns:
        print("No asset transactions to load")
        return

    print(f"Loading {len(asset_txns)} asset transactions...")
    query = """
    UNWIND $asset_txns AS txn
    CREATE (at:AssetTransaction {
        assetTxnId: txn.assetTxnId,
        txnType: txn.txnType,
        quantity: txn.quantity,
        txnDate: txn.txnDate,
        note: txn.note
    })
    """
    session.run(query, asset_txns=asset_txns)

    # Create AssetTransaction -> Asset relationships
    print("Creating AssetTransaction -> Asset relationships...")
    query = """
    UNWIND $asset_txns AS txn
    MATCH (at:AssetTransaction {assetTxnId: txn.assetTxnId})
    MATCH (a:Asset {assetId: txn.assetId})
    CREATE (at)-[:TRANSACTION_FOR]->(a)
    """
    session.run(query, asset_txns=asset_txns)

    # Create AssetTransaction -> FROM_LOCATION relationships
    print("Creating AssetTransaction -> FROM_LOCATION relationships...")
    query = """
    UNWIND $asset_txns AS txn
    WITH txn WHERE txn.fromLocationId IS NOT NULL
    MATCH (at:AssetTransaction {assetTxnId: txn.assetTxnId})
    MATCH (l:Location {locationId: txn.fromLocationId})
    CREATE (at)-[:FROM_LOCATION]->(l)
    """
    session.run(query, asset_txns=asset_txns)

    # Create AssetTransaction -> TO_LOCATION relationships
    print("Creating AssetTransaction -> TO_LOCATION relationships...")
    query = """
    UNWIND $asset_txns AS txn
    WITH txn WHERE txn.toLocationId IS NOT NULL
    MATCH (at:AssetTransaction {assetTxnId: txn.assetTxnId})
    MATCH (l:Location {locationId: txn.toLocationId})
    CREATE (at)-[:TO_LOCATION]->(l)
    """
    session.run(query, asset_txns=asset_txns)

    print(f"✓ {len(asset_txns)} asset transactions loaded")


def populate_from_json(json_file_path):
    """Main function to populate Neo4j from JSON file"""
    print(f"Loading data from {json_file_path}...")

    with open(json_file_path, 'r') as f:
        data = json.load(f)

    with driver.session() as session:
        # Clear and setup
        clear_database(session)
        create_constraints(session)

        # Load nodes
        load_customers(session, data.get('customers', []))
        load_vendors(session, data.get('vendors', []))
        load_sites(session, data.get('sites', []))
        load_locations(session, data.get('locations', []))
        load_items(session, data.get('items', []))
        load_assets(session, data.get('assets', []))
        load_bills(session, data.get('bills', []))
        load_purchase_orders(session, data.get('purchaseOrders', []), data.get('purchaseOrderLines', []))
        load_sales_orders(session, data.get('salesOrders', []), data.get('salesOrderLines', []))
        load_asset_transactions(session, data.get('assetTransactions', []))

        print("\n" + "=" * 60)
        print("✓ Database population complete!")
        print("=" * 60)

        # Show summary
        print("\nDatabase Summary:")
        summary_query = """
        MATCH (n)
        RETURN labels(n)[0] as NodeType, count(n) as Count
        ORDER BY Count DESC
        """
        result = session.run(summary_query)
        for record in result:
            print(f"  {record['NodeType']}: {record['Count']}")

        print("\nRelationship Summary:")
        rel_query = """
        MATCH ()-[r]->()
        RETURN type(r) as RelType, count(r) as Count
        ORDER BY Count DESC
        """
        result = session.run(rel_query)
        for record in result:
            print(f"  {record['RelType']}: {record['Count']}")


if __name__ == "__main__":
    json_file = "/Users/nada/PycharmProjects/AI_AGENTS DHUB_ORANGE/InventoryChatbot-main/inventory_chatbot_langgraph/KG_neo4j/inventory_data.json"

    if not os.path.exists(json_file):
        print(f"Error: {json_file} not found!")
        print("Please create the JSON file first.")
    else:
        try:
            populate_from_json(json_file)
        except Exception as e:
            print(f"Error: {e}")
        finally:
            driver.close()