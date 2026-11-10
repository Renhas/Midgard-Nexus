export function flattenCollectionTree(nodes, level = 0) {
  const out = [];
  (nodes || []).forEach((node) => {
    out.push({
      id: node.id,
      name: node.name,
      in_collection: Boolean(node.in_collection),
      level,
    });
    if (node.children?.length) {
      out.push(...flattenCollectionTree(node.children, level + 1));
    }
  });
  return out;
}
