/* TODO:
 * get camera and sensor status if connected
 *
 * 
 */

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
                    <input type="checkbox" class="image-checkbox" data-filename="${image}">
                    <span class="filename">${image}</span>
                    <div>
                        <a href="file/download/${image}" download>Download</a>
                        <button onclick="deleteImage('${image}')" class="delete-button">Delete</button>
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

// Delete all images
async function deleteAllImages() {
    if (!confirm('Are you sure you want to delete ALL images? This action cannot be undone.')) {
        return;
    }

    try {
        const response = await fetch('file/delete_all', {
            method: 'POST',
        });
        const result = await response.json();
        if (result.success) {
            alert(result.message);
            updateImageList();
        } else {
            alert(result.message);
        }
    } catch (error) {
        console.error('Failed to delete all images:', error);
        alert('An error occurred while trying to delete all images.');
    }
}

// New Function: Download all images as a ZIP
function downloadAllImages() {
    window.location.href = 'file/download_all';
}

// Helper function to get filenames of selected checkboxes
function getSelectedFilenames() {
    const checkboxes = document.querySelectorAll('.image-checkbox:checked');
    return Array.from(checkboxes).map(checkbox => checkbox.dataset.filename);
}

// New Function: Delete selected images
async function deleteSelected() {
    const filenames = getSelectedFilenames();
    if (filenames.length === 0) {
        alert('Please select at least one image to delete.');
        return;
    }

    if (!confirm(`Are you sure you want to delete the selected ${filenames.length} image(s)?`)) {
        return;
    }

    try {
        const response = await fetch('file/delete_selected', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ filenames: filenames }),
        });
        const result = await response.json();
        if (result.success) {
            alert(result.message);
            updateImageList();
        } else {
            alert(result.message);
        }
    } catch (error) {
        console.error('Failed to delete selected images:', error);
        alert('An error occurred while trying to delete the selected images.');
    }
}

// New Function: Download selected images
async function downloadSelected() {
    const filenames = getSelectedFilenames();
    if (filenames.length === 0) {
        alert('Please select at least one image to download.');
        return;
    }

    try {
        const response = await fetch('file/download_selected', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ filenames: filenames }),
        });

        // The response will be a ZIP file, so we handle it as a blob
        if (response.ok) {
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.style.display = 'none';
            a.href = url;
            a.download = 'selected_images.zip';
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
        } else {
            const result = await response.json();
            alert(result.message);
        }
    } catch (error) {
        console.error('Failed to download selected images:', error);
        alert('An error occurred while trying to download the selected images.');
    }
}

