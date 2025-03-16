from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.spinner import Spinner
from kivy.uix.switch import Switch
from kivy.uix.scrollview import ScrollView
from database import DatabaseManager
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from google_drive_backup import GoogleDriveBackup, check_and_backup
from scoring_logic import ScoringCalculator
import io
import os
from kivy.core.image import Image as CoreImage
from kivy.graphics import Color
from kivy.uix.image import Image
import matplotlib.pyplot as plt
from matplotlib.backends.backend_agg import FigureCanvasAgg


class YearMonthSelectionScreen(Screen):
    def __init__(self, db_manager, **kwargs):
        super().__init__(**kwargs)
        self.db_manager = db_manager
        self.create_ui()

    def create_ui(self):
        layout = BoxLayout(orientation='vertical', padding=20, spacing=10)

        # Year Input
        year_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=50)
        year_label = Label(text='Year:', size_hint_x=0.3)
        self.year_input = TextInput(
            multiline=False, 
            input_type='number', 
            size_hint_x=0.7
        )
        year_layout.add_widget(year_label)
        year_layout.add_widget(self.year_input)
        layout.add_widget(year_layout)

        # Month Input
        month_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=50)
        month_label = Label(text='Month (01-12):', size_hint_x=0.3)
        self.month_input = TextInput(
            multiline=False, 
            input_type='number', 
            size_hint_x=0.7
        )
        month_layout.add_widget(month_label)
        month_layout.add_widget(self.month_input)
        layout.add_widget(month_layout)

        # View Data Button
        view_button = Button(
            text='View Data', 
            size_hint_y=None, 
            height=50
        )
        view_button.bind(on_press=self.show_data_view)
        layout.add_widget(view_button)

        # Back Button
        back_button = Button(
            text='Back', 
            size_hint_y=None, 
            height=50
        )
        back_button.bind(on_press=self.go_back)
        layout.add_widget(back_button)

        self.add_widget(layout)

    def show_data_view(self, *args):
        # Validate inputs
        try:
            year = self.year_input.text
            month = self.month_input.text.zfill(2)  # Ensure two-digit format
            
            # Create DataViewScreen with year and month
            data_view_screen = DataViewScreen(
                self.db_manager, 
                year=year, 
                month=month, 
                name='data_view'
            )
            
            # Add to screen manager and switch
            self.manager.add_widget(data_view_screen)
            self.manager.current = 'data_view'
        
        except ValueError:
            # Show error (you might want to use a popup)
            print("Invalid year or month")

    def go_back(self, *args):
        self.manager.current = 'main'
        
class BackupScreen(Screen):
    def __init__(self, db_manager, **kwargs):
        super().__init__(**kwargs)
        self.db_manager = db_manager
        self.create_ui()

    def create_ui(self):
        layout = BoxLayout(orientation='vertical', padding=20, spacing=10)

        # Backup Button
        backup_button = Button(
            text='Backup to Google Drive', 
            size_hint_y=None, 
            height=50
        )
        backup_button.bind(on_press=self.perform_backup)
        layout.add_widget(backup_button)

        # Status Label
        self.status_label = Label(
            text='', 
            size_hint_y=None, 
            height=50
        )
        layout.add_widget(self.status_label)

        # Back Button
        back_button = Button(
            text='Back to Main', 
            size_hint_y=None, 
            height=50
        )
        back_button.bind(on_press=self.go_back)
        layout.add_widget(back_button)

        self.add_widget(layout)

    def perform_backup(self, *args):
        db_path = os.path.join(os.path.dirname(__file__), self.db_manager.db_name)
        
        backup = GoogleDriveBackup(db_path)
        success, message = backup.backup_database()
        
        self.status_label.text = message
        self.status_label.color = (0, 1, 0, 1) if success else (1, 0, 0, 1)

    def go_back(self, *args):
        self.manager.current = 'main'

