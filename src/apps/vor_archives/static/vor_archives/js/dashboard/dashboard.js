document.addEventListener("alpine:init", () => {
    Alpine.data("vorDashStats", () => ({
        workTypes: ["book", "film", "game"],
        pieCharts: { types: null, statuses: null , age: null, rating: null},
        barCharts: { rating: null},
        statusMatrix: {},
        ageMatrix: {},
        ratingMatrix: {},
        spent: {},
        typeMeta: {},
        statusChoices: {},
        ageChoices: {},
        ratingChoices: {},

        init() {
            const data = window.readJsonScript("dash-stats-opts");
            this.statusMatrix = data.status_matrix || {};
            this.ageMatrix = data.age_matrix || {};
            this.ratingMatrix = data.rating_matrix || {};
            this.spent = data.spent || {};
            this.typeMeta = data.type_meta || {};
            this.statusChoices = data.status_choices || {}
            this.ageChoices = data.age_choices || {};
            this.ratingChoices = data.rating_choices || {};

            this.$nextTick(() => {
                this.renderPieTypes();
                this.renderPieStatus();
                this.renderPieAge();
                this.renderPieRating();
                this.renderBarRating();
            });

            this.$watch("pieStatusItems", () => {
                this.$nextTick(() => this.renderPieStatus());
            });
            this.$watch("pieAgeItems", () => {
                this.$nextTick(() => this.renderPieAge());
            });
            this.$watch("pieRatingItems", () => {
                this.$nextTick(() => this.renderPieRating());
            });
        },
        get worksTotalCount() {
            return Object.keys(this.typeMeta).reduce((sum, type) => sum + this.sumByRow(type, this.statusMatrix), 0);
        },
        get averageRating() {
            if (!this.workTypes.length) return "0.0";
            const total_res = this.workTypes.reduce((res, type) => {
                const row_res = this.sumByRowWithCount(type, this.ratingMatrix);
                res.sum += row_res.sum;
                res.count += row_res.count;
                return res;
            }, {"sum": 0, "count": 0});
            return total_res.count ? (total_res.sum / total_res.count).toFixed(1) : "0.0";
        },
        get spentProgressItems() {
            return Object.entries(this.spent).map(([key, value]) => ({
                key: key,
                count: value,
                unit: this.typeMeta[key].unit,
                icon: this.typeMeta[key].icon,
            }));
        },
        get pieTypesItems() {
            return Object.keys(this.typeMeta).map(type => ({
                label: this.typeMeta[type].label,
                count: this.sumByRow(type, this.statusMatrix),
            }));
        },
        get pieStatusItems() {
            if (!this.workTypes.length) return {};
            return Object.keys(this.statusChoices).map(status => ({
                label: this.statusChoices[status].label,
                count: this.sumByCol(status, this.statusMatrix),
            }));
        },
        get pieAgeItems() {
            if (!this.workTypes.length) return {};
            return Object.keys(this.ageChoices).map(age => ({
                label: this.ageChoices[age].label,
                count: this.sumByCol(age, this.ageMatrix),
            }));
        },
        get pieRatingItems() {
            if (!this.workTypes.length) return {};
            return Object.keys(this.ratingChoices).map(age => ({
                label: this.ratingChoices[age].label,
                count: this.sumByCol(age, this.ratingMatrix),
            }));
        },
        get barRatingItems() {
            return Object.keys(this.typeMeta).map(type => {
                const { sum, count } = this.sumByRowWithCount(type, this.ratingMatrix);
                return {
                label: this.typeMeta[type].label,
                count: this.avgStr(sum, count)};
            });
        },
        toggleType(type) {
            const index = this.workTypes.indexOf(type);
            if (index > -1) {
                this.workTypes.splice(index, 1);
            } else {
                this.workTypes.push(type);
            }
        },
        sumByCol(col, matrix) {
            return this.workTypes.reduce((sum, type) =>
                sum + (matrix[type]?.[col] || 0), 0);
        },
        sumByRow(row, matrix) {
            const row_data = matrix[row] || {};
            return Object.values(row_data).reduce((sum, val) => sum + val, 0)
        },
        sumByRowWithCount(row, matrix) {
            const row_data = matrix[row] || {};
            return Object.entries(row_data).reduce((res, [rating, count]) => {
                    if (rating === "") return res;
                    res.sum += Number(rating) * count;
                    res.count += count;
                    return res;
            }, {"sum": 0, "count": 0});
        },
        avgStr(sum, count) {
            return count ? (sum / count).toFixed(1) : "0.0";
        },
        formatNumber(number) {
            return Number(number).toFixed(1).toLocaleString("ru-RU");
        },
        _renderPie(key, canvas, items, { centerText = null } = {}) {
            if (!canvas || !window.Chart) return;
            Chart.getChart(canvas)?.destroy();
            this.pieCharts[key] = null;
            if (!items.length) return;

            this.pieCharts[key] = new Chart(canvas, {
                type: "doughnut",
                data: {
                    labels: items.map(i => i.label),
                    datasets: [{
                        data: items.map(i => i.count),
                        backgroundColor: items.map(
                            (_, index) => window.DASH_CHART_COLORS[index % window.DASH_CHART_COLORS.length]
                        ),
                        borderColor: "#1A233A",
                        borderWidth: 2,
                    }],
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: "bottom",
                            labels: {
                                boxWidth: 12,
                                color: "#E2E8F0",
                            },
                        },
                        centerText: centerText
                            ? {"text": centerText.value, "label": centerText.label, }
                            : undefined,
                    },
                },
                plugins: [window.centerTextPlugin]
            });
        },
        _renderBar(key, canvas, items) {
            if (!canvas || !window.Chart) return;
            Chart.getChart(canvas)?.destroy();
            this.barCharts[key] = null;
            if (!items.length) return;

            this.barCharts[key] = new Chart(canvas, {
                type: "bar",
                data: {
                    labels: items.map(i => i.label),
                    datasets: [{
                        data: items.map(i => i.count),
                        backgroundColor: items.map(
                            (_, index) => window.DASH_CHART_COLORS[index % window.DASH_CHART_COLORS.length]
                        ),
                        borderRadius: 4,
                        borderSkipped: false,
                        barThickness: "flex",
                        maxBarThickness: 96,
                    }],
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: {
                            beginAtZero: true,
                            suggestedMax: 10,
                            ticks: {
                                color: "#94A3B8",
                                font: { size: 11 },
                                precision: 0,     // целые числа на оси
                            },
                            grid: { color: "rgba(255,255,255,0.06)" },
                            border: { display: false },
                        },
                        x: {
                            ticks: {
                                color: "#94A3B8",
                                font: { size: 11 },
                            },
                            grid: { display: false },
                            border: { display: false },
                        },
                    },
                    plugins: {
                        legend: { display: false },
                        tooltip: {
                            backgroundColor: "#1A233A",
                            titleColor: "#E2E8F0",
                            bodyColor: "#E2E8F0",
                            borderColor: "rgba(167,139,250,0.3)",
                            borderWidth: 1,
                        },
                    },
                }
            });
        },
        renderPieTypes() {
            this._renderPie(
                "types",
                this.$refs.pieTypes,
                this.pieTypesItems,
                { centerText: { value: this.worksTotalCount, label: "всего" } }
            );
        },
        renderPieStatus() {
            this._renderPie(
                "statuses",
                this.$refs.pieStatus,
                this.pieStatusItems,
                { centerText: null }
            );
        },
        renderPieAge() {
            this._renderPie(
                "age",
                this.$refs.pieAge,
                this.pieAgeItems,
                { centerText: null }
            );
        },
        renderPieRating() {
            this._renderPie(
                "rating",
                this.$refs.pieRating,
                this.pieRatingItems,
                { centerText: { value: this.averageRating, label: "среднее"} }
            );
        },
        renderBarRating() {
            this._renderBar(
                "rating",
                this.$refs.barRating,
                this.barRatingItems,
            );
        },
    }));

    Alpine.data("vorDashAttrs", () => {
        const barCharts = Object.create(null);
        const cloudCharts = Object.create(null);
        return {
            attrView: "cloud",
            attrs: {},
            attrTotals: {},
            totalWorks: 0,
            histTopN: 12,
            init() {
                const data = window.readJsonScript("dash-attrs-opts");
                this.attrs = data.attrs || {};
                this.totalWorks = data.total;
                this.histTopN = data.histTopN || 12;
                this.calcAttrTotal();
                this.$nextTick(() => this._updateData());
                this.$watch("attrView", () => this._updateData());
                this.$watch("attrs", () => this._updateData());
            },
            calcAttrTotal() {
                this.attrTotals = Object.fromEntries(
                    Object.entries(this.attrs).map(([key, items]) => [
                        key,
                        items.reduce((sum, item) => sum + (item.count || 0), 0),
                    ])
                );
            },
            getItems(attrKey) {
                return this.attrs[attrKey];
            },
            getHistItems(attrKey) {
                return this.attrs[attrKey].slice(0, this.histTopN).map((item) => ({
                    label: item.name,
                    count: item.count,
                }));
            },
            getCloudItems(attrKey) {
                const items = this.attrs[attrKey];
                if (!items.length) return [];

                const counts = items.map(i => i.count);
                const min = Math.min(...counts);
                const max = Math.max(...counts);

                return items.map(item => {
                    const size = min === max ? (window.MIN_SIZE_PX + window.MAX_SIZE_PX) / 2
                        : window.MIN_SIZE_PX + ((item.count - min) / (max - min)) * (window.MAX_SIZE_PX - window.MIN_SIZE_PX);

                    return {
                        label: item.name,
                        count: item.count,
                        size,
                    };
                });
            },
            calcAttrShare(count, attrKey) {
                const total = this.attrTotals[attrKey];
                return total ? (count / total).toFixed(1) : 0;
            },
            formatPercent: window.formatDashPercent,
            setAttrView(view) {
                if (view === this.attrView) return;
                this.attrView = view;
            },
            _updateData() {
                if (this.attrView === "bar") {
                    this.$nextTick(() => this._renderAllBars());
                }
                if (this.attrView === "cloud") {
                    this.$nextTick(() => this._renderAllClouds());
                }
            },
            _deleteAllBars() {
                for (const key of Object.keys(barCharts)) {
                    try {
                        barCharts[key]?.stop();
                        barCharts[key]?.destroy();
                    } catch (e) {
                        console.error('[attrs] destroy failed for', key, e);
                    }
                    delete barCharts[key];
                }
            },
            _deleteAllClouds() {
                for (const key of Object.keys(cloudCharts)) {
                    try {
                        cloudCharts[key]?.stop();
                        cloudCharts[key]?.destroy();
                    } catch (e) {
                        console.error('[attrs] destroy failed for', key, e);
                    }
                    delete cloudCharts[key];
                }
            },
            _renderAllBars() {
                Object.keys(this.attrs).forEach((key) => this.renderSingleBar(key));
            },
            _renderAllClouds() {
                Object.keys(this.attrs).forEach((key) => this.renderSingleCloud(key));
            },
            _formBarData(items) {
                return {
                    labels: items.map(i => i.label),
                    data: items.map(i => i.count),
                    bgColor: items.map(
                        (_, index) => window.DASH_CHART_COLORS[index % window.DASH_CHART_COLORS.length]
                    ),
                }
            },
            _formCloudData(items) {
                return {
                    labels: items.map(i => i.label),
                    data: items.map(i => i.size),
                    counts: items.map(i => i.count),
                    color: window.DASH_CHART_COLORS[0],
                }
            },
            _renderBar(key, canvas, items) {
                if (!canvas || !window.Chart) return;
                const { labels, data, bgColor } = this._formBarData(items);
                if (barCharts[key]) {
                    const chart = barCharts[key];
                    chart.data.labels = labels;
                    chart.data.datasets[0].data = data;
                    chart.data.datasets[0].backgroundColor = bgColor;
                    chart.update();
                    return;
                }

                barCharts[key] = new Chart(canvas, {
                    type: "bar",
                    data: {
                        labels: labels,
                        datasets: [{
                            data: data,
                            backgroundColor: bgColor,
                            borderRadius: 4,
                            borderSkipped: false,
                            barThickness: "flex",
                            maxBarThickness: 96,
                        }],
                    },
                    options: {
                        indexAxis: 'y',
                        responsive: true,
                        maintainAspectRatio: false,
                        scales: {
                            y: {
                                beginAtZero: true,
                                ticks: {
                                    color: "#94A3B8",
                                    font: { size: 11 },
                                },
                                grid: { display: false },
                                border: { display: false },
                            },
                            x: {
                                ticks: {
                                    color: "#94A3B8",
                                    font: { size: 11 },
                                    precision: 0,
                                },
                                grid: { color: "rgba(255,255,255,0.06)" },
                                border: { display: false },
                            },
                        },
                        plugins: {
                            legend: { display: false },
                            tooltip: {
                                backgroundColor: "#1A233A",
                                titleColor: "#E2E8F0",
                                bodyColor: "#E2E8F0",
                                borderColor: "rgba(167,139,250,0.3)",
                                borderWidth: 1,
                            },
                        },
                    }
                });
            },
            _renderCloud(key, canvas, items) {
                if (!canvas || !window.Chart) return;
                const { labels, data, counts, color } = this._formCloudData(items);
                if (cloudCharts[key]) {
                    const chart = cloudCharts[key];
                    chart.data.labels = labels;
                    chart.data.datasets[0].data = data;
                    chart.data.datasets[0].color = color;
                    chart.data.datasets[0].counts = counts;
                    chart.update();
                    return;
                }

                cloudCharts[key] = new Chart(canvas, {
                    type: "wordCloud",
                    data: {
                        labels: labels,
                        datasets: [{
                            label: "",
                            data: data,
                            color: color,
                            counts: counts,
                            minRotation: 0,
                            maxRotation: 0,
                            padding: 8,
                        }],
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            legend: { display: false },
                            title: { display: false },
                            tooltip: {
                                backgroundColor: "#1A233A",
                                titleColor: "#E2E8F0",
                                bodyColor: "#E2E8F0",
                                borderColor: "rgba(167,139,250,0.3)",
                                borderWidth: 1,
                                callbacks: {
                                    label: (ctx) => {
                                        const counts = ctx.dataset.counts ?? [];
                                        return `${counts[ctx.dataIndex] ?? ''}`;
                                    },
                                },
                            },
                        },
                    }
                });
            },
            renderSingleBar(attrKey) {
                this._renderBar(
                    attrKey,
                    this.$refs[`bar-${attrKey}`],
                    this.getHistItems(attrKey),
                );
            },
            renderSingleCloud(attrKey) {
                this._renderCloud(
                    attrKey,
                    this.$refs[`cloud-${attrKey}`],
                    this.getCloudItems(attrKey),
                );
            },
            destroy() {
                this._deleteAllBars();
            }
        }
    });
});
