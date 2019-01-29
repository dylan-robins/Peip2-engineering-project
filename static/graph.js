const data = [{
    label: 'Sine wave',
    values: []
}];

function init_graph(graph_id) {

    const graph = $(graph_id).epoch({
        type: 'time.line',
        data: data,
        axes: ["left", "bottom"]
    });

    // Connect to the server
    var socket = io.connect('http://' + document.domain + ':' + location.port + '/data');

    // Register event handler for server sent data.
    socket.on('point', function(msg) {
        console.log(msg)
        graph.push([{
            time: msg.timestamp,
            y: msg.value
        }]);
        if (data[0].values.length > 100) {
            data[0].values.shift();
        }
    });

    // Send message every 10s to keep the connection alive
    // one day, maybe, browsers will close down sockets on exit...
    setInterval(function(){
        socket.emit('keepalive');
    }, 10000);
}
$(document).ready(function() {
    init_graph('#graph');
});
