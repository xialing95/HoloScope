/*
 * Main index page JavaScript
 * Add an ID to your main content element for easy targeting
 */ 

// update main content area when nav link is clicked
document.addEventListener('DOMContentLoaded', () => {
    const navLinks = document.querySelectorAll('.main-nav a');
    const mainContentArea = document.getElementById('main-content-area');

    if (!mainContentArea) return; // Exit if the content area isn't found

    navLinks.forEach(link => {
        link.addEventListener('click', (event) => {
            event.preventDefault(); // Stop the browser from navigating to a new page

            const url = link.getAttribute('href');

            // Use the fetch API to get content from the URL
            fetch(url)
                .then(response => {
                    if (!response.ok) {
                        throw new Error('Network response was not ok');
                    }
                    return response.text(); // Get the HTML content as text
                })
                .then(html => {
                    // Replace the content of the main area with the new HTML
                    mainContentArea.innerHTML = html;
                })
                .catch(error => {
                    console.error('Fetch error:', error);
                    mainContentArea.innerHTML = '<p style="color:red;">Failed to load content.</p>';
                });
        });
    });
});

// get camera and sensor status if connected


/*
 * Network-related JavaScript functions
 * JavaScript function to call the Flask route
 */
function enableHotspot() {
    // Show a "Connecting..." message while the script runs
    document.getElementById("network-status").innerText = "Hotspot Connecting...";

    fetch('/network/enable_hotspot')
        .then(response => response.json())
        .then(data => {
            // Update the status paragraph with the message from the server
            document.getElementById("network-status").innerText = data.status;
        })
        .catch(error => {
            // Handle any errors that occur during the fetch request
            console.error('Error:', error);
            document.getElementById("network-status").innerText = "Error enabling hotspot.";
        });
}       

function connectToWifi() {
    // Show a "Connecting..." message while the script runs
    document.getElementById("network-status").innerText = "WiFi Connecting...";

    // 1. Get the values from the input fields
    const ssid = document.getElementById('ssid').value;
    const password = document.getElementById('password').value;

    // 2. Prepare the data to be sent in the request body
    const data = {
        ssid: ssid,
        password: password
    };

    // 3. Send the POST request using the Fetch API
    fetch('/network/connect_to_wifi', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(data)
    })
        .then(response => response.json())
        .then(data => {
            // Update the status paragraph with the message from the server
            document.getElementById("network-status").innerText = data.status;
        })
        .catch(error => {
            // Handle any errors that occur during the fetch request
            console.error('Error:', error);
            document.getElementById("network-status").innerText = "Error enabling hotspot.";
        });
}

/*
 * Camera setting & preview related JavaScript functions
 * JavaScript function to call the Flask route
 */
document.addEventListener('submit', function(event) {
    // Check if the form being submitted is the one you want
    if (event.target && event.target.id === 'camera_config') {
        event.preventDefault(); 

        const form = event.target;
        const formData = new FormData(form);
        const statusDiv = document.getElementById('camera-status');

        fetch('/camera/camera_config', {
            method: 'POST',
            body: formData
        })
        .then(response => response.text())
        .then(text => {
            statusDiv.textContent = text;
        })
        .catch(error => {
            statusDiv.textContent = 'Failed to update controls: ' + error;
        });
    }
});



 
