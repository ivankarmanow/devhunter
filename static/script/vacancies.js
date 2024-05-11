async function submit_form() {
    formNode = document.getElementById("vacform");
    let data = new FormData(formNode);
    let response = await fetch('vacancies', {
        method: 'POST',
        body: data
    })
    document.querySelector("html").innerHTML = await response.text();
}