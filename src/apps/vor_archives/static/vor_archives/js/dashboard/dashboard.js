import { getAlpine } from "@lib/alpine";
import { createDashAttrsComponent } from "@vor/dashboard/attrs";
import { createDashStatsComponent } from "@vor/dashboard/stats";

document.addEventListener("alpine:init", () => {
  const alpine = getAlpine();
  alpine.data("vorDashStats", createDashStatsComponent);
  alpine.data("vorDashAttrs", createDashAttrsComponent);
});
