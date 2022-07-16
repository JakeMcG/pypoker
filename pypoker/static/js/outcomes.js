function fetchData() {
    const data = $("#hand-filter-form").serialize();
    $.ajax({
        type: "POST",
        url: "/outcomes/",
        data: data,
        success: function(response) {
            showResults(response)
        },
        error: (xhr, error) => console.log("error")
    });
}

function showResults(results) {
    $("#outcomes-result").html("Filtered seats: " + results["totalCount"]
        + "<br>Eligible for action: " + results["eligibleCount"]
        + "<br>Took action: " + results["matchedCount"] + " (" + (100*results["matchedCount"]/results["eligibleCount"]).toFixed(1) + "% of eligible)"
        + "<br>Wins: " + results["matchedWins"] + " (" + (100*results["matchedWins"]/results["matchedCount"]).toFixed(1) + "% of actions taken)"
        + "<br>Average Profit: " + (results["matchedProfitBB"]/results["matchedCount"]).toFixed(1) + " BB"
    )

}

$(document).ready(function() {

    setFormCallback(fetchData);
})