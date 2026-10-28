(function () {
    window.DASH_CHART_COLORS = [
        "#A78BFA", "#60A5FA", "#34D399", "#F87171", "#FB923C",
        "#818CF8", "#FBBF24", "#22D3EE", "#F472B6", "#94A3B8",
        "#C084FC", "#38BDF8",
    ];

    window.MIN_SIZE_PX = 12;
    window.MAX_SIZE_PX = 48;

    window.centerTextPlugin = {
        id: "centerText",
        afterDraw(chart, args, opts) {
            if (!opts?.text) return;
            const { ctx, chartArea } = chart;
            if (!chartArea) return;
            const cx = (chartArea.left + chartArea.right) / 2;
            const cy = (chartArea.top + chartArea.bottom) / 2;
            ctx.save();
            ctx.textAlign = "center";
            ctx.textBaseline = "middle";
            ctx.font = "bold 28px sans-serif";
            ctx.fillStyle = "#E2E8F0";
            ctx.fillText(opts.text, cx, cy - 8);
            if (opts.label) {
                ctx.font = "12px sans-serif";
                ctx.fillStyle = "#94A3B8";
                ctx.fillText(opts.label, cx, cy + 16);
            }
            ctx.restore();
        },
    };

    window.readJsonScript = function (id) {
        const el = document.getElementById(id);
        if (!el) {
            return {};
        }
        try {
            return JSON.parse(el.textContent);
        } catch (error) {
            return {};
        }
    };

    window.formatDashPercent = function (value) {
        const number = Number(value || 0);
        if (!number) {
            return "0%";
        }
        if (Number.isInteger(number)) {
            return `${number}%`;
        }
        return `${number}%`;
    };
})();
