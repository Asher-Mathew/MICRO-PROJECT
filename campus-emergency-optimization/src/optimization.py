import pandas as pd
import pulp
import folium

DAYS = 365
BUDGET = 1500000

facilities = pd.read_csv("../data/facilities.csv")
demands = pd.read_csv("../data/demands.csv")
warehouses = pd.read_csv("../data/warehouses.csv")
transport = pd.read_csv("../data/transportation_costs.csv")

for df in [facilities, demands, warehouses, transport]:
    df.columns = df.columns.str.strip()

facilities = pd.merge(facilities, demands, on="facility_id")

facilities["annual_demand"] = facilities["daily_demand"] * DAYS

capacity_column = next(
    (col for col in warehouses.columns if "capacity" in col.lower()),None)

if capacity_column is None:
    raise Exception("Capacity column not found in warehouses.csv")

warehouses["annual_capacity"] = warehouses[capacity_column] * DAYS

construction_col = None
operation_col = None

for col in warehouses.columns:
    col_lower = col.lower()

    if "construction" in col_lower:
        construction_col = col

    if "operational" in col_lower or "operation" in col_lower:
        operation_col = col

if construction_col is None or operation_col is None:
    raise Exception("Cost columns not found in warehouses.csv")

cost_dict = {
    (row["from_warehouse"], row["to_facility"]): row["cost_per_unit"]
    for _, row in transport.iterrows()
}

model = pulp.LpProblem(
    "Campus_Emergency_Distribution",
    pulp.LpMinimize
)

ship = pulp.LpVariable.dicts(
    "Ship",
    [(w, f)
     for w in warehouses["warehouse_id"]
     for f in facilities["facility_id"]],
    lowBound=0
)

open_w = pulp.LpVariable.dicts(
    "OpenWarehouse",
    warehouses["warehouse_id"],
    cat="Binary"
)

transport_cost = pulp.lpSum(
    ship[w, f] * cost_dict[(w, f)]
    for w in warehouses["warehouse_id"]
    for f in facilities["facility_id"]
)

construction_cost = pulp.lpSum(
    open_w[w] *
    warehouses.loc[
        warehouses["warehouse_id"] == w,
        construction_col
    ].values[0] / 10
    for w in warehouses["warehouse_id"]
)

operational_cost = pulp.lpSum(
    open_w[w] *
    warehouses.loc[
        warehouses["warehouse_id"] == w,
        operation_col
    ].values[0] * DAYS
    for w in warehouses["warehouse_id"]
)

model += transport_cost + construction_cost + operational_cost

for f in facilities["facility_id"]:

    demand = facilities.loc[
        facilities["facility_id"] == f,
        "annual_demand"
    ].values[0]

    model += (
        pulp.lpSum(ship[w, f] for w in warehouses["warehouse_id"])
        == demand
    )

for w in warehouses["warehouse_id"]:

    capacity = warehouses.loc[
        warehouses["warehouse_id"] == w,
        "annual_capacity"
    ].values[0]

    model += (
        pulp.lpSum(ship[w, f] for f in facilities["facility_id"])
        <= capacity * open_w[w]
    )

model += pulp.lpSum(
    open_w[w] for w in warehouses["warehouse_id"]
) == 2

model += (
    transport_cost
    + construction_cost
    + operational_cost
    <= BUDGET
)

model.solve()

print("\nStatus:", pulp.LpStatus[model.status])

print("\nSelected Warehouses:")
for w in warehouses["warehouse_id"]:
    if open_w[w].value() == 1:
        print(" ", w)

print("\nShipment Plan:")
for w in warehouses["warehouse_id"]:
    for f in facilities["facility_id"]:

        value = ship[w, f].value()

        if value and value > 0:
            print(f"{w} -> {f} : {value:.2f} units")

print("\nCost Breakdown")
print("------------------")
print("Transportation Cost :", pulp.value(transport_cost))
print("Construction Cost   :", pulp.value(construction_cost))
print("Operational Cost    :", pulp.value(operational_cost))
print("Total Cost          :", pulp.value(model.objective))

if pulp.LpStatus[model.status] == 'Optimal':
    # 1. Initialize Map (Centered on the coordinates from your geographic_bounds.csv)
    # Based on your data: 40.8075, -73.9626
    campus_map = folium.Map(location=[40.8075, -73.9626], zoom_start=15, tiles="OpenStreetMap")

    # 2. Add Warehouses
    for _, row in warehouses.iterrows():
        w_id = row['warehouse_id']
        is_open = open_w[w_id].varValue == 1
        color = 'green' if is_open else 'red'
        
        folium.Marker(
            location=[row['latitude'], row['longitude']],
            popup=f"Warehouse: {row['warehouse_name']}<br>Status: {'OPEN' if is_open else 'CLOSED'}",
            icon=folium.Icon(color=color, icon='home')
        ).add_to(campus_map)

    # 3. Add Facilities
    for _, row in facilities.iterrows():
        folium.Marker(
            location=[row['latitude'], row['longitude']],
            popup=f"Facility: {row['facility_name']}<br>Annual Demand: {row['annual_demand']}",
            icon=folium.Icon(color='blue', icon='university', prefix='fa')
        ).add_to(campus_map)

    # 4. Draw Optimal Routes
    for w in warehouses["warehouse_id"]:
        for f in facilities["facility_id"]:
            qty = ship[w, f].varValue
            if qty and qty > 0:
                # Get start and end points
                start = warehouses.loc[warehouses['warehouse_id'] == w, ['latitude', 'longitude']].values[0]
                end = facilities.loc[facilities['facility_id'] == f, ['latitude', 'longitude']].values[0]
                
                folium.PolyLine(
                    locations=[start, end],
                    weight=3,
                    color='orange',
                    opacity=0.8,
                    tooltip=f"Route: {w} to {f} | Qty: {qty:,.0f}"
                ).add_to(campus_map)

    # 5. Save and Export
    campus_map.save("../campus_map.html")
    print("\nSuccess! Map saved as 'campus_map.html' in the project root.")
else:
    print("Optimization failed to find an optimal solution.")