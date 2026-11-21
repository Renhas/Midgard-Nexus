from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect

from ..catalog import DEFAULT_DASH_TAB
from ..services import TAB_CONTEXT_BUILDERS
from .utils import dash_tab_or_404, render_dashboard_shell


@login_required
def dashboard(request):
    """Страница дашборда — редирект на вкладку статистики."""
    return redirect("vor_archives:dashboard:tab", tab=DEFAULT_DASH_TAB)


@login_required
def dashboard_tab(request, tab: str):
    """Оболочка дашборда для выбранной вкладки."""
    resolved_tab = dash_tab_or_404(tab)
    builder = TAB_CONTEXT_BUILDERS.get(resolved_tab["kind"])
    extra = builder(request.user, request.GET) if builder else {}
    return render_dashboard_shell(request, resolved_tab, extra)
