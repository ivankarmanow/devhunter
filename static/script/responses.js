async function submit_form() {
    formNode = document.getElementById("respform");
    let data = new FormData(formNode);
    let response = await fetch('responses', {
        method: 'post',
        body: data
    })
    document.querySelector("html").innerHTML = await response.text();
}