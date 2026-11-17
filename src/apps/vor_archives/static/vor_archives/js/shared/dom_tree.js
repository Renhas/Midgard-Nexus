export function getCollectionPathFromTree(id) {
  const item = document.querySelector(`.vor-collection-item[data-collection-id="${id}"]`);
  const path = [];
  let node = item?.closest(".vor-collection-tree-node");
  while (node) {
    const row = node.querySelector(":scope > .vor-collection-item");
    if (row?.dataset.collectionId) {
      path.unshift({
        id: Number(row.dataset.collectionId),
        name: row.dataset.collectionName || "",
      });
    }
    node = node.parentElement?.closest(".vor-collection-tree-node") || null;
  }
  return path;
}

export function getCollectionNode(id) {
  return document.querySelector(`.vor-collection-tree-node[data-collection-id="${id}"]`);
}

export function getCollectionSiblings(node) {
  const parent = node?.parentElement;
  if (!parent) {
    return [];
  }
  return [...parent.querySelectorAll(":scope > .vor-collection-tree-node")];
}
