import { notify } from "@toast/notify";

export const VOR_TOAST_TEXT = {
  collectionCreated: "Коллекция создана",
  collectionRenamed: "Коллекция переименована",
  collectionDeleted: "Коллекция удалена",
  workAddedToCollection: "Добавлено в коллекцию",
  workRemovedFromCollection: "Убрано из коллекции",
  workCreated: "Произведение создано",
  workAttached: "Добавлено в список",
  workSaved: "Изменения сохранены",
  workSaveFailed: "Не удалось сохранить произведение",
  workUpdateFailed: "Не удалось сохранить изменения",
  deletedTitle: "Удалено",
  singleArtworkDeleted: "Произведение удалено из списка",
  manyArtworksDeleted: (count) => `Удалено произведений: ${count}`,
  attrCreated: "Атрибут создан",
  attrUpdated: "Атрибут обновлён",
  singleAttrDeleted: "Атрибут удалён",
  manyAttrsDeleted: (count) => `Удалено атрибутов: ${count}`,
  openActionLabel: "Открыть",
};

export const vorNotify = {
  collectionCreated({ id, name }, onOpen) {
    notify.success(VOR_TOAST_TEXT.collectionCreated, {
      message: name || "",
      action:
        id && typeof onOpen === "function"
          ? { label: VOR_TOAST_TEXT.openActionLabel, onClick: () => onOpen(id, name) }
          : null,
    });
  },
  collectionRenamed(name) {
    notify.success(VOR_TOAST_TEXT.collectionRenamed, { message: name || "" });
  },
  collectionDeleted() {
    notify.success(VOR_TOAST_TEXT.collectionDeleted);
  },
  workAddedToCollection({ id, name, isCurrent }, onOpen) {
    notify.success(VOR_TOAST_TEXT.workAddedToCollection, {
      message: name || "",
      action:
        !isCurrent && id && typeof onOpen === "function"
          ? { label: VOR_TOAST_TEXT.openActionLabel, onClick: () => onOpen(id, name) }
          : null,
    });
  },
  workRemovedFromCollection(name) {
    notify.success(VOR_TOAST_TEXT.workRemovedFromCollection, { message: name || "" });
  },
  workCreated(title) {
    notify.success(VOR_TOAST_TEXT.workCreated, { message: title || "" });
  },
  workAttached(title = "") {
    notify.success(VOR_TOAST_TEXT.workAttached, { message: title || "" });
  },
  workSaved(title) {
    notify.success(VOR_TOAST_TEXT.workSaved, { message: title || "" });
  },
  workSaveFailed(message = "") {
    notify.error(VOR_TOAST_TEXT.workSaveFailed, { message });
  },
  workUpdateFailed(message = "") {
    notify.error(VOR_TOAST_TEXT.workUpdateFailed, { message });
  },
  artworksDeleted(count) {
    const num = Number(count || 0);
    const message = num === 1 ? VOR_TOAST_TEXT.singleArtworkDeleted : VOR_TOAST_TEXT.manyArtworksDeleted(num);
    notify.success(VOR_TOAST_TEXT.deletedTitle, { message });
  },
  attrSaved({ isCreate, name }) {
    notify.success(isCreate ? VOR_TOAST_TEXT.attrCreated : VOR_TOAST_TEXT.attrUpdated, {
      message: name || "",
    });
  },
  attrsDeleted(count) {
    const num = Number(count || 0);
    const message = num === 1 ? VOR_TOAST_TEXT.singleAttrDeleted : VOR_TOAST_TEXT.manyAttrsDeleted(num);
    notify.success(VOR_TOAST_TEXT.deletedTitle, { message });
  },
};

export default vorNotify;
