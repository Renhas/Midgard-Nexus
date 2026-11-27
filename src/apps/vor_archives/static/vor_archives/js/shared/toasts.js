import { notify } from "@toast/notify";

export const VOR_TOAST_ACTIONS = {
  open: "Открыть",
};

export const VOR_TOASTS = {
  collectionCreated: {
    title: "Коллекция создана",
    message: ({ name }) => (name ? `Название: ${name}` : ""),
  },
  collectionRenamed: {
    title: "Коллекция переименована",
    message: ({ oldName, name }) => (oldName && name ? `«${oldName}» → «${name}»` : name ? `«${name}»` : ""),
  },
  collectionDeleted: {
    title: "Коллекция удалена",
    message: ({ name }) => (name ? `Название: ${name}` : ""),
  },
  workAddedToCollection: {
    title: "Добавлено в коллекцию",
    message: ({ workTitle, collectionName }) =>
      workTitle && collectionName
        ? `«${workTitle}» в «${collectionName}»`
        : collectionName
          ? `«${collectionName}»`
          : "",
  },
  workRemovedFromCollection: {
    title: "Удалено из коллекции",
    message: ({ workTitle, collectionName }) =>
      workTitle && collectionName
        ? `«${workTitle}» из «${collectionName}»`
        : collectionName
          ? `«${collectionName}»`
          : "",
  },
  workCreated: {
    title: "Произведение создано",
    message: ({ title }) => (title ? `Название: ${title}` : ""),
  },
  workAttached: {
    title: "Произведение добавлено в список",
    message: ({ title }) => (title ? `Название: ${title}` : ""),
  },
  workSaved: {
    title: "Произведение изменено",
    message: ({ oldTitle, title, changedFields }) => formatEditMessage(oldTitle, title, changedFields),
  },
  workSaveFailed: {
    title: "Не удалось сохранить произведение",
  },
  workUpdateFailed: {
    title: "Не удалось сохранить изменения",
  },
  artworkDeleted: {
    title: "Произведение удалено",
    message: ({ title }) => (title ? `Название: ${title}` : ""),
  },
  artworksDeletedMany: {
    title: "Произведения удалены",
    message: ({ count }) => `Количество: ${count}`,
  },
  attrCreated: {
    title: "Атрибут создан",
    message: ({ name }) => (name ? `Название: ${name}` : ""),
  },
  attrUpdated: {
    title: "Атрибут изменён",
    message: ({ oldName, name, changedFields }) => formatEditMessage(oldName, name, changedFields),
  },
  attrDeleted: {
    title: "Атрибут удалён",
    message: ({ name }) => (name ? `Название: ${name}` : ""),
  },
  attrsDeletedMany: {
    title: "Атрибуты удалены",
    message: ({ count }) => `Количество: ${count}`,
  },
};

function formatEditMessage(oldName, newName, changedFields) {
  const lines = [];
  if (oldName && newName && oldName !== newName) {
    lines.push(`«${oldName}» → «${newName}»`);
  }
  const fields = (changedFields || []).filter(Boolean);
  if (fields.length) {
    lines.push(`Изменённые поля: ${fields.join(", ")}`);
  }
  return lines.join("\n");
}

function openAction(onClick) {
  return typeof onClick === "function" ? { label: VOR_TOAST_ACTIONS.open, onClick } : null;
}

export const vorNotify = {
  collectionCreated({ id, name }, onOpen) {
    notify.success(VOR_TOASTS.collectionCreated.title, {
      message: VOR_TOASTS.collectionCreated.message({ name }),
      action: id ? openAction(() => onOpen?.(id, name)) : null,
    });
  },
  collectionRenamed({ oldName, name }) {
    notify.success(VOR_TOASTS.collectionRenamed.title, {
      message: VOR_TOASTS.collectionRenamed.message({ oldName, name }),
    });
  },
  collectionDeleted({ name } = {}) {
    notify.success(VOR_TOASTS.collectionDeleted.title, {
      message: VOR_TOASTS.collectionDeleted.message({ name }),
    });
  },
  workAddedToCollection({ id, workTitle, collectionName, isCurrent }, onOpen) {
    notify.success(VOR_TOASTS.workAddedToCollection.title, {
      message: VOR_TOASTS.workAddedToCollection.message({ workTitle, collectionName }),
      action: !isCurrent && id ? openAction(() => onOpen?.(id, collectionName)) : null,
    });
  },
  workRemovedFromCollection({ workTitle, collectionName }) {
    notify.success(VOR_TOASTS.workRemovedFromCollection.title, {
      message: VOR_TOASTS.workRemovedFromCollection.message({ workTitle, collectionName }),
    });
  },
  workCreated({ title, url }, onOpen) {
    notify.success(VOR_TOASTS.workCreated.title, {
      message: VOR_TOASTS.workCreated.message({ title }),
      action: url ? openAction(() => onOpen?.(url)) : null,
    });
  },
  workAttached({ title, url }, onOpen) {
    notify.success(VOR_TOASTS.workAttached.title, {
      message: VOR_TOASTS.workAttached.message({ title }),
      action: url ? openAction(() => onOpen?.(url)) : null,
    });
  },
  workSaved({ oldTitle, title, changedFields }) {
    notify.success(VOR_TOASTS.workSaved.title, {
      message: VOR_TOASTS.workSaved.message({ oldTitle, title, changedFields }),
    });
  },
  workSaveFailed(message = "") {
    notify.error(VOR_TOASTS.workSaveFailed.title, { message });
  },
  workUpdateFailed(message = "") {
    notify.error(VOR_TOASTS.workUpdateFailed.title, { message });
  },
  artworksDeleted({ count, title }) {
    const num = Number(count || 0);
    if (num === 1) {
      notify.success(VOR_TOASTS.artworkDeleted.title, {
        message: VOR_TOASTS.artworkDeleted.message({ title }),
      });
      return;
    }
    notify.success(VOR_TOASTS.artworksDeletedMany.title, {
      message: VOR_TOASTS.artworksDeletedMany.message({ count: num }),
    });
  },
  attrSaved({ isCreate, oldName, name, changedFields }) {
    if (isCreate) {
      notify.success(VOR_TOASTS.attrCreated.title, {
        message: VOR_TOASTS.attrCreated.message({ name }),
      });
      return;
    }
    notify.success(VOR_TOASTS.attrUpdated.title, {
      message: VOR_TOASTS.attrUpdated.message({ oldName, name, changedFields }),
    });
  },
  attrsDeleted({ count, name }) {
    const num = Number(count || 0);
    if (num === 1) {
      notify.success(VOR_TOASTS.attrDeleted.title, {
        message: VOR_TOASTS.attrDeleted.message({ name }),
      });
      return;
    }
    notify.success(VOR_TOASTS.attrsDeletedMany.title, {
      message: VOR_TOASTS.attrsDeletedMany.message({ count: num }),
    });
  },
};

export default vorNotify;
