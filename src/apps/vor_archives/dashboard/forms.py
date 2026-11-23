from django import forms

from .catalog import HEATMAP_MAX_YEAR, HEATMAP_MIN_YEAR


class HeatmapFilterForm(forms.Form):
    year = forms.IntegerField(
        required=False,
        min_value=HEATMAP_MIN_YEAR,
        max_value=HEATMAP_MAX_YEAR,
    )

    def get_year(self) -> int | None:
        if self.is_valid():
            return self.cleaned_data.get("year")
        return None


class FeedPaginationForm(forms.Form):
    offset = forms.IntegerField(required=False, min_value=0)

    def get_offset(self) -> int:
        if self.is_valid():
            return self.cleaned_data.get("offset") or 0
        return 0
