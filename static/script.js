// Event source object
let eventSource;
// Array of charts
let charts = [];
// Boolean to treat first eventSource response differently to rest
let first_receive = true;

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

function add_points_to_charts(points, scales, timeframe) {
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

        // Find point scale
        for (let obj of scales) {
            if (obj.stream == point.stream) {
                // Set y axis scale
                chart.options.scales.yAxes = [{
                    ticks: {
                        min: obj.min,
                        max: obj.max
                    }
                }];
                // calculate x axis scale
                let x_min; // date at start of axis
                let x_max = Date.now() // date at end of axis
                switch (timeframe) {
                    case "day":
                        x_min = new Date(Date.now() - 1000*60*60*24);
                        break;
                    case "week":
                        x_min = new Date(Date.now() - 1000*60*60*24*7);
                        break;
                    case "month":
                        x_min = new Date(Date.now() - 1000*60*60*24*30);
                        break;
                    case "year":
                        x_min = new Date(Date.now() - 1000*60*60*24*365);
                        break;
                }
                if (timeframe != "realtime") {
                    chart.options.scales.xAxes[0].time = {
                        min: x_min,
                        max: x_max
                    }
                }
            }
        }
        // limit chart length
        if (chart.data.datasets[0].data.length > 50) {
            chart.data.datasets[0].data.shift();
        }
        chart.update();
        
    }
}

function request_data(period) {
    // Display spinner
    $("main").html('<div class="lds-ring"><div></div><div></div><div></div><div></div></div>');

    console.log(period);
    
    // Request realtime points
    if (period == "realtime") {
        // Connect to the server
        eventSource = new EventSource("/stream");
        first_receive = true;
        // Register event handler for server sent data.
        eventSource.onmessage = function(e) {
            if (first_receive) {
                // clear existing charts
                charts = []
                $("main").html("");
                first_receive = false;
            }
            msg = JSON.parse(e.data.replace(/'/g, '"'))
            console.log(msg);
            add_points_to_charts(msg.data, msg.scales);
        }
    // Request historical points from a fixed timeframe
    } else {
        let req = new XMLHttpRequest();
        req.onreadystatechange = function() {
            if(this.readyState == 4 && this.status == 200) {
                // close realtime data stream
                eventSource.close();
                // Get new points
                msg = JSON.parse(this.responseText);
                console.log(msg);
                // clear existing charts
                $("main").html("");
                charts = []
                // Draw data
                add_points_to_charts(msg.data, msg.scales, period);
            } else if (this.readyState == 4) {
                console.log("Unable to fetch data... Error ", this.status);
            }
        }
        req.open('POST', '/stream', true);
        req.setRequestHeader('content-type', 'application/x-www-form-urlencoded;charset=UTF-8');
        req.send("name=" + period);
    }
}

// Connect to the server
request_data("realtime");
