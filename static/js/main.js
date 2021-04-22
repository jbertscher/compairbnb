$( document ).ready(function() {

    var tabledata;
    var table; 

    fetch('/api/' + trip_id)
        .then(function (response) {
            return response.json();
        }).then(function (json) {
            tabledata = json;

            console.log('Table data:');
            console.log(tabledata); 

            tabledata_parsed = JSON.parse(tabledata);
            var bed_types = [];
            var bed_type_cols = [];
            for(var i=0; i<tabledata_parsed.length; i++) {
                Object.keys(JSON.parse(tabledata_parsed[i].num_bed_types)).forEach(bed_type => {
                    if (!bed_types.includes(bed_type)) {
                        bed_types.push(bed_type)
                        bed_type_cols.push({'title': bed_type,'field': 'num_bed_types.' + bed_type});
                    }
                });
                if(tabledata_parsed[i].num_bed_types == '{}') {
                    tabledata_parsed[i].num_bed_types = null;
                };
                tabledata_parsed[i].num_bed_types = JSON.parse(tabledata_parsed[i].num_bed_types)
            };

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
                    {
                        title:"Beds", 
                        columns: bed_type_cols
                    },
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
            url: '/submit_url/{{ trip_id }}',
            type: 'post',
            data:$('#submitUrl').serialize(),
            success:function(){
                console.log('this worked')
                fetch('/api/' + trip_id)
                    .then(function (response) {
                        return response.json();
                    }).then(function (json) {
                        tabledata = json;
                        table.replaceData(tabledata);
                    });
            }
        });
    });
});