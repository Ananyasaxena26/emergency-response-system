import osmnx as ox

print(
    "Downloading road network for Delhi-NCR using tuple bounding box format..."
)

# In newer OSMnx versions, bbox expects a tuple: (left/west, bottom/south, right/east, top/north)
# Bounding box covering a central region of New Delhi
bbox = (77.200, 28.610, 77.235, 28.635)

# Download the graph passing bbox as a single tuple parameter
G = ox.graph_from_bbox(bbox=bbox, network_type="drive")

print("Success! Road graph loaded.")
print(f"Total Intersections (Nodes): {len(G.nodes)}")
print(f"Total Street Segments (Edges): {len(G.edges)}")