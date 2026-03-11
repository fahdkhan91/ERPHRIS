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