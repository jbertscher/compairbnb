$( document ).ready(function() {

    var table;

    // Returns an array of the bed types and how they map to the values in the table data
    function extractBedTypesNums(tabledata) {
        var bedTypes = [];
        var bedTypeCols = [];

        // Loop through each listing
        for(var i=0; i<tabledata.length; i++) {
            listing_i = tabledata[i].num_bed_types
            // For each bed type in the BedType key, will add the bed type to the array if it doesn't exist
            Object.keys(listing_i).forEach(BedType => {
                if (!bedTypes.includes(BedType)) {
                    bedTypes.push(BedType)
                    bedTypeTormatted = BedType.replace('_', ' ').replace(/(^\w{1})|(\s+\w{1})/g, letter => letter.toUpperCase())
                    bedTypeCols.push({'title': bedTypeTormatted, 'field': 'num_bed_types.' + BedType});
                }
            });
        };

        // Returns bed type columns and key for their respective values
        return bedTypeCols;
    }

    // Returns an array of the voters and how they map to the values in the table data
    function extractVotes(tabledata) {
        var voters = [];
        var votersCols = [];

        // Loop through each listing
        for(var i=0; i<tabledata.length; i++) {
            listing_i = tabledata[i].votes;
            if (listing_i) { // Only execute below if there are votes for this property
                // For each voter in the voters key, will add the voter to the array if they don't exist
                Object.keys(listing_i).forEach(voter => {
                    if (!voters.includes(voter)) {
                        voters.push(voter);
                        votersCols.push({'title': voter,'field': 'votes.' + voter, 'formatter':'star', 'editor':'star', 'headerMenu':userHeaderMenu,
                        'editorParams':{ 
                            elementAttributes:{
                                maxlength:40
                            }
                        }});
                    }
                });
            }
        }

        // Returns bed type columns and key for their respective values
        return votersCols;
    }

    fetch('/api/' + trip_id)
        .then(function (response) {
            return response.json();
        }).then(function (json) {
            tabledata = json;
            table = loadTable(tabledata);
        });

    // Define column header to delete users from preferences parent column
    var userHeaderMenu = [
        {
            label:"Delete Column",
            action:function(e, column) {
                column.delete(column.getDefinition().title)
                fetch('/api/' + trip_id, {
                    headers: {
                        'Content-Type': 'application/json'
                    },

                    method: 'POST',

                    body: JSON.stringify({
                        "action": "delete_user",
                        "user": column.getDefinition().title
                    })
            
                }).then(function(response){
                    return response.text();
                }).then(function(text){
                    console.log('POST response: ');

                    // Should be 'OK' if everything was successful
                    console.log(text);
                });
            }
        }
    ]

    function loadTable(tabledata) {
        bedTypeCols = extractBedTypesNums(tabledata);
        votersCols = extractVotes(tabledata);

        //multiline text area
        var customTextareaFormatter = function(cell, formatterParams, onRendered){
            var el = cell.getElement();
            el.style.whiteSpace = "pre-wrap";
            el.style.overflow = "auto";
            el.style.maxHeight = "150px";
            return this.emptyToSpace(this.sanitizeHTML(cell.getValue()));
        };

        // This column contains x's that, when clicked, delete listings from the trip
        var listingDeletionCol = {
            field:'deleteListing', formatter:"buttonCross", width:40, hozAlign:"center", frozen:true, 
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
        }

        //define column header menu as column visibility toggle
        var headerMenu = function() {
            var menu = [];
            var columns = this.getColumns();

            for(let column of columns){
                console.log(column.getDefinition().field)
                if(!['image', 'deleteListing'].includes(column.getDefinition().field)){

                    //create checkbox element using font awesome icons
                    let icon = document.createElement("i");
                    icon.classList.add("fas");
                    icon.classList.add(column.isVisible() ? "fa-check-square" : "fa-square");

                    //build label
                    let label = document.createElement("span");
                    let title = document.createElement("span");

                    title.textContent = " " + column.getDefinition().title;

                    label.appendChild(icon);
                    label.appendChild(title);

                    //create menu item
                    menu.push({
                        label:label,
                        action:function(e){
                            //prevent menu closing
                            e.stopPropagation();

                            //toggle current column visibility
                            column.toggle();

                            //change menu item icon
                            if(column.isVisible()){
                                icon.classList.remove("fa-square");
                                icon.classList.add("fa-check-square");
                            }else{
                                icon.classList.remove("fa-check-square");
                                icon.classList.add("fa-square");
                            }
                        }
                    });
                }
            }

        return menu;
        };

        // Create Tabulator on DOM element with id "listings-table"
        var table = new Tabulator("#listings-table", {
            minHeight: 220, // Set height of table (in CSS or here), this enables the Virtual DOM and improves render speed dramatically (can be any valid css height value)
            data: tabledata,
            layout: "fitData",
            columns:[ // Define Table Columns
                listingDeletionCol,
                {title:"Click image to visit URL", field:"image", formatter:"image", 
                width:235, frozen: true, headerMenu:headerMenu, formatterParams:{
                    width:"225px",
                    height:"150px"
                }, cellClick:function(e, cell) { // So that clicking the image takes you to the listing URL
                    var win = window.open(cell.getRow().getData().url, '_blank');
                    win.focus();
                }},
                {title:"Title", field:"p3_summary_title", maxWidth: 200, formatter:"textarea", frozen:true},
                {title:"Bedrooms", field:"bedroom_label"},
                {title:"Beds", columns: bedTypeCols},   // Bed types grouped columns
                {title:"Bathrooms", field:"bathroom_label"},
                {title:"Guests", field:"guest_label"},
                {title:"Location", field:"p3_summary_address", maxWidth: 125, formatter:"textarea"},
                {title:"Rating", field:"localized_overall_rating"},
                {title:"Comments", field:"comments", formatter:customTextareaFormatter, width: 300, editor:"textarea", editorParams:{
                    whiteSpace: "pre-wrap",
                    overflow: "auto",
                    maxHeight: "150px"
                }},
                // {title:"Comments", field:"comments", formatter:customTextareaFormatter, editor:"textarea"}
                {title:"Preferences", columns: votersCols} // Voter grouped columns
            ],
            cellEdited: function(cell){
                var column;
                switch (cell.getColumn().getDefinition().title) {
                    case 'Comments':
                        column = 'comments';
                        value = cell.getValue()
                        break;
                     default:
                        column = 'preferences';
                        value = {
                            'user': cell.getColumn().getDefinition().title,
                            'points': cell.getValue()
                        };
                        break;
                }
                
                fetch('/api/' + trip_id, {
                    headers: {
                        'Content-Type': 'application/json'
                    },

                    method: 'POST',

                    body: JSON.stringify({
                        "action": "update_data",
                        "field": column,
                        "listing_id": cell.getRow().getData().listing_id,
                        "value": value
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
        return table;
    };

    // Add a column for a voter
    addVoterCol = function(table, voterName) { 
        table.addColumn({
            title: voterName, field:"stars", formatter:"star", editor:"star", headerMenu:userHeaderMenu, editorParams:{ 
                elementAttributes:{
                    maxlength:40
                }
            }
        });
    };
    
    // This gets executed when a new listing is submitted
    // It clears the text box and reloads the table
    $('#submitUrl').submit(function(e) {
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
                        table = loadTable(json);
                    });
            },
            complete:function(){
                $('#urlInput').val('');
            }
        });
    });

    // This gets executed when a new voter is submitted
    // It clears the text box and adds the voter to the table
    $('#addVoter').submit(function(e) {
        e.preventDefault();
        $.ajax({
            url: '/add_voter/' + trip_id,
            type: 'post',
            data:$('#addVoter').serialize(),
            success:function(){
                fetch('/api/' + trip_id)
                    .then(function (response) {
                        return response.json();
                    }).then(function (json) {
                        addVoterCol(table, $('#voterNameInput').val())
                        $('#voterNameInput').val('')
                    });
            }
        });
    });
});