class StatisticsScreen(Screen):
    def __init__(self, db_manager, **kwargs):
        super().__init__(**kwargs)  # Important: pass kwargs to parent
        self.db_manager = db_manager
        self.create_ui()

    def create_daily_score_chart(self):
        # Fetch daily scores
        cursor = self.db_manager.conn.cursor()
        cursor.execute('SELECT date, daily_score FROM entries ORDER BY date DESC LIMIT 7')
        entries = cursor.fetchall()

        dates = [entry[0] for entry in entries]
        scores = [entry[1] for entry in entries]

        plt.figure(figsize=(10, 4))
        plt.plot(dates, scores, marker='o')
        plt.title('Daily Score Trend')
        plt.xlabel('Date')
        plt.ylabel('Daily Score')
        plt.xticks(rotation=45)
        plt.tight_layout()

        # Convert plot to image
        buf = io.BytesIO()
        plt.savefig(buf, format='png')
        buf.seek(0)
        plt.close()

        # Create Kivy texture
        return CoreImage(buf, ext='png').texture

    def create_activity_frequency_chart(self):
         # Fetch daily scores
        cursor = self.db_manager.conn.cursor()
        cursor.execute('SELECT date, dhyaanam FROM entries ORDER BY date DESC LIMIT 7')
        entries = cursor.fetchall()

        dates = [entry[0] for entry in entries]
        scores = [entry[1] for entry in entries]

        plt.figure(figsize=(10, 4))
        plt.plot(dates, scores, marker='o')
        plt.title('Daily Score Trend')
        plt.xlabel('Date')
        plt.ylabel('Daily Score')
        plt.xticks(rotation=45)
        plt.tight_layout()

        # Convert plot to image
        buf = io.BytesIO()
        plt.savefig(buf, format='png')
        buf.seek(0)
        plt.close()

        # Create Kivy texture
        return CoreImage(buf, ext='png').texture

    def create_ui(self):
        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)

        # Scrollview for multiple charts
        scroll_view = ScrollView()
        chart_layout = BoxLayout(orientation='vertical', size_hint_y=None)
        chart_layout.bind(minimum_height=chart_layout.setter('height'))

        # Daily Score Trend
        daily_score_texture = self.create_daily_score_chart()
        daily_score_widget = Image(texture=daily_score_texture, size_hint_y=None, height=500)
        chart_layout.add_widget(Label(text="Daily Score Trend", size_hint_y=None, height=50))
        chart_layout.add_widget(daily_score_widget)

        # Activity Frequency
        activity_texture = self.create_activity_frequency_chart()
        activity_widget = Image(texture=activity_texture, size_hint_y=None, height=500)
        chart_layout.add_widget(Label(text="Activity Frequency", size_hint_y=None, height=50))
        chart_layout.add_widget(activity_widget)

        scroll_view.add_widget(chart_layout)
        layout.add_widget(scroll_view)

        # Back Button
        back_button = Button(
            text='Back to Main', 
            size_hint_y=None, 
            height=50
        )
        back_button.bind(on_press=self.go_back)
        layout.add_widget(back_button)

        self.add_widget(layout)
    
    def go_back(self, *args):
        # Change to main screen
        self.manager.current = 'main'


class DataViewScreen(Screen):
    def __init__(self, db_manager, year, month, **kwargs):
        # Use super() to properly initialize the Screen
        super().__init__(**kwargs)
        self.db_manager = db_manager
        self.year = year
        self.month = month
        self.create_ui()

    def create_ui(self):
        layout = BoxLayout(orientation='vertical', padding=20, spacing=10)

        # Title with selected month/year
        self.title_label = Label(
            text=f"Data for {self.month}/{self.year}", 
            size_hint_y=None, 
            height=50,
            bold=True
        )
        layout.add_widget(self.title_label)

        # Scrollable Data Table
        scroll_view = ScrollView()
        self.data_grid = GridLayout(
            cols=7,  # Match number of headers
            size_hint_y=None,
            row_default_height='48dp',
            spacing=[5, 5]
        )
        self.data_grid.bind(minimum_height=self.data_grid.setter('height'))

        # Define headers with specific widths
        headers = [
            ('Date', 0.15),
            ('Urine Color', 0.15),
            ('Sugar Threshold', 0.15),
            ('Processed Food', 0.15),
            ('Physical Activity', 0.15),
            ('Dhyaanam', 0.15),
            ('Score', 0.1)
        ]
        
        # Add headers
        for header, width in headers:
            label = Label(
                text=header, 
                bold=True, 
                size_hint_x=width,
                halign='center'
            )
            self.data_grid.add_widget(label)

        # Fetch and display data
        cursor = self.db_manager.conn.cursor()
        cursor.execute('''
            SELECT date, urine_color, 
                   sugar_threshold, processed_food, 
                   physical_activity, dhyaanam, 
                   daily_score
            FROM entries
            WHERE strftime('%Y', date) = ? AND strftime('%m', date) = ?
            ORDER BY date
        ''', (self.year, self.month))
        
        entries = cursor.fetchall()

        # Display entries
        if not entries:
            # No entries found
            no_data_label = Label(
                text="No entries found for selected month/year", 
                size_hint_x=1
            )
            self.data_grid.add_widget(no_data_label)
        else:
            for entry in entries:
                for i, value in enumerate(entry):
                    # Get the corresponding width from headers
                    width = headers[i][1]
                    
                    label = Label(
                        text=str(value), 
                        size_hint_x=width,
                        halign='center'
                    )
                    self.data_grid.add_widget(label)

        scroll_view.add_widget(self.data_grid)
        layout.add_widget(scroll_view)

        # Back Button
        back_button = Button(
            text='Back', 
            size_hint_y=None, 
            height=50
        )
        back_button.bind(on_press=self.go_back)
        layout.add_widget(back_button)

        self.add_widget(layout)

    def go_back(self, *args):
        self.manager.current = 'year_month_selection'



