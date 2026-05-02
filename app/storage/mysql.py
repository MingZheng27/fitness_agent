import logging
import mysql.connector
from mysql.connector import Error
from typing import Optional, List, Dict, Any
from app.config import get_settings
import uuid
from datetime import datetime
import json

logger = logging.getLogger(__name__)


class MySQLClient:
    def __init__(self):
        self.settings = get_settings()
        self._connection = None

    def get_connection(self):
        try:
            if self._connection is None or not self._connection.is_connected():
                self._connection = mysql.connector.connect(
                    host=self.settings.mysql_host,
                    port=self.settings.mysql_port,
                    user=self.settings.mysql_user,
                    password=self.settings.mysql_password,
                    database=self.settings.mysql_database
                )
            return self._connection
        except Error as e:
            logger.error(f"MySQL connection failed: {e}")
            raise

    def init_tables(self):
        conn = self.get_connection()
        cursor = conn.cursor()

        # Create users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id VARCHAR(36) PRIMARY KEY,
                tenant_id VARCHAR(36) NOT NULL,
                username VARCHAR(100),
                age INT,
                gender VARCHAR(20),
                height FLOAT,
                weight FLOAT,
                fitness_goals JSON,
                constraints JSON,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Create exercise_records table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS exercise_records (
                id VARCHAR(36) PRIMARY KEY,
                user_id VARCHAR(36) NOT NULL,
                date DATE NOT NULL,
                exercise_type INT NOT NULL,
                duration_minutes INT,
                intensity INT,
                calories_burned INT,
                recovery_status VARCHAR(20),
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)

        # Create diet_records table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS diet_records (
                id VARCHAR(36) PRIMARY KEY,
                user_id VARCHAR(36) NOT NULL,
                date DATE NOT NULL,
                meal_type VARCHAR(20),
                foods JSON,
                calories INT,
                nutrients JSON,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)

        # Create user_preferences table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_preferences (
                user_id VARCHAR(36) PRIMARY KEY,
                exercise_preferences JSON,
                diet_preferences JSON,
                fitness_goals JSON,
                constraints JSON,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)

        conn.commit()
        cursor.close()

    def create_user(self, tenant_id: str, username: str, age: int, gender: str,
                   height: float, weight: float, fitness_goals: List[str],
                   constraints: Dict[str, Any]) -> str:
        conn = self.get_connection()
        cursor = conn.cursor()
        user_id = str(uuid.uuid4())

        cursor.execute("""
            INSERT INTO users (id, tenant_id, username, age, gender, height, weight, fitness_goals, constraints)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (user_id, tenant_id, username, age, gender, height, weight,
              json.dumps(fitness_goals), json.dumps(constraints)))

        # Create empty preferences
        cursor.execute("""
            INSERT INTO user_preferences (user_id) VALUES (%s)
        """, (user_id,))

        conn.commit()
        cursor.close()
        return user_id

    def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        conn = self.get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
        result = cursor.fetchone()
        cursor.close()
        return result

    def create_exercise_record(self, user_id: str, date: str, exercise_type: str,
                               duration_minutes: int, intensity: int, calories_burned: int,
                               recovery_status: str, notes: str) -> str:
        conn = self.get_connection()
        cursor = conn.cursor()
        record_id = str(uuid.uuid4())

        cursor.execute("""
            INSERT INTO exercise_records (id, user_id, date, exercise_type, duration_minutes, intensity, calories_burned, recovery_status, notes)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (record_id, user_id, date, exercise_type, duration_minutes, intensity, calories_burned, recovery_status, notes))

        conn.commit()
        cursor.close()
        return record_id

    def get_exercise_records(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        conn = self.get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT * FROM exercise_records WHERE user_id = %s ORDER BY date DESC LIMIT %s
        """, (user_id, limit))
        results = cursor.fetchall()
        cursor.close()
        return results

    def create_diet_record(self, user_id: str, date: str, meal_type: str,
                           foods: str, calories: int, nutrients: str) -> str:
        conn = self.get_connection()
        cursor = conn.cursor()
        record_id = str(uuid.uuid4())

        cursor.execute("""
            INSERT INTO diet_records (id, user_id, date, meal_type, foods, calories, nutrients)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (record_id, user_id, date, meal_type, foods, calories, nutrients))

        conn.commit()
        cursor.close()
        return record_id

    def get_diet_records(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        conn = self.get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT * FROM diet_records WHERE user_id = %s ORDER BY date DESC LIMIT %s
        """, (user_id, limit))
        results = cursor.fetchall()
        cursor.close()
        return results

    def get_user_preferences(self, user_id: str) -> Optional[Dict[str, Any]]:
        conn = self.get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM user_preferences WHERE user_id = %s", (user_id,))
        result = cursor.fetchone()
        cursor.close()
        return result

    def update_user_preferences(self, user_id: str, exercise_preferences: str,
                               diet_preferences: str, fitness_goals: str, constraints: str) -> bool:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE user_preferences
            SET exercise_preferences = %s, diet_preferences = %s, fitness_goals = %s, constraints = %s
            WHERE user_id = %s
        """, (exercise_preferences, diet_preferences, fitness_goals, constraints, user_id))
        conn.commit()
        cursor.close()
        return cursor.rowcount > 0

    def get_user_stats(self, user_id: str) -> Dict[str, Any]:
        conn = self.get_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT COUNT(*) as total_exercises, COALESCE(SUM(calories_burned), 0) as total_calories
            FROM exercise_records WHERE user_id = %s
        """, (user_id,))
        exercise_stats = cursor.fetchone()

        cursor.execute("""
            SELECT COUNT(*) as total_meals FROM diet_records WHERE user_id = %s
        """, (user_id,))
        diet_stats = cursor.fetchone()

        cursor.close()
        return {
            "total_exercises": exercise_stats["total_exercises"],
            "total_calories_burned": exercise_stats["total_calories"],
            "total_meals": diet_stats["total_meals"]
        }


mysql_client = MySQLClient()