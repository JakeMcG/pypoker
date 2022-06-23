// set default min date in form
var d = new Date();
d.setMonth(d.getMonth() - 1);
$("input[name='min-date']").val(d.toISOString().substr(0,10)); // to format desired by HTML

function setFormCallback(fcn) {
    $('#hand-filter-form').submit(function(event) {
        event.preventDefault();
        fcn();
    })
}