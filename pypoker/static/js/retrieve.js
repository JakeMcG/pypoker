$(document).ready(function() {    
    // $("#import_link").on("click", function BcpImport() {
    //     $("#auth_modal").modal({
    //       keyboard: false, //remove option to close with keyboard
    //       show: true //Display loader!
    //     });
    // });

    $("#bcp_signin").on("submit", function(e) {
        e.preventDefault();
        $.ajax({
            type: "POST",
            url: "/retrieve/",
            data: $(this).serialize(),
            success: function(response) {
                console.log("Import Callback");
                console.log(response);
                $("#loader").modal("hide");
                if (!response["error"]) {
                    $("#result_title").text("Success!");
                    var resultTxt = "Imported " + response["newHands"] + " new hands from BCP.";
                    if (response["newHands"] > 0){
                        resultTxt += " Earliest: " + response["earliestHandTime"] + ", Latest: " + response["latestHandTime"]
                    }
                } else {
                    $("#result_title").text("Something went wrong.");
                    var resultTxt = response["errorText"];
                }                
                $("#result_text").text(resultTxt);
                $('#result_modal').modal("show");
            },
            error: function(xhr, error) {
                console.log("Unknown Error");
                $("#loader").modal("hide");
                $("#result_title").text("Something went wrong.");
                $("#result_text").text("Error Status " + xhr.status);
                $("#result_modal").modal("show");
            }
        });
        console.log("Passed ajax");
        $("#auth_modal").modal("hide");
        $("#loader").modal({
            backdrop: "static",
            keyboard: false, //remove option to close with keyboard
            show: true //Display loader!
        })
    });
});