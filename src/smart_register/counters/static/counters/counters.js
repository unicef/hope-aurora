(function ($) {
    const baseUrl = $("#counters").data("url");
    const getLineData = (initialData, lengthOfDataChunks) => {
        const numOfChunks = Math.ceil(initialData.length / lengthOfDataChunks);
        const dataChunks = [];

        for (var i = 0; i < numOfChunks; i++) dataChunks[i] = [];

        initialData.forEach((entry, index) => {
            const chunkNumber = Math.floor(index / lengthOfDataChunks);
            dataChunks[chunkNumber];
            dataChunks[chunkNumber].push(entry);
        });

        const averagedChunks = dataChunks.map(chunkEntry => {
            const chunkAverage = chunkEntry.reduce(sumArray) / lengthOfDataChunks;
            return chunkEntry.map(chunkEntryValue => chunkAverage);
        });

        return averagedChunks.flat().map(e => Math.floor(e));
    };
    const sumArray = (accumulator, currentValue) => accumulator + currentValue;
    var m = moment();
    var currentDay = m.format("YYYY-MM-DD");
    var ctx = document.getElementById("myChart");
    var config = {
        type: "bar",
        options: {
            parsing: {
                key: "total",
                xAxisKey: "total",
                yAxisKey: "total"
            },
            responsive: false,
            layout: {
                padding: 0
            },
            plugins: {
                datalabels: {
                    anchor: "center",
                    align: "center",
                    formatter: Math.round,
                },
                title: {
                    display: true,
                },
                legend: {
                    display: true,
                }
            }
        },
        data: {
            labels: [],
            datasets: [{
                label: "",
                data: [],
                backgroundColor: "#2861c555",
                borderColor: "#2861c5",
                borderWidth: 1
            },
                {
                    // datalabels: {
                    //     labels: {
                    //         title: null
                    //     }
                    // },
                    data: [],
                    label: "",
                    type: "line",
                    borderColor: "#FF312D",
                    fill: false,
                    borderWidth: 1,
                    order: 1
                }

            ]
        }
    };
    Chart.register(ChartDataLabels);
    var myChart = new Chart(ctx, config);

    ctx.onclick = function (evt) {
        var points = myChart.getElementsAtEventForMode(evt, "nearest", {intersect: true}, true);
        if (points.length) {
            const firstPoint = points[0];
            const label = myChart.data.labels[firstPoint.index];
            const slabel = myChart.data.datasets[firstPoint.datasetIndex].label;
            const value = myChart.data.datasets[firstPoint.datasetIndex].data[firstPoint.index];
        }
    };

    ajax_chart({});

    function ajax_chart(params) {
        params.rnd = Math.random();
        const qs = new URLSearchParams(params).toString();
        $.getJSON(baseUrl + "?" + qs).done(function (response) {
            var chartData = response.data.map(a => a.total);
            var lineData = 0;[]
            if (chartData.length > 0) {
                const lineData = getLineData(chartData, chartData.length);
                myChart.data.datasets[1].data = lineData;
            } else {
                myChart.data.datasets[1].data = [];
            }

            myChart.data.labels = response.labels;
            myChart.data.datasets[0].data = chartData;
            myChart.data.datasets[0].rawData = response.data;
            myChart.data.datasets[0].label = "Total Registrations: " + response.total.toLocaleString();
            myChart.data.datasets[1].label = "Daily Average: " + lineData;

            myChart.options.plugins.title.text = response.label;
            myChart.update(); // finally update our chart
            currentDay = moment(response.day, "YYYY-MM-DD").format("YYYY-MM-DD");
        });
    }

    $("#prev").on("click", function (e) {
        var data;
        currentDay = moment(currentDay).subtract(1, "months").format("YYYY-MM-DD");
        data = {m: currentDay};
        ajax_chart(data);
    });
    $("#next").on("click", function (e) {
        var data;
        currentDay = moment(currentDay).add(1, "months").format("YYYY-MM-DD");
        data = {m: currentDay};
        ajax_chart(data);
    });
})(django.jQuery);
