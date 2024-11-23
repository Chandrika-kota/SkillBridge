import mysql.connector
from mysql.connector import Error
from config import DevelopmentConfig

def connect_to_db():
    """Establish a connection to the MySQL database."""
    try:
        connection = mysql.connector.connect(
            host=DevelopmentConfig.DB_HOST,
            user=DevelopmentConfig.DB_USER,
            password=DevelopmentConfig.DB_PASSWORD,
            database=DevelopmentConfig.DB_NAME
        )
        if connection.is_connected():
            print("Connected to the database.")
        return connection
    except Error as e:
        print(f"Error connecting to the database: {e}")
        return None

def close_db_connection(connection):
    """Close the database connection."""
    if connection and connection.is_connected():
        connection.close()
        print("Database connection closed.")
