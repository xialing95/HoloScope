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
    const previewImage = document.getElementById('camera-preview');
    const statusDiv = document.getElementById('camera-message-box');
    const form = event.target; // Get the form element that triggered the event

    // Check if the form being submitted is the one you want
    if (form && form.id === 'camera_init_config') {
        event.preventDefault(); 
        
        //  Create a FormData object from the form
        const formData = new FormData(form);

        // Use the fetch API to send a POST request
        fetch('/camera/init_config', {
            method: 'POST',
            body: formData,
        })
        .then(response => {
            // Check if the response is okay before parsing
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json(); 
        })
        .then(data => {
            // Update the image's source using the URL from the JSON
            previewImage.src = data.image_url;

            // Access the camera_settings object
            const cameraSettings = data.camera_settings;
            // Convert the JavaScript object back to a formatted JSON string
            const formattedSettings = JSON.stringify(cameraSettings, null, 4);
            // Update the innerHTML of the div with the formatted string inside <pre> tags
            statusDiv.innerHTML = `<p>Camera Settings:</p><pre>${formattedSettings}</pre>`;

        })
        .catch(error => {
            console.error('Error:', error);
            const statusDiv = document.getElementById('status-update');
            statusDiv.innerText = `<p style="color:red;">Error updating content.</p>`;
        });
    }
});


/*
 * File download & preview related JavaScript functions
 * JavaScript function to call the Flask route
 */

// Function to update the image list dynamically
async function updateImageList() {
    try {
        const response = await fetch('file/images');
        const images = await response.json();
        const imageList = document.getElementById('image-list');
        imageList.innerHTML = ''; // Clear the current list

        if (images.length === 0) {
            const listItem = document.createElement('li');
            listItem.textContent = 'No images found.';
            imageList.appendChild(listItem);
        } else {
            images.forEach(image => {
                const listItem = document.createElement('li');
                listItem.innerHTML = `
                    ${image}
                    <div>
                        <a href="file/download/${image}" download>Download</a>
                        <button onclick="deleteImage('${image}')">Delete</button>
                    </div>
                `;
                imageList.appendChild(listItem);
            });
        }
    } catch (error) {
        console.error('Failed to update image list:', error);
    }
}

async function deleteImage(filename) {
    if (!confirm(`Are you sure you want to delete ${filename}?`)) {
        return;
    }

    try {
        const response = await fetch(`file/delete/${filename}`, {
            method: 'POST', // Use POST for deletion requests
        });
        const result = await response.json();
        if (result.success) {
            alert(result.message);
            updateImageList(); // Refresh the list after successful deletion
        } else {
            alert(result.message);
        }
    } catch (error) {
        console.error('Failed to delete image:', error);
        alert('An error occurred while trying to delete the image.');
    }
}

/*
 * Dashboard setup timelapse JavaScript functions
 * JavaScript function to call the Flask route
 */
// document.getElementById('timelapse-form').addEventListener('submit', function(event) {
//     // Prevent the default form submission (page reload)
//     event.preventDefault();

//     // Get the form element
//     const form = event.target;
    
//     // Create a FormData object to easily collect all form data
//     const formData = new FormData(form);

//     // Get the status message element
//     const statusElement = document.getElementById('timelapse-status');

//     // Display a loading message
//     statusElement.innerHTML = '<h4>Starting time lapse...</h4>';

//     // Send the form data to the server
//     fetch('/dashboard/start', {
//         method: 'POST',
//         body: formData,
//     })
//     .then(response => {
//         // Check if the response is valid before parsing
//         if (!response.ok) {
//             throw new Error('Network response was not ok');
//         }
//         return response.json();
//     })
//     .then(data => {
//         // Update the status with the server's response
//         statusElement.innerHTML = `<h4>Execution time (seconds): ${data.elapseTime}, Total Number Photos: ${data.numphotos}</h4>`;
//     })
//     .catch(error => {
//         // Handle any errors that occurred during the fetch
//         console.error('Error:', error);
//         statusElement.innerHTML = '<h4 style="color:red;">Failed to start time lapse.</h4>';
//     });
// });

document.addEventListener('DOMContentLoaded', (event) => {
    // New functions to start and stop the time-lapse
    window.startTimelapse = function() {
        const filename = document.getElementById('filename').value;
        const duration = document.getElementById('duration').value;
        const interval = document.getElementById('interval').value;
        
        const data = {
            filename: filename,
            duration: duration,
            interval: interval
        };
        
        fetch('/camera/start_timelapse', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data),
        })
        .then(response => response.json())
        .then(result => {
            const messageBox = document.getElementById('timelapse-message-box');
            if (result.status === 'error') {
                messageBox.innerText = `<p>${result.message}</p>`;
            } else {
                messageBox.innerText = `<p>${result.message}</p>`;
            }
        })
        .catch(error => {
            const messageBox = document.getElementById('timelapse-message-box');
            messageBox.innerText = `<p>Error starting time-lapse. Check console.</p>`;
            console.error('Error:', error);
        });
    };

    window.stopTimelapse = function() {
        fetch('/camera/stop_timelapse', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        })
        .then(response => response.json())
        .then(result => {
            const messageBox = document.getElementById('message-box');
            messageBox.innerText = `<p>${result.message}</p>`;
        })
        .catch(error => console.error('Error:', error));
    };

    // Periodically check the time-lapse status
    setInterval(() => {
        fetch('/dashboard/timelapse_status')
            .then(response => response.json())
            .then(data => {
                const messageBox = document.getElementById('timelapse-status');
                const photoStatus = document.getElementById('photo-status');

                if (data.status === 'Running') {
                    if (photoStatus) {
                        photoStatus.textContent = `${data.current_photo}/${data.total_photos}`;
                    }
                    if (messageBox) {
                        messageBox.innerHTML = `<p>Time-lapse is running...</p>`;
                    }
                    if (progressContainer) {
                        progressContainer.style.display = 'block';
                    }
                } else {
                    if (photoStatus) {
                        photoStatus.textContent = `0/0`;
                    }
                    if (data.status !== 'Idle' && messageBox) {
                        messageBox.innerHTML = `<p>Time-lapse ended with status: ${data.status}</p>`;
                    }
                }
            })
            .catch(error => console.error('Error fetching status:', error));
    }, 3000); // Poll every 3 seconds
});