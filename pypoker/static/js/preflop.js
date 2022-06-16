const positions = ["BB", "SB", "D", "D-1", "D-2", "D-3", "D-4", "D-5", "D-6"];

// custom aggregator to show mean and count
var display = function() {
    return function() {
    return {
        count: 0,
        average: 0,
        push: function(e) {
        this.average = (this.count*this.average + e.vpip) / (this.count+1);
        this.count++;
        },
        value: function() {
        return this;
        },
        format: function(x) {
        vpip = (x.average * 100).toFixed(1);
        n = x.count;
        return vpip + " % (n = " + n + ")";
        }
    }
    }
}

function updatePivot(rawData) {
    var tblData = rawData.map(function(e) {
        var out = e;
        out.vpip = +e.vpip; // to numeric  
        return out;
    })

    $("#pivot").pivotUI(tblData,
        {rows: ["Seat"],
        vals: ["vpip"],
        derivedAttributes: {
            "Seat": (e) => positions[e["position"]],
            "StackBigBlinds": function(e) {
                return e["starting_stack"] / e["big_blind"]
            },
            "StackBin (BB)": $.pivotUtilities.derivers.bin("StackBigBlinds", 50),
            "BetsBefore": (e) => e["vp_before"]
        },
        aggregators: {"VPIP": display},
        sorters: {
            Seat: $.pivotUtilities.sortAs(positions) // otherwise sorts alphabetically
        },
        // hide intermediate or renamed attributes
        hiddenAttributes: ["StackBigBlinds", "starting_stack", "big_blind",
            "position", "time_stamp", "vp_before", "vpip", "num_players"]
    });
}    

function fetchData() {
    $("#pivot").hide();
    $("#error").hide();
    $("#loader").show();
    const data = $('#hand-filter-form').serialize();
    $.ajax({
        type: "POST",
        url: "/preflop/",
        data: data,
        success: function(response) {
            $("#loader").hide();
            $("#pivot").show();
            updatePivot(response);
        },
        error: function(xhr, error) {
            $("#loader").hide();
            $("#error").show();
            $("#error-text").text("Something went wrong.");
        }
    })
}

$(document).ready(function() {

    // set default min date in form
    var d = new Date();
    d.setMonth(d.getMonth() - 1);
    $("input[name='min-date']").val(d.toISOString().substr(0,10)); // to format desired by HTML

    $('#hand-filter-form').submit(function(event) {
        event.preventDefault();
        fetchData();
    })

    fetchData(); // do this immediately once the date in the form is set   
});