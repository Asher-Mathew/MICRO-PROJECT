import folium
import pandas as pd

# --- Assuming the optimization has already run and you have 'open_w' and 'ship' ---

# 1. Create a base map centered on the campus
# Using coordinates from geographic_bounds.csv if available, else average of facilities
map_center = [40.8075, -73.9626] 
campus_map = folium.Map(location=map_center, zoom_start=15, tiles="CartoDB positron")

# 2. Add Warehouses to the map
for _, row in warehouses.iterrows():
    w_id = row['warehouse_id']
    is_open = open_w[w_id].varValue == 1
    
    color = 'green' if is_open else 'gray'
    status = "OPEN" if is_open else "CLOSED"
    
    folium.Marker(
        location=[row['latitude'], row['longitude']],
        popup=f"Warehouse: {row['warehouse_name']}\nStatus: {status}",
        icon=folium.Icon(color=color, icon='info-sign')
    ).add_to(campus_map)

# 3. Add Facilities to the map
for _, row in facilities.iterrows():
    folium.CircleMarker(
        location=[row['latitude'], row['longitude']],
        radius=7,
        popup=f"Facility: {row['facility_name']}\nDemand: {row['daily_demand']}",
        color='red',
        fill=True,
        fill_color='red'
    ).add_to(campus_map)

# 4. Draw Transportation Routes (Lines) based on the Shipment Plan
for w in warehouses["warehouse_id"]:
    for f in facilities["facility_id"]:
        qty = ship[w, f].varValue
        if qty and qty > 0:
            # Get coordinates for the line
            w_coords = warehouses.loc[warehouses['warehouse_id'] == w, ['latitude', 'longitude']].values[0]
            f_coords = facilities.loc[facilities['facility_id'] == f, ['latitude', 'longitude']].values[0]
            
            # Draw line
            folium.PolyLine(
                locations=[w_coords, f_coords],
                weight=2, # You can scale weight based on qty if desired
                color='blue',
                opacity=0.6,
                tooltip=f"Route: {w} to {f} | Annual Qty: {qty:,.0f}"
            ).add_to(campus_map)

# 5. Save the map
campus_map.save("campus_distribution_map.html")
print("Map has been saved as campus_distribution_map.html. Open it in any browser!")