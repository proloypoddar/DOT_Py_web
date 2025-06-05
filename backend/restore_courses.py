import os
import sys

# Add the project root to sys.path to enable package imports
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, os.pardir))
if project_root not in sys.path:
    sys.path.append(project_root)

from pymongo import MongoClient
from datetime import datetime
from backend.config import Config
import logging
from backend.models import get_database
from pymongo.errors import ConnectionFailure

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def connect_to_db():
    """Connect to MongoDB and return database instance"""
    try:
        client = MongoClient(Config.MONGO_URI)
        db = client[Config.MONGO_DB_NAME]
        logger.info("Successfully connected to MongoDB")
        return db
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {str(e)}")
        return None

def add_course(db, course_data):
    """Add a single course to the database"""
    try:
        # Add timestamps
        course_data['created_at'] = datetime.utcnow()
        course_data['updated_at'] = datetime.utcnow()
        
        # Ensure price is float
        if 'price' in course_data:
            course_data['price'] = float(course_data['price'])
        
        # Insert course
        result = db.courses.insert_one(course_data)
        logger.info(f"Successfully added course: {course_data['title']} (ID: {result.inserted_id})")
        return True, str(result.inserted_id)
    except Exception as e:
        logger.error(f"Failed to add course {course_data.get('title', 'Unknown')}: {str(e)}")
        return False, str(e)

def add_courses_to_db():
    """Adds the predefined list of courses to the database."""
    try:
        db = get_database()
        # Drop the courses collection if it exists
        if 'courses' in db.list_collection_names():
            db.drop_collection('courses')
            print("Existing courses collection dropped.")

        # Insert courses
        result = db.courses.insert_many(courses_list)
        print(f"Added {len(result.inserted_ids)} courses successfully.")

    except ConnectionFailure as e:
        print(f"Failed to connect to MongoDB: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")

