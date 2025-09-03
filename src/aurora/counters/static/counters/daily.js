(function ($) {
    const day = $("#counters").data("day");
    const data = $("#counters").data("data");
    var m = moment();
    currentDay = m.format(day);

    $("#prev").on("click", function (e) {
        currentDay = moment(currentDay).subtract(1, "days").format("YYYY-MM-DD");
        location.href = "?day=" + currentDay
    });
    $("#next").on("click", function (e) {
        var data;
        currentDay = moment(currentDay).add(1, "days").format("YYYY-MM-DD");
        location.href = "?day=" + currentDay ;
    });

    Chart.register(ChartDataLabels);
            var ctx = document.getElementById("myChart").getContext("2d");
            var myChart = new Chart(ctx, {
                type: "bar",
                options: {
                    responsive: false,
                    layout: {
                        padding: 0
                    },
                    plugins: {
                        datalabels: {
                            anchor: "center",
                            align: "center",
                            formatter: Math.round,
                            padding: 10,
                            rotation: 0,
                            font: {
                                weight: "bold"
                            },
                        },
                        title: {
                            display: true,
                            text: moment(currentDay).format("dddd, Do MMMM YYYY")
                        },
                        legend: {
                            display: false,
                        }
                    }
                },
                data: {
                    labels: ["00:00", "01:00", "02:00", "03:00", "04:00", "05:00", "06:00", "07:00", "08:00", "09:00", "10:00", "11:00", "12:00", "13:00", "14:00", "15:00", "16:00", "17:00", "18:00", "19:00", "20:00", "21:00", "22:00", "23:00"],
                    datasets: [{
                        label: "",
                        data: data,
                        backgroundColor: "#2861c555",
                        borderColor: "#2861c5",
                        borderWidth: 1
                    }]
                }
            });

})($);
