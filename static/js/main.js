$( document ).ready(function() {

    // Returns an array of the bed types and how they map to the values in the table data
    function extract_bed_types_nums(tabledata) {
        var bed_types = [];
        var bed_type_cols = [];
        // Loop through each listing
        for(var i=0; i<tabledata.length; i++) {
            listing_i = tabledata[i].num_bed_types
            // For each bed type in the bed_type key, will add the bed type to the array if it doesn't exist
            Object.keys(listing_i).forEach(bed_type => {
                if (!bed_types.includes(bed_type)) {
                    bed_types.push(bed_type)
                    bed_type_cols.push({'title': bed_type,'field': 'num_bed_types.' + bed_type});
                }
            });
        };

        // Returns bed type columns and key for their respective values
        return bed_type_cols
    }

    fetch('/api/' + trip_id)
        .then(function (response) {
            return response.json();
        }).then(function (json) {
            tabledata = json;
            load_table(tabledata)
        });

    function load_table(tabledata) {
        console.log('Table data:');
        console.log(tabledata); 

        bed_type_cols = extract_bed_types_nums(tabledata);

        // Create Tabulator on DOM element with id "example-table"
        table = new Tabulator("#listings-table", {
            minHeight:220, // Set height of table (in CSS or here), this enables the Virtual DOM and improves render speed dramatically (can be any valid css height value)
            data:tabledata, // Assign data to table
            layout:"fitColumns", // Fit columns to width of table (optional),
            columns:[ // Define Table Columns
                {title:"Click image to visit URL", field:"image", formatter:"image", width:235, formatterParams:{
                    width:"225px",
                    height:"150px"
                }, cellClick:function(e, cell) { // So that clicking the image takes you to the listing URL
                    var win = window.open(cell.getRow().getData().url, '_blank');
                    win.focus();
                }},
                {title:"Title", field:"p3_summary_title", formatter:"textarea"},
                {title:"Bedrooms", field:"bedroom_label"},
                // Grouped columns
                {
                    title:"Beds", 
                    columns: bed_type_cols
                },
                {title:"Bathrooms", field:"bathroom_label"},
                {title:"Guests", field:"guest_label"},
                {title:"Location", field:"p3_summary_address", formatter:"textarea"},
                {title:"Rating", field:"localized_overall_rating"},
                {title:"Comments", field:"comments", editor:"textarea"}
            ],
            cellEdited: function(cell){
                cell_value = cell.getValue()
                fetch('/api/' + trip_id, {

                    headers: {
                        'Content-Type': 'application/json'
                    },

                    method: 'POST',

                    body: JSON.stringify({
                        "action": "add_comments",
                        "listing_id": cell.getRow().getData().listing_id,
                        "comments": cell_value
                    })

                }).then(function (response) {
                    return response.text();
                }).then(function(text){

                    console.log('POST response: ');

                    // Should be 'OK' if everything was successful
                    console.log(text);
                })
            }
        });

        table.addColumn({
            formatter:"buttonCross", width:40, hozAlign:"center", 
            cellClick:function(e, cell) {
                cell.getRow().delete();
                // POST
                fetch('/api/' + trip_id, {

                    // Declare what type of data we're sending
                    headers: {
                        'Content-Type': 'application/json'
                    },

                    // Specify the method
                    method: 'POST',

                    // A JSON payload
                    body: JSON.stringify({
                        "action": "delete_listing",
                        "listing_id": cell.getRow().getData().listing_id
                    })
                }).then(function (response) { // At this point, Flask has printed our JSON
                    return response.text();
                }).then(function (text) {

                    console.log('POST response: ');

                    // Should be 'OK' if everything was successful
                    console.log(text);
                });
            }
        }, true, "Delete");
    };
    
    // This gets executed when a new listing is submitted
    // It clears the text box and reloads the table
    $('#submitUrl').submit(function(e){
        e.preventDefault();
        $.ajax({
            url: '/submit_url/' + trip_id,
            type: 'post',
            data:$('#submitUrl').serialize(),
            success:function(){
                fetch('/api/' + trip_id)
                    .then(function (response) {
                        return response.json();
                    }).then(function (json) {
                        load_table(json);
                    });
            },
            complete:function(){
                $('#urlInput').val('');
            }
        });
    });
});