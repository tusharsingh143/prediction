from flask import Flask, render_template, request, jsonify, redirect, session
import pyodbc
import pickle
import traceback

app = Flask(__name__, template_folder='templates')
app.secret_key = 'your_secret_key'  # Add a secret key for session management

# Load the RandomForest model from the pickle file
try:
    with open('models/RandomForest.pkl', 'rb') as f:
        RF = pickle.load(f)
except FileNotFoundError:
    print("Error: Model file not found.")
    exit(1)
except Exception as e:
    print("Error loading model:", e)
    exit(1)

# Connect to SQL Server
def get_db_connection():
    try:
        conn = pyodbc.connect('DRIVER={SQL Server};SERVER=LAPTOP-1CLB812F\SQLEXPRESS;DATABASE=CropDb')
        return conn, conn.cursor()
    except pyodbc.Error as e:
        print("Database connection error:", e)
        raise

# Route for handling prediction from API request
@app.route('/testing', methods=['POST'])
def testing():
    try:
        conn, cursor = get_db_connection()

        data = request.form
        input_data = [float(data.get(key, 0.0)) for key in ['N', 'P', 'K', 'temperature', 'humidity', 'ph', 'rainfall']]
        city = data.get('city', '')
        
        # Make prediction using the RF model
        prediction = RF.predict([input_data])[0]

        # Insert data into the database
        cursor.execute("INSERT INTO input_data (N, P, K, temperature, humidity, ph, rainfall, city, prediction) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", 
               (input_data[0], input_data[1], input_data[2], input_data[3], input_data[4], input_data[5], input_data[6], city, prediction))
        conn.commit()

        return jsonify({'prediction': str(prediction), 'input_data': input_data})
    except Exception as e:
        traceback.print_exc()  # Print exception traceback
        return jsonify({'error': "An error occurred while processing your request."}), 500
    finally:
        conn.close()

# Route for serving the HTML file
@app.route('/')
def index():
    return render_template('index.html')


# Route for handling admin login
@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        if email == 'admin@gmail.com' and password == 'Admin@123':
            # Admin authentication successful
            session['admin_logged_in'] = True
            return redirect('/admin/dashboard')  # Redirect to admin dashboard
        else:
            return "Invalid email or password. Please try again."
    else:
        return render_template('admin_login.html')

# Route for admin dashboard
@app.route('/admin/dashboard')
def admin_dashboard():
    # Check if admin is logged in
    if 'admin_logged_in' in session and session['admin_logged_in']:
        try:
            conn, cursor = get_db_connection()
            cursor.execute("SELECT * FROM input_data")
            data = cursor.fetchall()
            return render_template('admin_dashboard.html', data=data)
        except Exception as e:
            traceback.print_exc()  # Print exception traceback
            return jsonify({'error': "An error occurred while processing your request."}), 500
        finally:
            conn.close()
    else:
        return redirect('/admin_login')  # Redirect to admin login if not logged in

# if __name__ == "__main__":
#     app.run(debug=False)
