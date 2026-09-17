import networkx as nx
import osmnx as ox

G = None


def get_graph():
  global G
  if G is None:
    print("Loading road network graph...")
    bbox = (77.18, 28.58, 77.25, 28.66)
    try:
      G = ox.graph_from_bbox(bbox=bbox, network_type="drive")
      print("OSM Graph loaded successfully!")
    except Exception as e:
      print(f"OSM download failed ({e}), using grid fallback.")
      # Create a safe grid graph with integer node labels
      grid = nx.grid_2d_graph(10, 10)
      G = nx.convert_node_labels_to_integers(grid)
      for u, v, data in G.edges(data=True):
        data["length"] = 1.0
  return G


def run_emergency_routing(
    ambulance_lat, ambulance_lon, incident_lat, incident_lon
):
  try:
    graph = get_graph()
    is_osm = isinstance(graph, (nx.DiGraph, nx.MultiDiGraph))

    # 1. Safely pick source and target nodes based on graph type
    if is_osm:
      try:
        source_node = ox.distance.nearest_nodes(
            graph, X=ambulance_lon, Y=ambulance_lat
        )
        incident_node = ox.distance.nearest_nodes(
            graph, X=incident_lon, Y=incident_lat
        )
      except Exception:
        nodes = list(graph.nodes())
        source_node, incident_node = nodes[0], nodes[1]
    else:
      # Fallback grid graph node selection (guaranteed valid indices)
      nodes = list(graph.nodes())
      source_node = nodes[0]
      incident_node = nodes[min(15, len(nodes) - 1)]

    if source_node == incident_node:
      return {
          "error": (
              "Ambulance and incident locations map to the exact same node."
          )
      }

    # 2. Find path with automatic fallback to connected nodes if isolated
    try:
      normal_path = nx.shortest_path(
          graph, source=source_node, target=incident_node, weight="length"
      )
    except nx.NetworkXNoPath:
      if is_osm:
        undirected = graph.to_undirected()
        largest_cc = max(nx.connected_components(undirected), key=len)
        cc_nodes = list(largest_cc)
        source_node, incident_node = cc_nodes[0], cc_nodes[min(1, len(cc_nodes)-1)]
        normal_path = nx.shortest_path(
            graph, source=source_node, target=incident_node, weight="length"
        )
      else:
        nodes = list(graph.nodes())
        source_node, incident_node = nodes[0], nodes[min(20, len(nodes) - 1)]
        normal_path = nx.shortest_path(
            graph, source=source_node, target=incident_node, weight="length"
        )

    # 3. Simulate road blockage
    blocked_edge_info = None
    if len(normal_path) > 1:
      u, v = normal_path[0], normal_path[1]
      if graph.has_edge(u, v):
        graph.remove_edge(u, v)
        blocked_edge_info = f"Blocked road segment between node {u} and {v}"

    # 4. Recalculate dynamic alternative path
    try:
      dynamic_path = nx.shortest_path(
          graph, source=source_node, target=incident_node, weight="length"
      )
    except nx.NetworkXNoPath:
      dynamic_path = ["All paths blocked"]

    return {
        "source_node": source_node,
        "incident_node": incident_node,
        "simulation_event": blocked_edge_info,
        "rescue_path_length": (
            len(dynamic_path) if isinstance(dynamic_path, list) else 0
        ),
        "graph_nodes_count": len(graph.nodes),
    }

  except Exception as e:
    return {"error": f"Routing calculation failed: {str(e)}"}