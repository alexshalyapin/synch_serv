from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.uix.tabbedpanel import TabbedPanel, TabbedPanelItem
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.graphics import Color, Rectangle
import math

# Global variables
g = float(1.62)
M = float(2250)
m = [float(1000)]
C = float(3660)
q = float(0)
h = [float(0.0000001)]
h_min = float(0.00000001)
V_h = [float(0)]
x = [float(0)]
u = [float(0)]
a = float(0)
a_max = float(3 * 9.81)
al = float(0)
dm = float(0)
t = float(0)
i = int(0)
t_f = [float(0)]

# Data storage for the second tab
data_history = []


def q_a():
    global q, a
    q = dm / t
    a = q * C / (M + m[i])


def main_bl():
    global V_h, x, u, h, m
    V_old = V_h[i]
    V_h.append(V_h[i] + a * t * math.sin(al))
    x.append(x[i] + (V_old + V_h[i + 1]) / 2 * t)
    u_old = u[i]
    u.append(u[i] + (a * math.cos(al) - g) * t)
    h.append(h[i] + (u[i + 1] + u_old) / 2 * t)
    m.append(m[i] - q * t)


def correct_bl():
    global V_h, x, u, h, m
    V_old = V_h[i - 1]
    V_h[i] = V_h[i - 1] + a * t * math.sin(al)
    x[i] = x[i - 1] + (V_old + V_h[i]) / 2 * t
    u_old = u[i - 1]
    u[i] = u[i - 1] + (a * math.cos(al) - g) * t
    h[i] = h[i - 1] + (u[i] + u_old) / 2 * t
    m[i] = m[i - 1] - q * t


class BorderedLabel(Label):
    """Custom Label with a border."""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        with self.canvas.before:
            # Set border color
            Color(0, 0, 0, 1)  # Black border
            self.border = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self.update_border, size=self.update_border)

    def update_border(self, *args):
        """Update the border when the label's position or size changes."""
        self.border.pos = self.pos
        self.border.size = self.size


class TabbedTextInput(TextInput):
    def __init__(self, next_input=None, **kwargs):
        super().__init__(**kwargs)
        self.next_input = next_input

    def keyboard_on_key_down(self, window, keycode, text, modifiers):
        # Handle Tab key press
        if keycode[1] == 'tab':
            if self.next_input:
                self.next_input.focus = True
            return True  # Prevent default behavior
        return super().keyboard_on_key_down(window, keycode, text, modifiers)


