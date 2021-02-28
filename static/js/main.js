var tabledata;

fetch('/api')
    .then(function (response) {
        return response.json();
    }).then(function (json) {
        tabledata = json;

        console.log('Table data:');
        console.log(tabledata); 

        //create Tabulator on DOM element with id "example-table"
        var table = new Tabulator("#listings-table", {
            height:205, // set height of table (in CSS or here), this enables the Virtual DOM and improves render speed dramatically (can be any valid css height value)
            data:JSON.parse(tabledata), //assign data to table
            layout:"fitColumns", //fit columns to width of table (optional)
            autoColumns:true
        });

        table.addColumn({
            formatter:"buttonCross", width:40, hozAlign:"center", 
            cellClick:function(e, cell) {
                cell.getRow().delete();
                // POST
                fetch('/api', {

                    // Declare what type of data we're sending
                    headers: {
                    'Content-Type': 'application/json'
                    },

                    // Specify the method
                    method: 'POST',

                    // A JSON payload
                    body: JSON.stringify({
                        "action": "delete_listing",
                        "listing": cell.getRow().getData().id
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