import { describe, expect, it } from "vitest";
import { collectRequiredFields, fieldIsEmpty, fieldValue, isRequiredField } from "@vor/artworks/pure/form_state";

describe("fieldValue and fieldIsEmpty", () => {
  const fieldToState = {
    field_text: { key: "fieldText", trim: true },
    field_num: { key: "fieldNum" },
  };

  it("reads mapped state values", () => {
    const state = { fieldText: "hello", fieldNum: 0 };
    expect(fieldValue(state, "field_text", fieldToState)).toBe("hello");
    expect(fieldValue(state, "field_num", fieldToState)).toBe(0);
    expect(fieldValue(state, "unknown", fieldToState)).toBeUndefined();
  });

  it("trims string fields when trim flag is enabled", () => {
    expect(fieldIsEmpty({ fieldText: "   " }, "field_text", fieldToState)).toBe(true);
    expect(fieldIsEmpty({ fieldText: " ok " }, "field_text", fieldToState)).toBe(false);
  });

  it("treats 0 as non-empty for numeric fields", () => {
    expect(fieldIsEmpty({ fieldNum: 0 }, "field_num", fieldToState)).toBe(false);
    expect(fieldIsEmpty({ fieldNum: "" }, "field_num", fieldToState)).toBe(true);
    expect(fieldIsEmpty({ fieldNum: null }, "field_num", fieldToState)).toBe(true);
  });
});

describe("collectRequiredFields and isRequiredField", () => {
  const validationConfig = {
    requiredByType: {
      type_a: ["title", "count"],
      type_b: ["title"],
    },
    conditionalRequired: [
      {
        workType: "type_b",
        when: { subType: "special" },
        fields: ["extra_field"],
      },
    ],
  };

  it("collects base required fields for workType", () => {
    const state = { workType: "type_a" };
    expect(collectRequiredFields(state, validationConfig)).toEqual(["title", "count"]);
    expect(isRequiredField(state, "count", validationConfig)).toBe(true);
    expect(isRequiredField(state, "extra_field", validationConfig)).toBe(false);
  });

  it("appends conditional fields when condition matches", () => {
    const matching = { workType: "type_b", subType: "special" };
    const nonMatching = { workType: "type_b", subType: "regular" };

    expect(collectRequiredFields(matching, validationConfig)).toEqual(["title", "extra_field"]);
    expect(isRequiredField(matching, "extra_field", validationConfig)).toBe(true);
    expect(isRequiredField(nonMatching, "extra_field", validationConfig)).toBe(false);
  });
});
