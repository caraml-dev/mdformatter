import logging

from treelib import Tree

from typing import Dict, List


class Node:
    def __init__(self, id, parent_id, rank) -> None:
        self.id = id
        self.parent_id = parent_id
        self.rank = rank

    def to_dict(self) -> Dict:
        return {"id": self.id, "parent_id": self.parent_id, "rank": self.rank}

    def __lt__(self, other):
        return self.rank < other.rank

    def __repr__(self) -> str:
        return str(self.to_dict())


def build_tree(nodes: List[Node], sorting: int = Tree.WIDTH) -> List[Node]:
    """
    Builds a tree from the given list and returns it as a sorted list.

    Parameters
    ----------
    nodes: List[Node]
        A list of nodes that should be parsed into a tree.
    sorting: int
        The sorting order to be used when converting the tree back to a list.

    Returns
    -------
    The parsed tree structure as a list, sorted in the specified mode.
    """
    node_map, node_map_clone = {}, {}
    for node in nodes:
        node_map[node.id] = node
        node_map_clone[node.id] = node

    added = set()
    tree = Tree()
    while node_map:
        for node_id, node in node_map.items():
            if node.parent_id in added:
                tree.create_node(node, node_id, parent=node.parent_id)
                added.add(node_id)
                node_map.pop(node_id)
                break
            elif node.parent_id is None:
                tree.create_node(node, node_id)
                added.add(node_id)
                node_map.pop(node_id)
                break
    logging.debug(f"Parsed tree: {tree.to_dict()}")

    # Save the results as a list and return
    parsed_nodes = []
    for node_id in tree.expand_tree(mode=Tree.WIDTH):
        parsed_nodes.append(node_map_clone[node_id])
    return parsed_nodes
