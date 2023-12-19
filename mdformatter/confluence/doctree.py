import logging

from treelib import Tree

from typing import Dict, List


class Node:
    def __init__(self, id, parent_id) -> None:
        self.id = id
        self.parent_id = parent_id

    def to_dict(self) -> Dict:
        return {"id": self.id, "parent_id": self.parent_id}

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
    item_parent_map = {}
    for node in nodes:
        item_parent_map[node.id] = node.parent_id

    added = set()
    tree = Tree()
    while item_parent_map:
        for item, parent in item_parent_map.items():
            if parent in added:
                tree.create_node(item, item, parent=parent)
                added.add(item)
                item_parent_map.pop(item)
                break
            elif parent is None:
                tree.create_node(item, item)
                added.add(item)
                item_parent_map.pop(item)
                break
    logging.debug(f"Parsed tree: {tree.to_dict()}")

    # Save the results as a list and return
    parsed_nodes = []
    for node in tree.expand_tree(mode=Tree.WIDTH):
        parsed_nodes.append(Node(id=node, parent_id=tree.ancestor(node)))
    return parsed_nodes