# Comprehensive list of courses with details
courses_list = [
    {
        "title": "Python Programming Level 1",
        "short_description": "Start your coding journey with the fundamentals of Python programming.",
        "description": "This course is designed for absolute beginners. You will learn the basics of Python programming, including variables, data types, operators, control flow (if-else, loops), and functions. We focus on building a strong foundation for your programming career.",
        "duration": "4 Months",
        "level": "Beginner",
        "category": "python",
        "syllabus": [
            {"title": "Module 1: Introduction to Python", "topics": ["Setting up Python environment", "Variables and Data Types", "Basic Input and Output", "Operators"]},
            {"title": "Module 2: Control Flow", "topics": ["Conditional Statements (if, elif, else)", "Loops (for, while)", "Break and Continue"]},
            {"title": "Module 3: Data Structures - Part 1", "topics": ["Lists", "Tuples", "Working with Sequences"]},
            {"title": "Module 4: Data Structures - Part 2", "topics": ["Dictionaries", "Sets", "Introduction to Strings"]},
            {"title": "Module 5: Functions and Modules", "topics": ["Defining Functions", "Function Arguments", "Scope and Lifetime of Variables", "Importing Modules"]},
            {"title": "Module 6: Basic Projects", "topics": ["Building simple command-line applications"]},
            # Add more modules to cover 4 months (approx. 16 weeks / 8 quizzes)
        ],
        "status": "Active",
        "features": [
            "4-month duration",
            "2 classes per week",
            "Quizzes every 2 weeks",
            "Project Showcase in the last class",
            "Certificate upon completion",
            "Ideal for absolute beginners"
        ]
    },
    {
        "title": "Python Programming Level 2",
        "short_description": "Intermediate Python concepts including OOP and File I/O.",
        "description": "Building upon Level 1, this course dives into Object-Oriented Programming (OOP) principles in Python. You will learn about classes, objects, inheritance, and polymorphism. The course also covers comprehensive file handling techniques, working with different file formats, and error handling.",
        "duration": "4 Months",
        "level": "Intermediate",
        "category": "python",
        "syllabus": [
            {"title": "Module 1: Object-Oriented Programming Basics", "topics": ["Classes and Objects", "Instance and Class Variables", "Methods"]},
            {"title": "Module 2: OOP Principles", "topics": ["Inheritance", "Polymorphism", "Encapsulation"]},
            {"title": "Module 3: File Handling", "topics": ["Reading and Writing Files", "Working with Different File Modes"]},
            {"title": "Module 4: Working with File Formats", "topics": ["CSV Files", "JSON Data"]},
            {"title": "Module 5: Error Handling and Exceptions", "topics": ["Try, Except, Finally", "Custom Exceptions"]},
            {"title": "Module 6: Intermediate Projects", "topics": ["Building applications involving file processing and OOP"]},
            # Add more modules to cover 4 months
        ],
        "status": "Active",
        "features": [
            "4-month duration",
            "2 classes per week",
            "Quizzes every 2 weeks",
            "Project Showcase in the last class",
            "Certificate upon completion",
            "Focus on OOP and File Handling"
        ]
    },
    {
        "title": "Python Programming Level 3",
        "short_description": "Advanced Python topics: Data Structures and Algorithms.",
        "description": "This advanced course focuses on efficient data structures and algorithms using Python. You will learn about various data structures like linked lists, stacks, queues, trees, and graphs, and explore common algorithms for searching, sorting, and graph traversal. Emphasis is placed on analyzing algorithm efficiency.",
        "price": 15000, # Reusing previous price
        "duration": "4 Months",
        "level": "Advanced",
        "category": "python",
        "syllabus": [
            {"title": "Module 1: Introduction to Data Structures and Algorithms", "topics": ["Big O Notation", "Analyzing Complexity"]},
            {"title": "Module 2: Linked Lists and Arrays", "topics": ["Singly and Doubly Linked Lists", "Dynamic Arrays"]},
            {"title": "Module 3: Stacks and Queues", "topics": ["Implementations and Applications"]},
            {"title": "Module 4: Trees", "topics": ["Binary Trees", "Binary Search Trees", "Tree Traversals"]},
            {"title": "Module 5: Graphs", "topics": ["Graph Representation", "Graph Traversal (BFS, DFS)"]},
            {"title": "Module 6: Sorting Algorithms", "topics": ["Bubble Sort", "Insertion Sort", "Merge Sort", "Quick Sort"]},
            {"title": "Module 7: Searching Algorithms", "topics": ["Linear Search", "Binary Search"]},
            {"title": "Module 8: Advanced Projects", "topics": ["Implementing algorithms and data structures in projects"]},
            # Add more modules to cover 4 months
        ],
        "status": "Active",
        "features": [
            "4-month duration",
            "2 classes per week",
            "Quizzes every 2 weeks",
            "Project Showcase in the last class",
            "Certificate upon completion",
            "Deep dive into Data Structures and Algorithms"
        ]
    },
    {
        "title": "Robotics with IoT",
        "short_description": "Hands-on robotics programming using Python and integrating IoT concepts.",
        "description": "Learn to build and program robots using Python and popular microcontrollers like Arduino UNO R3. This course covers essential robotics concepts, sensor integration (IR, Ultrasonic, DHT11, MQ-2, Soil Moisture, LDR, Water Sensor), motor control (Servo), wireless communication (Bluetooth), and basic IoT principles to connect your robot to the internet.",
        "price": 5500, # User provided price
        "duration": "4 Months",
        "level": "Advanced", # User specified Advanced
        "category": "robotics_iot", # Categorizing as robotics with IoT
        "syllabus": [
            {"title": "Module 1: Introduction to Robotics and Microcontrollers", "topics": ["What is Robotics?", "Introduction to Arduino UNO R3", "Basic Circuit Building"]},
            {"title": "Module 2: Programming Arduino with Python", "topics": ["Setting up Python-Arduino communication", "Basic I/O Control"]},
            {"title": "Module 3: Sensor Integration - Part 1", "topics": ["IR Sensors", "Ultrasonic Sonar Sensor (HC-SR04)"]},
            {"title": "Module 4: Sensor Integration - Part 2", "topics": ["DHT11 Temperature and Humidity Sensor", "MQ-2 Gas Sensor", "LDR, Water Sensor"]},
            {"title": "Module 5: Actuators and Motor Control", "topics": ["Servo Motor Control", "Relay Module"]},
            {"title": "Module 6: Wireless Communication", "topics": ["HC-06 Bluetooth Module", "Basic Wireless Control"]},
            {"title": "Module 7: Display and Interface", "topics": ["I2C Display (16x2)", "7-Segment Display", "Joystick Module"]},
            {"title": "Module 8: Power Management and Batteries", "topics": ["LiPo Batteries and Charging"]},
            {"title": "Module 9: Introduction to IoT in Robotics", "topics": ["Connecting Robots to the Internet (Basic Concepts)"]},
            {"title": "Module 10: Integrated Robotics Projects", "topics": ["Building and programming mobile robots", "Sensor-based automation"]},
            {"title": "Module 11: Advanced Sensor and Module Use", "topics": ["Potentiometer", "RFID Module", "IMU"]},
            # Add more modules to cover 4 months
        ],
        "status": "Active",
        "features": [
            "4-month duration",
            "2 classes per week",
            "Quizzes every 2 weeks",
            "Project Showcase in the last class",
            "Certificate upon completion",
            "Includes comprehensive robotics component kit (list provided)"
        ],
        "components_included": [
            "Arduino UNO R3 (1)", "Multimeter 500 (1)", "Jumper Wires (M-M, M-F, F-F) (40)", "IR Sensors (2)",
            "Ultrasonic Sonar Sensor (HC-SR04) (1)", "Relay Module (1)", "Servo Motor (1)", "Robotic Chassis(2 Wheel) (1)",
            "HC-06 Bluetooth Module (1)", "DHT11 Temperature and Humidity Sensor (1)", "MQ-2 Gas Sensor (1)",
            "I2C Display (16x2) (1)", "Soil Moisture Sensor (1)", "7-Segment Display (1)", "LiPo Battery (2)",
            "Battery Charger (for LiPo) (1)", "Resistors (various values) (10)", "LEDs (10)", "Joystick Module (1)",
            "Glue Gun (1)", "Potentiometer (1)", "RFID Module (1)", "LDR (Light Dependent Resistor) (1)",
            "Buzzer (2)", "Push Switch (3)", "IMU (1)", "Water sensor (1)", "Screw Driver (1)"
        ]
    },
    {
        "title": "Machine Learning with Python",
        "short_description": "Learn the fundamentals of Machine Learning and build practical ML projects using Python.",
        "description": "Explore the exciting field of Machine Learning. This course covers basic ML concepts, popular algorithms (like Linear Regression, Logistic Regression, Decision Trees, Clustering), data preprocessing, model evaluation, and building simple ML projects using Python libraries like scikit-learn, pandas, and numpy.",
        "price": 18000, # Reusing previous price
        "duration": "4 Months",
        "level": "Advanced", # User specified Advanced
        "category": "machine_learning",
        "syllabus": [
            {"title": "Module 1: Introduction to Machine Learning", "topics": ["What is ML?", "Types of ML (Supervised, Unsupervised)", "ML Workflow"]},
            {"title": "Module 2: Data Preprocessing", "topics": ["Handling Missing Data", "Encoding Categorical Data", "Scaling Features"]},
            {"title": "Module 3: Regression", "topics": ["Linear Regression", "Polynomial Regression", "Evaluating Regression Models"]},
            {"title": "Module 4: Classification", "topics": ["Logistic Regression", "Decision Trees", "Support Vector Machines (SVM)"]},
            {"title": "Module 5: Clustering", "topics": ["K-Means Clustering", "Hierarchical Clustering"]},
            {"title": "Module 6: Model Evaluation and Selection", "topics": ["Metrics (Accuracy, Precision, Recall, F1-score)", "Cross-Validation", "Hyperparameter Tuning"]},
            {"title": "Module 7: Introduction to Neural Networks", "topics": ["Basic Concepts of Neural Networks"]},
            {"title": "Module 8: Building ML Projects", "topics": ["Applying ML techniques to real-world problems"]},
            # Add more modules to cover 4 months
        ],
        "status": "Active",
        "features": [
            "4-month duration",
            "2 classes per week",
            "Quizzes every 2 weeks",
            "Project Showcase in the last class",
            "Certificate upon completion",
            "Focus on practical ML projects"
        ]
    }
]

def main():
    db = connect_to_db()
    if db is None:
        logger.error("Could not connect to database. Exiting...")
        return

    # Add each course
    for course in courses_list:
        success, message = add_course(db, course)
        if success:
            print(f"✅ Added course: {course['title']}")
        else:
            print(f"❌ Failed to add course: {course['title']} - {message}")

if __name__ == "__main__":
    add_courses_to_db() 