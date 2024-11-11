def evaluate_network_performance(nodes):
    """Evaluate the performance of nodes based on constraints."""
    for node in nodes:
        success_rate = 0
        for _ in range(10):
            success = authenticate_node_with_constraints(node)
            if success:
                success_rate += 1
        print(f"Node {node.node_id} success rate: {success_rate / 10 * 100}%")
        print(f"Remaining energy for {node.node_id}: {node.energy}")