class LifestyleTrackerApp(App):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Initialize database when app starts
        self.db_manager = DatabaseManager()
        check_and_backup('lifestyle_tracker.db')

    def build(self):
        # Create screen manager
        screen_manager = ScreenManager()

        # Create main screen
        main_screen = Screen(name='main')
        main_layout = BoxLayout(orientation='vertical')

        # Create a scrollable layout
        scroll_view = ScrollView()
        entry_layout = BoxLayout(orientation='vertical', padding=20, spacing=10, size_hint_y=None)
        entry_layout.bind(minimum_height=entry_layout.setter('height'))

        # Average Score Label
        avg_score = ScoringCalculator.get_average_score(self.db_manager)
        avg_score_label = Label(
            text=f"All-Time Average Score: {avg_score}", 
            size_hint_y=None, 
            height=50,
            bold=True,
            font_size=18,
            color=(0, 0.5, 0.5, 1)
        )
        main_layout.add_widget(avg_score_label)

        # Hours Slept
        hours_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=50)
        hours_label = Label(text='Hours Slept:', size_hint_x=0.3)
        self.hours_input = TextInput(multiline=False, size_hint_x=0.7)
        hours_layout.add_widget(hours_label)
        hours_layout.add_widget(self.hours_input)
        main_layout.add_widget(hours_layout)

        try:
            hours_slept = float(self.hours_input.text or 0)
        except ValueError:
            print("Invalid hours slept. Please enter a number.")
            return

        # Sleep Quality
        sleep_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=50)
        sleep_label = Label(text='Sleep Quality:', size_hint_x=0.3)
        self.sleep_spinner = Spinner(
            text='Select Quality',
            values=('Good', 'Moderate', 'Poor'),
            size_hint_x=0.7
        )
        sleep_layout.add_widget(sleep_label)
        sleep_layout.add_widget(self.sleep_spinner)
        main_layout.add_widget(sleep_layout)

        # Urine Color
        urine_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=50)
        urine_label = Label(text='Urine Color:', size_hint_x=0.3)
        self.urine_spinner = Spinner(
            text='Select Color',
            values=('Very Mild Yellow', 'Clear as Water', 'Mild Yellow', 'Yellow'),
            size_hint_x=0.7
        )
        urine_layout.add_widget(urine_label)
        urine_layout.add_widget(self.urine_spinner)
        main_layout.add_widget(urine_layout)

        # Sugar Threshold
        sugar_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=50)
        sugar_label = Label(text='Sugar Threshold:', size_hint_x=0.3)
        self.sugar_spinner = Spinner(
            text='Select',
            values=('Yes', 'No'),
            size_hint_x=0.7
        )
        sugar_layout.add_widget(sugar_label)
        sugar_layout.add_widget(self.sugar_spinner)
        main_layout.add_widget(sugar_layout)

        # Processed Food
        processed_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=50)
        processed_label = Label(text='Processed Food:', size_hint_x=0.3)
        self.processed_spinner = Spinner(
            text='Select',
            values=('Yes', 'No'),
            size_hint_x=0.7
        )
        processed_layout.add_widget(processed_label)
        processed_layout.add_widget(self.processed_spinner)
        main_layout.add_widget(processed_layout)

        # Oily Items
        oily_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=50)
        oily_label = Label(text='Oily Items:', size_hint_x=0.3)
        self.oily_spinner = Spinner(
            text='Select',
            values=('Yes', 'No'),
            size_hint_x=0.7
        )
        oily_layout.add_widget(oily_label)
        oily_layout.add_widget(self.oily_spinner)
        main_layout.add_widget(oily_layout)

        # Physical Activity
        physical_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=50)
        physical_label = Label(text='Physical Activity:', size_hint_x=0.3)
        self.physical_spinner = Spinner(
            text='Select',
            values=('Yes', 'No'),
            size_hint_x=0.7
        )
        physical_layout.add_widget(physical_label)
        physical_layout.add_widget(self.physical_spinner)
        main_layout.add_widget(physical_layout)

        # Dhyaanam (Meditation)
        dhyaanam_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=50)
        dhyaanam_label = Label(text='Dhyaanam:', size_hint_x=0.3)
        self.dhyaanam_spinner = Spinner(
            text='Select',
            values=('Yes', 'No'),
            size_hint_x=0.7
        )
        dhyaanam_layout.add_widget(dhyaanam_label)
        dhyaanam_layout.add_widget(self.dhyaanam_spinner)
        main_layout.add_widget(dhyaanam_layout)

        # Exam Exempt (Switch)
        exam_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=50)
        exam_label = Label(text='Exam Exempt:', size_hint_x=0.3)
        self.exam_switch = Switch(size_hint_x=0.7)
        exam_layout.add_widget(exam_label)
        exam_layout.add_widget(self.exam_switch)
        main_layout.add_widget(exam_layout)

        # Mood
        mood_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=50)
        mood_label = Label(text='Mood:', size_hint_x=0.3)
        self.mood_spinner = Spinner(
            text='Select Mood',
            values=('Stressed', 'Anxious', 'Fine', 'Happy'),
            size_hint_x=0.7
        )
        mood_layout.add_widget(mood_label)
        mood_layout.add_widget(self.mood_spinner)
        main_layout.add_widget(mood_layout)

        # Remarks (Optional Text Input)
        remarks_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=100)
        remarks_label = Label(text='Remarks:', size_hint_x=0.3)
        self.remarks_input = TextInput(
            multiline=True, 
            hint_text='Optional additional notes...',
            size_hint_x=0.7
        )
        remarks_layout.add_widget(remarks_label)
        remarks_layout.add_widget(self.remarks_input)
        main_layout.add_widget(remarks_layout)

     # Statistics Button
        stats_button = Button(
            text='View Statistics', 
            size_hint_y=None, 
            height=50
        )
        stats_button.bind(on_press=self.show_statistics)
        entry_layout.add_widget(stats_button)

        # Save Button
        save_button = Button(
            text='Save Entry', 
            size_hint_y=None, 
            height=50
        )
        save_button.bind(on_press=self.save_entry)
        entry_layout.add_widget(save_button)

        # Data View Button
        data_view_button = Button(
            text='View Data', 
            size_hint_y=None, 
            height=50
        )
        data_view_button.bind(on_press=self.show_year_month_selection)
        entry_layout.add_widget(data_view_button)

        # Add entry_layout to scroll_view
        scroll_view.add_widget(entry_layout)

        # Add scroll_view to main_layout
        main_layout.add_widget(scroll_view)

        # Add main_layout to main_screen
        main_screen.add_widget(main_layout)

        # Add main screen to screen manager
        screen_manager.add_widget(main_screen)

        # Create and add statistics screen
        stats_screen = StatisticsScreen(self.db_manager, name='statistics')
        screen_manager.add_widget(stats_screen)

        # Create and add year month selection screen
        year_month_screen = YearMonthSelectionScreen(self.db_manager, name='year_month_selection')
        screen_manager.add_widget(year_month_screen)

        # Add backup button in main screen
        backup_screen = BackupScreen(self.db_manager, name='backup')
        screen_manager.add_widget(backup_screen)
        backup_button = Button(
            text='Backup', 
            size_hint_y=None, 
            height=50
        )
        entry_layout.add_widget(backup_button)
        backup_button.bind(on_press=self.show_backup)

        return screen_manager

    
    def show_backup(self, *args):
        self.root.current = 'backup'

    def show_year_month_selection(self, *args):
        self.root.current = 'year_month_selection'

    def show_statistics(self, *args):
        self.root.current = 'statistics'

    def save_entry(self, instance):
        entry_data = {
            'hours_slept': float(self.hours_input.text or 0),
            'sleep_quality': self.sleep_spinner.text,
            'urine_color': self.urine_spinner.text,
            'sugar_threshold': self.sugar_spinner.text,
            'processed_food': self.processed_spinner.text,
            'oily_items': self.oily_spinner.text,
            'physical_activity': self.physical_spinner.text,
            'dhyaanam': self.dhyaanam_spinner.text,
            'exam_exempt': 'Yes' if self.exam_switch.active else 'No',
            'mood': self.mood_spinner.text,
            'remarks': self.remarks_input.text
        }

        for key, value in entry_data.items():
            print(f"{key}: {value}")
        
        self.db_manager.insert_entry(entry_data)

    def on_stop(self):
        self.db_manager.close()
        


def main():
    LifestyleTrackerApp().run()

if __name__ == '__main__':
    main()