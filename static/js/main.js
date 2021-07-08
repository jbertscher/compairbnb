$( document ).ready(function() {

    var table;

    // Returns an array of the bed types and how they map to the values in the table data
    function extractBedTypesNums(tabledata) {
        var bedTypes = [];
        var bedTypeCols = [];

        // Loop through each listing
        for(var i=0; i<tabledata.length; i++) {
            listing_i = tabledata[i].num_bed_types
            // For each bed type in the bed_type key, will add the bed type to the array if it doesn't exist
            Object.keys(listing_i).forEach(bed_type => {
                if (!bedTypes.includes(bed_type)) {
                    bedTypes.push(bed_type)
                    bedTypeCols.push({'title': bed_type,'field': 'num_bed_types.' + bed_type});
                }
            });
        };

        // Returns bed type columns and key for their respective values
        return bedTypeCols
    }

    fetch('/api/' + trip_id)
        .then(function (response) {
            return response.json();
        }).then(function (json) {
            tabledata = json;
            table = loadTable(tabledata);
            var voterName = 'Jonathan'
            addVoterCol(table, voterName);
        });

    function loadTable(tabledata) {
        console.log('Table data:');
        console.log(tabledata); 

        bedTypeCols = extractBedTypesNums(tabledata);

        //multiline text area
        var customTextareaFormatter = function(cell, formatterParams, onRendered){
            var el = cell.getElement();
            el.style.whiteSpace = "pre-wrap";
            el.style.overflow = "auto";
            el.style.maxHeight = "150px";
            return this.emptyToSpace(this.sanitizeHTML(cell.getValue()));
        };
        
        //multiline text editor
        var customTextareaEditor = function(cell, formatterParams, onRendered){
            var editor = document.createElement("input")
            editor.style.whiteSpace = "pre-wrap";
            editor.style.overflow = "auto";
            editor.style.maxHeight = "150px";
            return editor;
        };

        // This column contains x's that, when clicked, delete listings from the trip
        var listingDeletionCol = {
            formatter:"buttonCross", width:40, hozAlign:"center", frozen:true, 
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

        //define row context menu contents
        var rowMenu = [
            {
                label:"<i class='fas fa-user'></i> Change Name",
                action:function(e, row){
                    row.update({name:"Steve Bobberson"});
                }
            },
            {
                label:"<i class='fas fa-check-square'></i> Select Row",
                action:function(e, row){
                    row.select();
                }
            },
            {
                separator:true,
            },
            {
                label:"Admin Functions",
                menu:[
                    {
                        label:"<i class='fas fa-trash'></i> Delete Row",
                        action:function(e, row){
                            row.delete();
                        }
                    },
                    {
                        label:"<i class='fas fa-ban'></i> Disabled Option",
                        disabled:true,
                    },
                ]
            }
        ]

        //define column header menu as column visibility toggle
        var headerMenu = function(){
            var menu = [];
            var columns = this.getColumns();

            for(let column of columns){

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

        return menu;
        };

        // Create Tabulator on DOM element with id "example-table"
        var table = new Tabulator("#listings-table", {
            minHeight:220, // Set height of table (in CSS or here), this enables the Virtual DOM and improves render speed dramatically (can be any valid css height value)
            data:tabledata, // Assign data to table
            layout:"fitData", // "fitColumns", // Fit columns to width of table (optional),
            rowContextMenu: rowMenu, //add context menu to rows,
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
                // Grouped columns
                {
                    title:"Beds", 
                    columns: bedTypeCols
                },
                {title:"Bathrooms", field:"bathroom_label"},
                {title:"Guests", field:"guest_label"},
                {title:"Location", field:"p3_summary_address", maxWidth: 125, formatter:"textarea"},
                {title:"Rating", field:"localized_overall_rating"},
                // {title:"Comments", field:"comments", formatter:customTextareaFormatter, editor:"textarea", editorParams:{
                //     whiteSpace: "pre-wrap",
                //     overflow: "auto",
                //     maxHeight: "150px"
                // }}customTextareaEditor
                // {title:"Comments", field:"comments", formatter:customTextareaFormatter, editor:"textarea"}
                {title:"Comments", field:"comments", formatter:customTextareaFormatter, editor:customTextareaEditor}
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
        return table;
    };

    // Add a column for a voter
    addVoterCol = function(table, voterName){ 
        table.addColumn({
            title: voterName, field:"stars", formatter:"star", editor:"star",editorParams:{ 
                elementAttributes:{
                    maxlength:40
                }
            }
        });
    };

    // document.body.addEventListener('click', function(){
    //     // console.log(table)
    //     addVoterCol(table);
    // }, true); 
    
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
                        table = loadTable(json);
                    });
            },
            complete:function(){
                $('#urlInput').val('');
            }
        });
    });

    // This gets executed when a new voter is submitted
    // It clears the text box and reloads the table
    $('#submitVoterName').submit(function(e){
        e.preventDefault();
        $.ajax({
            url: '/submit_voter/' + trip_id,
            type: 'post',
            data:$('#submitVoterName').serialize(),
            success:function(){
                fetch('/api/' + trip_id)
                    .then(function (response) {
                        return response.json();
                    }).then(function (json) {
                        table = loadTable(json);
                    });
            },
            complete:function(){
                $('#voterNameInput').val('');
            }
        });
    });
});