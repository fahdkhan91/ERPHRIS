let currentTable = ""

async function loadData(name){

currentTable = name

fetchData()

}

async function fetchData(){

if(currentTable === "") return

let search = document.getElementById("search").value

let res = await fetch(`/api/${currentTable}?search=${search}`)

let data = await res.json()

renderTable(data)

}

function renderTable(data){

if(data.length === 0){

document.getElementById("table").innerHTML="No Data"

return

}

function downloadData(){

if(currentTable === ""){

alert("Please select a report first")

return

}

window.location = "/download/" + currentTable

}



let html="<table><tr>"

Object.keys(data[0]).forEach(col=>{
html+="<th>"+col+"</th>"
})

html+="</tr>"

data.forEach(row=>{

html+="<tr>"

Object.values(row).forEach(val=>{
html+="<td>"+val+"</td>"
})

html+="</tr>"

})

html+="</table>"

document.getElementById("table").innerHTML=html

}

function downloadExcel(){
alert("Button working")
}

function filterTable() {
    // 1. Get the search text
    let input = document.getElementById("search");
    let filter = input.value.toUpperCase();
    
    // 2. Get the table (assuming your loadData adds a <table> tag inside #table)
    let table = document.querySelector("#table table");
    if (!table) return; // Exit if table hasn't loaded yet

    let tr = table.getElementsByTagName("tr");

    // 3. Loop through all rows, hide those that don't match the search
    for (let i = 1; i < tr.length; i++) { // Start at 1 to skip <th>
        let rowVisible = false;
        let tds = tr[i].getElementsByTagName("td");
        
        // Loop through cells in the row to see if any match
        for (let j = 0; j < tds.length; j++) {
            if (tds[j].textContent.toUpperCase().indexOf(filter) > -1) {
                rowVisible = true;
                break; 
            }
        }
        tr[i].style.display = rowVisible ? "" : "none";
    }
}
