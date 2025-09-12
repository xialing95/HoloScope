from flask import Blueprint, render_template, request, redirect, url_for


main_bp = Blueprint('main', __name__)

# This route handles the main page and form submissions.
@main_bp.route('/', methods=['GET', 'POST'])
def index():
    """
    Renders the main page on GET requests.
    Processes the form data on POST requests.
    """
    if request.method == 'POST':
        # Get data from the submitted form.
        connection_type = request.form.get('connection_type')
        ssid = request.form.get('ssid')
        password = request.form.get('password')

        # In a real-world application, you would use this data
        # to connect to a network or set up a hotspot.
        print(f"Received configuration for: {connection_type}")
        print(f"SSID: {ssid}")
        print(f"Password: {password}")

        # Redirect the user to a success page after submission.
        return redirect(url_for('main.success'))

    # Render the main HTML template for GET requests.
    return render_template('index.html')

@main_bp.route('/success')
def success():
    """
    A simple route to display a success message after form submission.
    """
    return "<h1>Configuration submitted successfully!</h1>"
