import { getDomainConfig } from "@vor/shared/domain";
import { fieldIsEmpty, isRequiredField } from "@vor/artworks/pure/form_state";

export function getValidationMixin() {
  const validationConfig = getDomainConfig().validation;
  const fieldToState = validationConfig.fieldToState;

  return {
    isRequired(name) {
      return isRequiredField(this, name, validationConfig);
    },
    isEmpty(name) {
      return fieldIsEmpty(this, name, fieldToState);
    },
    showRequired(name) {
      return this.isRequired(name) && this.isEmpty(name);
    },
    fieldInvalid(name) {
      return this.showRequired(name) || Boolean(this.fieldError(name));
    },
    fieldError(name) {
      const items = this.errors[name];
      if (!items || !items.length) {
        return "";
      }
      const item = items[0];
      if (item.persistent) {
        return item.message || item || "";
      }
      if (this.isRequired(name) && !this.isEmpty(name)) {
        return "";
      }
      return item.message || item || "";
    },
    formBanner() {
      return this.fieldError("__all__") || this.formError || "";
    },
  };
}
