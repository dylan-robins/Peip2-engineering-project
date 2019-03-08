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

function create_chart(chart_array, chart_name) {
    // Add HTML element
    $("main").append(`
        <div class="chart-container graph">
            <canvas id="${chart_name}"></canvas>
        </div>
    `);

    // Choose colours for chart
    const colour = random_colour();
    // Add chart to array
    charts.push({
        name: chart_name,
        object: new Chart(chart_name, {
            type: 'line',
            data: {
                datasets: [{
                    label: chart_name,
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

// Array of charts
let charts = [];

// Connect to the server
var socket = io.connect('http://' + document.domain + ':' + location.port + '/data');

// Register event handler for server sent data.
socket.on('point', function(msg) {
    // console.log(msg)
    // Check if new data is from a know stream
    if (!obj_in_array(charts, msg.stream)){
        // New stream: create a new chart
        create_chart(charts, msg.stream);
    }

    // find corresponding chart in array
    let chart = null;
    for (let elem of charts) {
        if (elem.name == msg.stream) {
            chart = elem.object;
        }
    }
    // add point to chart
    chart.data.datasets[0].data.push({
        x: Date(msg.timestamp * 1000),
        y: msg.value
    });

    // limit chart length
    if (chart.data.datasets[0].data.length > 50) {
        chart.data.datasets[0].data.shift();
    }

    chart.update();

});

// Send message every 10s to keep the connection alive
// one day, maybe, browsers will close down sockets on exit...
setInterval(function(){
    socket.emit('keepalive');
}, 10000);
