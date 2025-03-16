from datetime import datetime, timedelta


class ScoringCalculator:
    @staticmethod
    def count_recent_entries(db_manager, column, value, days):
        # Calculate the date threshold
        threshold_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        
        cursor = db_manager.conn.cursor()
        cursor.execute(f'''
            SELECT COUNT(*) 
            FROM entries 
            WHERE {column} = ? 
            AND date >= ?
        ''', (value, threshold_date))
        
        return cursor.fetchone()[0]

    @staticmethod
    def calculate_daily_score(entry_data, db_manager):
        score = 0

        # 1. Hours Slept
        hours_slept = float(entry_data.get('hours_slept', 0))
        if hours_slept < 6:
            score += 0
        elif 6 <= hours_slept <= 8:
            score += hours_slept
        elif 8 < hours_slept <= 9:
            score += 8
        else:
            score += 5

        # 2. Sleep Quality
        sleep_quality_map = {
            'Good': 5,
            'Moderate': 3,
            'Poor': 1
        }
        score += sleep_quality_map.get(entry_data.get('sleep_quality', 'Poor'), 1)

        # 3. Urine Color
        urine_color_yellow_count = ScoringCalculator.count_recent_entries(
            db_manager, 'urine_color', 'Yellow', 30
        )
        urine_color_map = {
            'Very Mild Yellow': 5,
            'Clear as Water': 4,
            'Mild Yellow': 2,
            'Yellow': max(0, 5 - (0.5 * urine_color_yellow_count))
        }
        score += urine_color_map.get(entry_data.get('urine_color', 'Yellow'), 0)

        # 4. Sugar Threshold
        sugar_threshold_yes_count = ScoringCalculator.count_recent_entries(
            db_manager, 'sugar_threshold', 'Yes', 30
        )
        score += 5 if entry_data.get('sugar_threshold') == 'No' else max(0, 5 - (0.5 * sugar_threshold_yes_count))

        # 5. Processed Food
        processed_food_yes_count = ScoringCalculator.count_recent_entries(
            db_manager, 'processed_food', 'Yes', 30
        )
        if processed_food_yes_count > 7:
            score += max(0, 5 - (0.5 * processed_food_yes_count))
        else:
            score += 5 if entry_data.get('processed_food') == 'No' else 0

        # 6. Oily Items
        oily_items_yes_count_7_days = ScoringCalculator.count_recent_entries(
            db_manager, 'oily_items', 'Yes', 7
        )
        oily_items_yes_count_30_days = ScoringCalculator.count_recent_entries(
            db_manager, 'oily_items', 'Yes', 30
        )
        if oily_items_yes_count_7_days > 3:
            score += max(0, 5 - (0.5 * oily_items_yes_count_30_days))
        else:
            score += 5 if entry_data.get('oily_items') == 'No' else 0

        # 7. Physical Activity
        physical_activity_no_count_15_days = ScoringCalculator.count_recent_entries(
            db_manager, 'physical_activity', 'No', 15
        )
        physical_activity_no_count_30_days = ScoringCalculator.count_recent_entries(
            db_manager, 'physical_activity', 'No', 30
        )
        if physical_activity_no_count_15_days <= 2:
            score += 5 if entry_data.get('physical_activity') == 'Yes' else 0
        else:
            score += max(0, 5 - (0.5 * physical_activity_no_count_30_days))

        # 8. Dhyaanam (Meditation)
        if entry_data.get('exam_exempt') == 'Yes':
            score += 0
        else:
            score += 10 if entry_data.get('dhyaanam') == 'Yes' else -10

        # 9. Mood
        mood_map = {
            'Happy': 5,
            'Fine': 4,
            'Anxious': 0,
            'Stressed': 2
        }
        score += mood_map.get(entry_data.get('mood', 'Stressed'), 2)

        return round(score, 2)

    @staticmethod
    def get_average_score(db_manager):
        cursor = db_manager.conn.cursor()
        cursor.execute('SELECT AVG(daily_score) FROM entries')
        avg_score = cursor.fetchone()[0]
        return round(avg_score, 2) if avg_score is not None else 0