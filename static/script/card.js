async function submit_form(event) {
    event.preventDefault();
    formNode = document.getElementById("response_form");
    let data = new FormData(formNode);
    let response = await fetch('/make_response', {
        method: 'POST',
        body: data
    })
}