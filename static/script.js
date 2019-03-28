function obj_in_array(array, obj_name) {
    for (let object of array) {
        if (object.name == obj_name) {
            return true;
        }
    }
    return false;
}

function random_colour() {
    let i = Math.floor(Math.random() * color_palette.length);
    return {
        fg: color_palette[i][500],
        bg: color_palette[i][300]
    }
}

function add_points_to_charts(points) {
    for (let point of points) {
        // Check if new data is from a know stream
        // if not, add new stream to page
        if (!obj_in_array(charts, point.stream)){
            // Add HTML element
            $("main").append(`
                <div class="chart-container graph">
                    <canvas id="${point.stream}"></canvas>
                </div>
            `);
            // Choose colours for chart
            const colour = random_colour();
            // Add chart to array
            charts.push({
                name: point.stream,
                object: new Chart(point.stream, {
                    type: 'line',
                    data: {
                        datasets: [{
                            label: point.stream,
                            backgroundColor: colour.fg,
                            borderColor: colour.bg,
                            fill: false,
                            data: []
                        }]
                    },
                    options: {
                        responsive: true,
                        scales: {
                            xAxes: [{
                                type: 'time',
                                display: true,
                                scaleLabel: {
                                    display: true,
                                    labelString: 'Date'
                                }
                            }],
                            yAxes: [{
                                display: true,
                                scaleLabel: {
                                    display: true,
                                    labelString: 'value'
                                }
                            }]
                        }
                    }
                })
            })
        }
        // find corresponding chart in array
        let chart = null;
        for (let elem of charts) {
            if (elem.name == point.stream) {
                chart = elem.object;
            }
        }
        // add point to chart
        chart.data.datasets[0].data.push({
            x: new Date(point.timestamp),
            y: point.value
        });
        // limit chart length
        if (chart.data.datasets[0].data.length > 50) {
            chart.data.datasets[0].data.shift();
        }
        chart.update();
        
    }
}

function request_data(period) {
    console.log(period);

    if (period == "realtime") {
        // clear existing charts
        charts = []
        $("main").html("");
        // Connect to the server
        eventSource = new EventSource("/stream");
        // Register event handler for server sent data.
        eventSource.onmessage = function(e) {
            msg = JSON.parse(e.data.replace(/'/g, '"'))
            add_points_to_charts(msg);
        }

    } else if (period == "day") {
        let req = new XMLHttpRequest();
        req.onreadystatechange = function() {
            if(this.readyState == 4 && this.status == 200) {
                // close realtime data stream
                eventSource.close();
                // Get new points
                points = JSON.parse(this.responseText);
                // clear existing charts
                charts = []
                $("main").html("");
                // Draw data
                add_points_to_charts(points);
            } else if (this.readyState == 4) {
                console.log("Unable to fetch data... Error ", this.status);
            }
        }
        req.open('POST', '/stream', true);
        req.setRequestHeader('content-type', 'application/x-www-form-urlencoded;charset=UTF-8');
        req.send("name=" + period);
    }
}


// Array of charts
let charts = [];

// Connect to the server
let eventSource;
request_data("realtime");