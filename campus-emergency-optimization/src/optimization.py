import pandas as pd
import pulp

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
    (col for col in warehouses.columns if "capacity" in col.lower()),
    None
)

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