class SimulationApp(App):
    def build(self):
        self.tabs = TabbedPanel(do_default_tab=False)

        # First Tab: Input and Results
        self.input_tab = TabbedPanelItem(text="Input")
        self.input_layout = BoxLayout(orientation='vertical', padding=10, spacing=10)

        # Input fields
        self.dm_input = TabbedTextInput(hint_text="Enter dm", multiline=False)
        self.t_input = TabbedTextInput(hint_text="Enter t", multiline=False)
        self.al_input = TabbedTextInput(hint_text="Enter al", multiline=False)

        # Set up tab order
        self.dm_input.next_input = self.t_input
        self.t_input.next_input = self.al_input
        self.al_input.next_input = self.dm_input  # Loop back to the first input

        # Submit button
        self.submit_button = Button(text="Submit", size_hint=(1, 0.2))
        self.submit_button.bind(on_press=self.process_input)

        # Result label
        self.result_label = Label(text="Results will be shown here", size_hint=(1, 0.6))

        # Add widgets to input layout
        self.input_layout.add_widget(self.dm_input)
        self.input_layout.add_widget(self.t_input)
        self.input_layout.add_widget(self.al_input)
        self.input_layout.add_widget(self.submit_button)
        self.input_layout.add_widget(self.result_label)

        self.input_tab.add_widget(self.input_layout)

        # Second Tab: History
        self.history_tab = TabbedPanelItem(text="History")
        self.history_layout = BoxLayout(orientation='vertical', padding=10, spacing=10)

        # Add column headers
        self.column_headers = GridLayout(cols=9, size_hint_y=None, height=40, spacing=0)
        headers = ["i", "dm", "t", "al", "h", "x", "u", "V_h", "t_f"]
        for header in headers:
            header_label = BorderedLabel(text=header, size_hint_x=None, width=100, bold=True)
            self.column_headers.add_widget(header_label)

        # Scrollable history display
        self.history_scroll = ScrollView(do_scroll_x=True, do_scroll_y=True)
        self.history_table = GridLayout(
            cols=9,
            size_hint_x=None,
            size_hint_y=None,
            spacing=0,
            row_default_height=40,  # Increase row height
            row_force_default=True,  # Force row height
        )
        self.history_table.bind(minimum_width=self.history_table.setter('width'))
        self.history_table.bind(minimum_height=self.history_table.setter('height'))
        self.history_scroll.add_widget(self.history_table)

        # Add widgets to history layout
        self.history_layout.add_widget(self.column_headers)
        self.history_layout.add_widget(self.history_scroll)

        self.history_tab.add_widget(self.history_layout)

        # Add tabs to the main panel
        self.tabs.add_widget(self.input_tab)
        self.tabs.add_widget(self.history_tab)

        return self.tabs

    def process_input(self, instance):
        global dm, t, al, i

        try:
            dm = float(self.dm_input.text)
            t = float(self.t_input.text)
            al = float(self.al_input.text)
            al = math.pi / 180 * al  # Convert degrees to radians

            if dm > m[i]:
                t = t * m[i] / dm
                dm = m[i]

            if dm < 0.05 * (M + m[i]) and t != 0:
                q_a()
                main_bl()
                t_f.append(t_f[i] + t)
                i += 1

                # Store data for history
                data_history.append({
                    "i": i,
                    "dm": dm,
                    "t": t,
                    "al": al,
                    "h": h[i],
                    "x": x[i],
                    "u": u[i],
                    "V_h": V_h[i],
                    "t_f": t_f[i]
                })

                # Display results
                result_text = (
                    f"h[i]: {round(h[i], 2)}\n"
                    f"x[i]: {round(x[i], 2)}\n"
                    f"u[i]: {round(u[i], 2)}\n"
                    f"V_h[i]: {round(V_h[i], 2)}\n"
                    f"t_f[i]: {round(t_f[i], 2)}\n"
                )
                self.result_label.text = result_text

                # Clear input fields
                self.dm_input.text = ""
                self.t_input.text = ""
                self.al_input.text = ""

                # Update history tab
                self.update_history_tab()

            else:
                self.show_popup("Error", "Invalid input: dm must be less than 5% of total mass.")

        except ValueError:
            self.show_popup("Error", "Please enter valid numbers for dm, t, and al.")

    def update_history_tab(self):
        # Clear existing history content
        self.history_table.clear_widgets()

        # Add new history entries
        for entry in data_history:
            # Add each value to the table
            values = [
                str(entry["i"]),
                f"{entry['dm']:.2f}",
                f"{entry['t']:.2f}",
                f"{entry['al']:.4f}",
                f"{entry['h']:.2f}",
                f"{entry['x']:.2f}",
                f"{entry['u']:.2f}",
                f"{entry['V_h']:.2f}",
                f"{entry['t_f']:.2f}"
            ]
            for value in values:
                value_label = BorderedLabel(text=value, size_hint_x=None, width=100)
                self.history_table.add_widget(value_label)

    def show_popup(self, title, message):
        popup_layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        popup_label = Label(text=message)
        popup_button = Button(text="OK", size_hint=(1, 0.2))
        popup_layout.add_widget(popup_label)
        popup_layout.add_widget(popup_button)

        popup = Popup(title=title, content=popup_layout, size_hint=(0.8, 0.4))
        popup_button.bind(on_press=popup.dismiss)
        popup.open()


if __name__ == '__main__':
    SimulationApp().run()