/*
 * Timelapse setup timelapse JavaScript functions
 * JavaScript function to call the Flask route
 */
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
                messageBox.innerText = result.message;
            } else {
                messageBox.innerText = result.message;
            }
        })
        .catch(error => {
            const messageBox = document.getElementById('timelapse-message-box');
            messageBox.innerText = `Error starting time-lapse. Check console.`;
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
            const messageBox = document.getElementById('timelapse-message-box');
            messageBox.innerText = result.message;
        })
        .catch(error => console.error('Error:', error));
    };

    // Periodically check the time-lapse status
    setInterval(() => {
        fetch('/camera/timelapse_status')
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

/*
 * Dashboard JavaScript functions
 * JavaScript function to call the Flask route
 */
function refreshImage() {
    var img = document.getElementById('latest-image');
    // This is a common trick to force the browser to reload the image
    // by adding a unique timestamp to the URL.
    img.src = '/dashboard/latest_image?' + new Date().getTime();
}

/*
 * Sensor JavaScript functions
 * JavaScript function to call the Flask route
 */
// This function fetches data from the Flask API and updates the page
document.addEventListener('DOMContentLoaded', function() {
    // --- 1. Get references to HTML elements ---
    const loggingForm = document.getElementById('logging-form');
    const resetButton = document.getElementById('reset-button');
    const statusMessage = document.getElementById('status-message');
    const logOutput = document.getElementById('log-output');
    const sensor_status = document.getElementById('sensor-status');

    // --- 2. Function to update sensor data dynamically ---
    async function updateSensorData() {
        try {
            const response = await fetch('/sensors/sensor_data');
            
            // Check if the response is successful before proceeding
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            
            // If the server returns an error (e.g., sensor not initialized), display it
            if (data.status === 'error') {
                document.getElementById('temp').textContent = 'Error';
                document.getElementById('humidity').textContent = 'Error';
                document.getElementById('pressure').textContent = 'Error';
                statusMessage.textContent = data.message;
                statusMessage.style.color = 'red';
                return;
            }

            // Update the HTML elements with the new data
            document.getElementById('temp').textContent = data.temperature;
            document.getElementById('humidity').textContent = data.humidity;
            document.getElementById('pressure').textContent = data.pressure;

        } catch (error) {
            console.error('Failed to fetch sensor data:', error);
            document.getElementById('temp').textContent = 'Error';
            document.getElementById('humidity').textContent = 'Error';
            document.getElementById('pressure').textContent = 'Error';
        }
    }

    // --- 3. Event Listener for Form Submission (Start Log) ---
    if (loggingForm) {
        loggingForm.addEventListener('submit', async function(event) {
            event.preventDefault(); // Prevent the default form submission (page reload)
            
            const submitButton = loggingForm.querySelector('button[type="submit"]');
            
            submitButton.disabled = true;
            submitButton.innerText= 'Logging...';
            sensor_status.innterTest = 'Environmental Logging Started'

            // Get form data
            const formData = new FormData(loggingForm);
            
            fetch('/sensors/startEnvSensor', {
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
                // Update the innerHTML of the div with the formatted string inside <pre> tags
                statusMessage.innerHTML = `<p>Sensor Status:</p><pre>${data.status}</pre>`;
                logOutput.innerHTML = `<p>Sensor Message:</p><pre>${data.message}</pre>`
            })

            // try {
            //     // Send a POST request to the Flask endpoint
            //     const response = await fetch('/sensors/startEnvSensor', {
            //         method: 'POST',
            //         body: formData
            //     });

            //     if (!response.ok) {
            //         throw new Error(`HTTP error! status: ${response.status}`);
            //     }

            //     const result = await response.json();

            //     // Display the status message from the server
            //     statusMessage.innerText = result.message;

            // } catch (error) {
            //     console.error('Error:', error);
            //     statusMessage.innerText = `Error: ${error.message}`;
            // } finally {
            //     // Re-enable the button after the request is complete
            //     submitButton.disabled = false;
            //     submitButton.innerText = 'Start Log';
            // }
        });
    }

    // 4a. Delegation for I2C Reset Button ('reset-button')
    document.addEventListener('click', async function(event) {
        // Check if the clicked element has the ID 'reset-button'
        if (event.target.id === 'reset-button') {
            
            // event.preventDefault() isn't strictly needed here unless the button is 
            // inside a form, but it's good practice.
            
            // Provide immediate user feedback
            statusMessage.innerText = 'Resetting I2C bus...';
            statusMessage.style.color = 'orange';

            try {
                const response = await fetch('/sensors/reset_i2c', {
                    method: 'POST'
                });

                // Check for HTTP errors before reading the body
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                
                const result = await response.json();

                if (result.status === 'success') {
                    statusMessage.innerText = result.message;
                    statusMessage.style.color = 'green';
                    updateSensorData(); // Re-start data updates after a successful reset
                } else {
                    // Handle server-side errors (e.g., status is 'error')
                    statusMessage.innerText = result.message;
                    statusMessage.style.color = 'red';
                }
            } catch (error) {
                // Handle network errors or errors thrown above
                console.error('Error during I2C reset:', error);
                statusMessage.innerText = `I2C Reset Failed: ${error.message}.`;
                statusMessage.style.color = 'red';
            }
        }
    });

    // --- 5. Initial Call and Periodic Updates ---
    // Call the function once when the page loads
    updateSensorData();

    // Call the function every 5 seconds to get the latest data
    setInterval(updateSensorData, 5000); 
});