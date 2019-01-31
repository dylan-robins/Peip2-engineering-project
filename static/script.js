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
        <div class="graph">
            <h2>${chart_name}</h2>
            <canvas id="${chart_name}" width="400" height="200"></canvas>
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
						},
						ticks: {
							major: {
								fontStyle: 'bold',
								fontColor: '#000000'
							}
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

    let chart = null;
    for (let elem of charts) {
        if (elem.name == msg.stream) {
            chart = elem.object;
        }
    }

    chart.data.datasets[0].data.push({
        x: Date(msg.timestamp * 1000),
        y: msg.value
    });

    chart.update();

    // if (data[0].values.length > 400) {
    //     data[0].values.shift();
    // }
});

// Send message every 10s to keep the connection alive
// one day, maybe, browsers will close down sockets on exit...
setInterval(function(){
    socket.emit('keepalive');
}, 10000);
