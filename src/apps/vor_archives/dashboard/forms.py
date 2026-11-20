from django import forms


class HeatmapFilterForm(forms.Form):
    year = forms.IntegerField(required=False, min_value=1970, max_value=2100)

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
