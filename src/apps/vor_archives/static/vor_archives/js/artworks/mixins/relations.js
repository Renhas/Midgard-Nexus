import { VorApi } from "@vor/artworks/api";
import {
  allowedRelationTypes as pureAllowedRelationTypes,
  relationKey as pureRelationKey,
  relationLabelFor as pureRelationLabelFor,
} from "@vor/artworks/pure/relations";

export function getRelationsMixin({
  relations = [],
  relationTypes = [],
  isAdd = false,
} = {}) {
  return {
    relations,
    relationTypes,
    isAdd: Boolean(isAdd),
    relAdding: false,
    relQuery: "",
    relResults: [],
    relPick: null,
    relPickType: "other",
    relTypeEdit: null,
    relationsEditable() {
      return this.isAdd || this.editing === true;
    },
    allowedRelationTypes(otherType) {
      return pureAllowedRelationTypes(this.relationTypes, otherType, this.workType);
    },
    relationKey(item) {
      return pureRelationKey(item);
    },
    relationLabelFor(type, direction) {
      return pureRelationLabelFor(this.relationTypes, type, direction);
    },
    toggleRelationType(item) {
      const key = this.relationKey(item);
      this.relTypeEdit = this.relTypeEdit === key ? null : key;
    },
    setRelationType(item, value) {
      item.relation_type = value;
      item.label = this.relationLabelFor(value, item.direction || "out");
      this.relTypeEdit = null;
    },
    removeRelation(item) {
      this.relations = this.relations.filter((rel) => rel !== item);
    },
    startRelationAdd() {
      this.relAdding = true;
      this.relQuery = "";
      this.relResults = [];
      this.relPick = null;
      this.relPickType = "other";
    },
    cancelRelationAdd() {
      this.relAdding = false;
      this.relPick = null;
      this.relQuery = "";
      this.relResults = [];
    },
    async searchRelatedWorks() {
      const query = String(this.relQuery || "").trim();
      if (!query || !this.relationSearchUrl) {
        this.relResults = [];
        return;
      }
      const wId = this.workId || this.createdWorkId || "";
      const data = await VorApi.searchRelatedWorks(this.relationSearchUrl, {
        q: query,
        exclude_type: this.workType,
        exclude_id: String(wId),
      });
      const taken = new Set(
        this.relations.map((item) => `${item.type_key}-${item.work_id}`)
      );
      this.relResults = (data?.results || []).filter(
        (item) => !taken.has(`${item.type_key}-${item.work_id}`)
      );
    },
    commitRelationAdd() {
      if (!this.relPick) return;
      const allowed = this.allowedRelationTypes(this.relPick.type_key).map((item) => item.value);
      const type = allowed.includes(this.relPickType) ? this.relPickType : allowed[0];
      this.relations = [
        ...this.relations,
        {
          id: null,
          title: this.relPick.title,
          cover_url: this.relPick.cover_url,
          icon: this.relPick.icon,
          type_key: this.relPick.type_key,
          work_id: this.relPick.work_id,
          relation_type: type,
          direction: "out",
          label: this.relationLabelFor(type, "out"),
        },
      ];
      this.cancelRelationAdd();
    },
    relationsJson() {
      return JSON.stringify(
        this.relations.map((item) => ({
          id: item.id || null,
          relation_type: item.relation_type,
          type_key: item.type_key,
          work_id: item.work_id,
        }))
      );
    }
  };
}
