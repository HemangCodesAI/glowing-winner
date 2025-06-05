
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}


function makeBlankPostRequest(url) {
    const csrftoken = getCookie('csrftoken'); // Replace 'csrftoken' with the name of your CSRF cookie if different

    fetch(url, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrftoken // Add the CSRF token to the headers
        },
        body: JSON.stringify({}) // Blank body
    })
        .then(response => response.json())
        .then(data => console.log('Success:', data))
        .catch(error => console.error('Error:', error));
}


function redirectToUrlWithPost(url, doconfirm=false, message="") {
    event.preventDefault();
    if(doconfirm){
        if(!confirm(message)){
            return;
        }
    }
    const csrftoken = getCookie('csrftoken'); // Extract the CSRF token from the cookie

    // Create a form element
    const form = document.createElement('form');
    form.method = 'POST';
    form.action = url;

    // Add the CSRF token as a hidden input field
    const csrfInput = document.createElement('input');
    csrfInput.type = 'hidden';
    csrfInput.name = 'csrfmiddlewaretoken';
    csrfInput.value = csrftoken;
    form.appendChild(csrfInput);

    // Optionally, add other hidden inputs for any data you want to send
    // Example:
    // const dataInput = document.createElement('input');
    // dataInput.type = 'hidden';
    // dataInput.name = 'key';
    // dataInput.value = 'value';
    // form.appendChild(dataInput);

    // Append the form to the body and submit it
    document.body.appendChild(form);
    form.submit();
}


