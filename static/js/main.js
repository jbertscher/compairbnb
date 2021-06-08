$( document ).ready(function() {

    var tabledata;
    var table; 

    // Parses the json and nested json objects. Keeps track of all the nested column names for table display later.
    function parse_json(tabledata) {
        tabledata_parsed = JSON.parse(tabledata);
        return tabledata_parsed
            // var bed_types = [];
            // var bed_type_cols = [];
            // // Loops through each listing, building a distinct array of bed types to serve as nested columns in the display table. End result
            // // is a an array of objects where each key is the column name and the value is the key within the final parsed json object that
            // // should be displayed for that column.
            // for(var i=0; i<tabledata_parsed.length; i++) {
            //     listing_i = JSON.parse(tabledata_parsed[i].num_bed_types)
            //     Object.keys(listing_i).forEach(bed_type => {
            //         if (!bed_types.includes(bed_type)) {
            //             bed_types.push(bed_type)
            //             bed_type_cols.push({'title': bed_type,'field': 'num_bed_types.' + bed_type});
            //         }
            //     });
            //     if(tabledata_parsed[i].num_bed_types == '{}') {
            //         tabledata_parsed[i].num_bed_types = null;
            //     };
            //     tabledata_parsed[i].num_bed_types = JSON.parse(tabledata_parsed[i].num_bed_types)
            // };

            // // Returns bed type columns and key for their respective values as well as parsed json object containing the data.
            // return(
            //     {
            //         'bed_type_cols': bed_type_cols,
            //         'tabledata_parsed': tabledata_parsed
            //     }
            // )
    }

    fetch('/api/' + trip_id)
        .then(function (response) {
            return response.json();
        }).then(function (json) {
            tabledata = json;

            console.log('Table data:');
            console.log(tabledata); 

            tabledata_parsed = JSON.parse(tabledata);
            // bed_type_cols = parsed_data['bed_type_cols'];
            // tabledata_parsed = parsed_data['tabledata_parsed'];

            //create Tabulator on DOM element with id "example-table"
            table = new Tabulator("#listings-table", {
                minHeight:220, // set height of table (in CSS or here), this enables the Virtual DOM and improves render speed dramatically (can be any valid css height value)
                data:tabledata_parsed, //assign data to table
                layout:"fitColumns", //fit columns to width of table (optional),
                columns:[ //Define Table Columns
                    {title:"Click image to visit URL", field:"image", formatter:"image", width:235, formatterParams:{
                        width:"225px",
                        height:"150px"
                    }, cellClick:function(e, cell) {
                        var win = window.open(cell.getRow().getData().url, '_blank');
                        win.focus();
                    }},
                    {title:"Title", field:"p3_summary_title", formatter:"textarea"},
                    {title:"Bedrooms", field:"bedroom_label"},
                    // Grouped columns
                    // {
                    //     title:"Beds", 
                    //     // columns: bed_type_cols
                    //     columns: {'queen_bed': 'num_bed_types.queen_bed'}
                    // },
                    {title:"Bathrooms", field:"bathroom_label"},
                    {title:"Guests", field:"guest_label"},
                    {title:"Location", field:"p3_summary_address", formatter:"textarea"}
                ]
                // autoColumns:true
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
        });

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
                        tabledata = parse_json(json)['tabledata_parsed'];
                        table.replaceData(tabledata);
                    });
            },
            complete:function(){
                console.log('should clear now 2');
                $('#urlInput').val('');
            }
        });
    });
});