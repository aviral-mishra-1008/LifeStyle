import sqlite3
from datetime import datetime, timedelta
from scoring_logic import ScoringCalculator

class DatabaseManager:
    def __init__(self, db_name='lifestyle_tracker.db'):
        self.db_name = db_name  
        self.conn = sqlite3.connect(db_name)
        self.create_table()

    def create_table(self):
        # Create table if not exists
        cursor = self.conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT,
                hours_slept REAL,
                sleep_quality TEXT,
                urine_color TEXT,
                sugar_threshold TEXT,
                processed_food TEXT,
                oily_items TEXT,
                physical_activity TEXT,
                dhyaanam TEXT,
                exam_exempt TEXT,
                mood TEXT,
                remarks TEXT,
                daily_score REAL
            )
        ''')
        self.conn.commit()

    def insert_entry(self, entry_data):
        # Insert new entry
        cursor = self.conn.cursor()
        
        # Add current date to entry
        entry_data['date'] = datetime.now().strftime('%Y-%m-%d')
        daily_score = ScoringCalculator.calculate_daily_score(entry_data, self)    
        entry_data['daily_score'] = daily_score

        # Prepare columns and values
        columns = ', '.join(entry_data.keys())
        placeholders = ', '.join(['?' for _ in entry_data])
        
        try:
            cursor.execute(f'''
                INSERT INTO entries ({columns}) 
                VALUES ({placeholders})
            ''', list(entry_data.values()))
            
            self.conn.commit()
            print("Entry saved successfully!")
        except sqlite3.Error as e:
            print(f"An error occurred: {e}")
            self.conn.rollback()



    def get_all_entries(self):
        # Retrieve all entries
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM entries')
        return cursor.fetchall()

    def close(self):
        # Close database connection
        self.conn.close()

    def get_entries_last_30_days(self):
        # Get entries from the last 30 days
        cursor = self.conn.cursor()
        thirty_days_ago = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        
        cursor.execute('''
            SELECT * FROM entries 
            WHERE date >= ?
            ORDER BY date DESC
        ''', (thirty_days_ago,))
        
        return cursor.fetchall()

    def count_recent_yes_entries(self, column, days):
        # Calculate the date threshold
        threshold_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        
        cursor = self.conn.cursor()
        cursor.execute(f'''
            SELECT COUNT(*) 
            FROM entries 
            WHERE {column} = 'Yes' 
            AND date >= ?
        ''', (threshold_date,))
        
        return cursor.fetchone()[0]

    # Modified get_entry_statistics method
    def get_entry_statistics(self):
        # Calculate some basic statistics
        cursor = self.conn.cursor()
        
        # Average hours slept
        cursor.execute('SELECT AVG(hours_slept) FROM entries')
        avg_sleep = cursor.fetchone()[0]
        
        # Most frequent mood
        cursor.execute('''
            SELECT mood, COUNT(*) as mood_count 
            FROM entries 
            GROUP BY mood 
            ORDER BY mood_count DESC 
            LIMIT 1
        ''')
        most_frequent_mood = cursor.fetchone()
        
        # Count of activities in specific time frames
        activities = {
            'physical_activity': {
                '15_days': self.count_recent_yes_entries('physical_activity', 15),
                'total': self.count_recent_yes_entries('physical_activity', 30)
            },
            'dhyaanam': {
                '15_days': self.count_recent_yes_entries('dhyaanam', 15),
                'total': self.count_recent_yes_entries('dhyaanam', 30)
            },
            'processed_food': {
                '30_days': self.count_recent_yes_entries('processed_food', 30)
            },
            'oily_items': {
                '7_days': self.count_recent_yes_entries('oily_items', 7),
                '30_days': self.count_recent_yes_entries('oily_items', 30)
            }
        }
        
        return {
            'avg_sleep': round(avg_sleep, 2) if avg_sleep else 0,
            'most_frequent_mood': most_frequent_mood[0] if most_frequent_mood else 'No data',
            'activities': activities
        }
