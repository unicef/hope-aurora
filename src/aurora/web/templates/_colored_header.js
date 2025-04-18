document.addEventListener("DOMContentLoaded", function (event) {
        const url = window.location.href;
        let color = '';
        let text = '';
        if (window.location.hostname === 'localhost') {
            color = '#FF6600';
            text = 'localhost';
        } else if (url.includes('-trn')) {
            color = '#BF360C';
            text = 'training';
        } else if (url.includes('-stg')) {
            color = '#673AB7';
            text = 'staging';
        } else if (url.includes('-dev')) {
            color = '#00796B';
            text = 'test';
        } else {
            color = '#00ADEF';
        }
        var head = document.getElementById("header");
        if (head){
            head.style.backgroundColor = color;
            var element = document.createElement("div");
            element.appendChild(document.createTextNode(text));
            document.getElementById('header').appendChild(element);
        }
    });
