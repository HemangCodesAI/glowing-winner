async function fetchJsonData(url) {
    try {
        const response = await fetch(url, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json'
            }
        });

        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
        }

        const data = await response.json();
        return data;
    } catch (error) {
        console.error('Error fetching data:', error);
        return null;
    }
}
exclude_ids = []
async function check_for_response(did, sobj) {
    const url = '/document/docdata/'+did;
    // console.log("HII");
    
    try {
        const data = await fetchJsonData(url);
        if (data) {
            // console.log('Data:', data);
            if(data.status!='active'){
                // console.log("NOT ACTIVE ", data.status);
                exclude_ids.push(did);
            }
            else{
                if(data.signature != ""){
                    // console.log("GOT SIGNATURE");
                    sobj.setAttribute('signature', data.signature);
                    sobj.classList.add("DOC"+data.signature);
                    exclude_ids.push(did);
                }
            }
        }
    } catch (error) {
        console.error('Error fetching data:', error);
    }
}

function checkforsignature(sobj){
    docs = document.getElementsByClassName("DOC" + sobj.getAttribute('signature'))[0];
    did = docs.id.slice(3, docs.id.length);
    if(!exclude_ids.includes(did)){
        check_for_response(did, sobj);
    }
}

const chatSocket = new WebSocket(
    'wss://'
    + 'multilipi-document-translation.centralindia.cloudapp.azure.com'
    + '/ws/progress/'
    + "roomName"
    + '/'
);

chatSocket.onmessage = function (e) {
    const data = JSON.parse(e.data);
    // console.log('recieved ', data);
    sobj = document.getElementsByClassName('progressdoc');
    for (i = 0; i < sobj.length; i++) {
        if (sobj[i].getAttribute('signature') != '') {
            // console.log(sobj[i].getAttribute('signature'), "  ==  ", data['message'][i]);
            docs = document.getElementsByClassName("DOC" + sobj[i].getAttribute('signature'))[0];
            // console.log("linear-gradient(to right, rgb(59, 130, 246) " + data['message'][i] + "%, rgb(255, 255, 255) " + (parseInt(data['message'][i])+1) + "%)")
            // docs.style.backgroundImage = "linear-gradient(to right, rgb(59, 130, 246) " + data['message'][i] + "%, rgb(255, 255, 255) " + (parseInt(data['message'][i]) + 1) + "%)"
            docs.getElementsByClassName('percentage_bar')[0].style.backgroundImage = "linear-gradient(to right, rgb(59, 130, 246) " + data['message'][i] + "%, rgb(255, 255, 255) " + (parseInt(data['message'][i]) + 1) + "%)"
            docs.getElementsByClassName("percentage")[0].innerText = parseInt(data['message'][i]) + "%";
            if (parseInt(data['message'][i]) >= 99.99) {
                // docs.parentElement.innerHTML = "<a href='/document/view/" + docs.id.slice(3, docs.id.length) + "/tgt' target='_blank'><img src='{% static 'svg/raphael_view.svg' %}'' alt=''></a></a><a href='/document/edit/" + docs.id.slice(3, docs.id.length) + `'><img src="{% static 'svg/flowbite_edit-solid.svg' %}" alt=''></a></a>`;
                done_code = `<div class="complete">
                                <a target="_blank" href="/document/view/${docs.id.slice(3, docs.id.length)}" class="header-buttons">
                                    <img src="https://multilipidashboard.blob.core.windows.net/static/svg/raphael_view.svg" alt=""></a>
                                
                                <a href="/document/edit/${docs.id.slice(3, docs.id.length)}" class="header-buttons">
                                    <img src="https://multilipidashboard.blob.core.windows.net/static/svg/flowbite_edit-solid.svg" alt=""></a>
                                
                            </div>`
                docs.parentElement.innerHTML = done_code;
            }
        }
    }
};

chatSocket.onclose = function (e) {
    console.error('Chat socket closed unexpectedly');
};

function extractData() {
    var allsignatures = [];

    sobj = document.getElementsByClassName('progressdoc');
    for (i = 0; i < sobj.length; i++) {
        if (sobj[i].getAttribute('signature') != '' && sobj[i].getAttribute('signature') != '0') {
            // console.log(sobj[i].getAttribute('signature'));
            allsignatures = allsignatures.concat(sobj[i].getAttribute('signature'));
        }
        else{
            checkforsignature(sobj[i]);
            // console.log(sobj[i], " ", sobj[i].getAttribute('signature'))
            docs = document.getElementsByClassName("DOC" + sobj[i].getAttribute('signature'))[0];
            did = docs.id.slice(3, docs.id.length);
            if(exclude_ids.includes(did)) {
                sobj[i].innerHTML = `<img src="https://multilipidashboard.blob.core.windows.net/static/svg/mdi_hide.svg" alt="">`;
            }
        }
    }
    if (allsignatures.length > 0) {
        // console.log("sending..")
        chatSocket.send(JSON.stringify({
            'signatures': allsignatures
        }));
    }
};

c = 0;
function refresgProgress() {
    if (c >= 200) {
        try{
            extractData();
        }
        catch (err) {
        }
        c = 0;
    }
    c += 1;
    window.requestAnimationFrame(refresgProgress);
}
window.requestAnimationFrame(refresgProgress);