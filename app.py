from flask import Flask, request, render_template_string
import RPi.GPIO as GPIO
import sqlite3
import os
import time

app = Flask(__name__)

# Define the path to the database file
db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'students.db')

# HTML template for the web interface
html = '''
<!DOCTYPE html>
<html>
<head>
    <title>Motor Control</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body {
            text-align: center;
            background-color: #002554;
            color: rgb(0, 0, 0);
            margin-top: 250px;
            font-family: Arial, sans-serif;
        }
        .container {
            border: 5px solid white;
            padding: 20px;
            display: inline-block;
            background-color: #ffffff;
            border-radius: 20px;
            max-width: 90%;
            width: 400px;
        }
        h1 {
            font-size: 40px;
        }
        button {
            margin-top: 25px;
            background-color: #002554;
            color: #ffffff;
            padding: 10px 20px;
            border: none;
            border-radius: 5px;
            cursor: pointer;
        }
        button:hover {
            background-color: #e0e0e0;
        }
        input[type="text"] {
            padding: 10px;
            font-size: 16px;
            border-radius: 5px;
            border: 1px solid #002554;
            width: 80%;
        }
        img {
            max-width: 100%;
            height: auto;
        }

        @media (max-width: 600px) {
            body {
                margin-top: 50px;
            }
            h1 {
                font-size: 30px;
            }
            button {
                padding: 10px 15px;
            }
            input[type="text"] {
                width: 100%;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        
        <h1>Enter Student ID</h1>
        <form action="/check_id" method="post">
            <input type="text" name="student_id" maxlength="6" required> <br>
            <button type="submit">Open Door</button>
        </form>
        <p>{{ message }}</p>
    </div>
</body>
</html>
'''

def initialize_db():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY,
            student_id TEXT NOT NULL
        )
    """)
    cursor.execute("INSERT OR IGNORE INTO students (student_id) VALUES ('123456')")
    cursor.execute("INSERT OR IGNORE INTO students (student_id) VALUES ('654321')")
    conn.commit()
    conn.close()

# Function to check if the student ID is valid
def check_student_id(student_id):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM students WHERE student_id = ?", (student_id,))
    result = cursor.fetchone()
    conn.close()
    return result is not None

# Define GPIO pins for the L298N motor driver
IN1 = 18  # GPIO pin connected to IN1 on the L298N
IN2 = 17  # GPIO pin connected to IN2 on the L298N
IN3 = 27  # GPIO pin connected to IN3 on the L298N
IN4 = 22  # GPIO pin connected to IN4 on the L298N

# Set up the GPIO pins
GPIO.setmode(GPIO.BCM)
GPIO.setup(IN1, GPIO.OUT)
GPIO.setup(IN2, GPIO.OUT)
GPIO.setup(IN3, GPIO.OUT)
GPIO.setup(IN4, GPIO.OUT)

# Define the step sequence for the stepper motor
step_sequence = [
    [1,0,0,0],
    [1,1,0,0],
    [0,1,0,0],
    [0,1,1,0],
    [0,0,1,0],
    [0,0,1,1],
    [0,0,0,1],
    [1,0,0,1]
]

# Function to perform a single step
def step_motor(step):
    GPIO.output(IN1, step[1])
    GPIO.output(IN2, step[0])
    GPIO.output(IN3, step[2])
    GPIO.output(IN4, step[3])

# Function to rotate the stepper motor
def rotate_motor(steps, delay):
    for _ in range(steps):
        for step in step_sequence:
            step_motor(step)
            time.sleep(delay)

@app.route('/')
def index():
    return render_template_string(html, message="")

@app.route('/check_id', methods=['POST'])
def check_id():
    student_id = request.form['student_id']
    if check_student_id(student_id):
        # Rotate the motor for one revolution
        steps_per_revolution = 200
        step_delay = 0.01
        rotate_motor(steps_per_revolution, step_delay)
        return render_template_string(html, message="Motor turned on and tested!")
    else:
        return render_template_string(html, message="Invalid student ID!")

if __name__ == '__main__':
    initialize_db()  # Initialize the database and table
    try:
        app.run(host='0.0.0.0', port=5000)
    except KeyboardInterrupt:
        GPIO.cleanup()
