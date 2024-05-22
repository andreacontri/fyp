import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from tkinter.scrolledtext import ScrolledText
import tkinter.font as tkFont

import warnings
warnings.filterwarnings("ignore", category=FutureWarning) # remove future warnings for debugging

# Import custom modules
from packages.vtt_formatting import format_VTT
from packages.timeline_generator import create_timeline_figure
from packages.stats_generator import create_stats_figure
from packages.chunk_splitter import split_text_into_chunks
from packages.summaries import abstractive_summarize_chunks, extractive_summarize_chunks, format_vtt_as_dialogue
from packages.openai import summarize_text
from packages.sentiment import sentiment

# Window size
window_width = 1200
window_height = 800



class VTTAnalyzer(tk.Tk):



    def __init__(self):
        super().__init__()
        
        self.title("VTT File Analyzer")
        self.geometry(f"{window_width}x{window_height}")
        # self.resizable(False, False)  # Make the window fixed in size
        self.custom_font = tkFont.Font(family="Helvetica", size=12)  # Define the font

        self.style = ttk.Style()
        self.style.configure('TButton', background='#8da0cb', foreground='blue', font=self.custom_font)
        self.style.configure('TLabel', font=self.custom_font, foreground='darkgrey')
        self.style.configure('TScale', background='#8da0cb')

        print("Window Initialized")

        self.ab = None  # Abstractive summarization result placeholder
        self.ex = None  # Extractive summarization result placeholder
        self.ai = None  # Summary generated by openAI api
        self.timeline = None  # Timeline visualization placeholder
        self.stats = None  # Statistical data visualization placeholder
        self.chunks = None  # Text chunks for analysis placeholder
        self.canvas_widget = None  # Canvas widget for dynamic content display
        self.df = None  # DataFrame to hold VTT data, if applicable

        self.setup_scrollable_window()  # Setup the main GUI components

        print("Initialized")



    def setup_scrollable_window(self):
        
        ##############################################################################################################   RED
        self.container = tk.Frame(self, bg='red')
        self.container.grid(sticky="nsew")
        
        # Configure the main window grid to expand properly
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Configure the container grid to expand properly
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(1, weight=1)
        ##############################################################################################################   YELLOW

        self.button_frame = tk.Frame(self.container, bg='yellow')
        self.button_frame.grid(row=0, column=0, sticky="ns", pady=10)
        ##############################################################################################################   LIGHTBLUE
        
        self.content_frame = tk.Frame(self.container, bg = "lightblue")
        self.content_frame.grid(row=0, column=1, sticky="nsew", pady=10)
        ##############################################################################################################   LIGHTGREEN

        self.canvas = tk.Canvas(self.content_frame, bg='lightgreen')
        self.scrollbar = ttk.Scrollbar(self.content_frame, orient="vertical", command=self.canvas.yview)

        self.scrollable_frame = ttk.Frame(self.canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.window = self.canvas.create_window((0, 0), window=self.scrollable_frame,)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.scrollbar.grid(row=0, column=1, sticky="ns")

        self.content_frame.grid_columnconfigure(0, weight=1)
        self.content_frame.grid_rowconfigure(0, weight=1)

        self.create_buttons()
        self.create_widgets()


    def create_buttons(self):
        button_options = {
            'style': 'TButton',
            'padding': 10,
            'width': 25
        }

        self.ex_analyze_button = ttk.Button(self.button_frame, text="Show Key Sentences", state='disabled', 
                                            command=self.generate_ex_summary, **button_options)
        self.ex_analyze_button.grid(row=0, column=0, pady=10, padx=10, sticky="ew")

        self.ab_analyze_button = ttk.Button(self.button_frame, text="Show Abstractive Summary", state='disabled', 
                                            command=self.generate_ab_summary, **button_options)
        self.ab_analyze_button.grid(row=1, column=0, pady=10, padx=10, sticky="ew")

        self.ai_analyze_button = ttk.Button(self.button_frame, text="Show openAI Summary", state='disabled', 
                                            command=self.generate_openai_summary, **button_options)
        self.ai_analyze_button.grid(row=2, column=0, pady=10, padx=10, sticky="ew")

        self.transcript_button = ttk.Button(self.button_frame, text="Show full transcript", state='disabled', 
                                            command=self.view_transcript, **button_options)
        self.transcript_button.grid(row=3, column=0, pady=10, padx=10, sticky="ew")

        self.sentiment_button = ttk.Button(self.button_frame, text="Show sentiment analysis", state='disabled', 
                                           command=self.view_sentiment, **button_options)
        self.sentiment_button.grid(row=4, column=0, pady=10, padx=10, sticky="ew")
        
        
        
    def create_widgets(self):
        self.upload_label = tk.Label(self.scrollable_frame, text="Please upload a VTT file:", 
                                    foreground="green", font=self.custom_font)
        self.upload_label.grid(row=0, column=0, pady=10, padx=10, sticky="n")

        self.upload_button = tk.Button(self.scrollable_frame, text="Upload File", command=self.open_file, 
                                    bg='#66c2a5', fg='white', font=self.custom_font)
        self.upload_button.grid(row=1, column=0, pady=10, padx=10, sticky="nswe")

        self.summary_label = ttk.Label(self.scrollable_frame, text="Select Summary Length", style='TLabel')
        self.summary_label.grid(row=2, column=0, pady=[20, 0], padx=10, sticky="w")

        self.slider = ttk.Scale(self.scrollable_frame, from_=50, to_=1000, orient=tk.HORIZONTAL, length=250)
        self.slider.set(100)
        self.slider.grid(row=3, column=0, pady=10, padx=10, sticky="ew")

        self.value_label = ttk.Label(self.scrollable_frame, text=f"Total words set to: {int(self.slider.get())}", style='TLabel')
        self.value_label.grid(row=4, column=0, pady=10, padx=10, sticky="w")

        self.slider.bind("<Motion>", self.update_label)

        self.summary_box = ScrolledText(self.scrollable_frame, height=10, width=80, 
                                        font=self.custom_font, bg='white', fg='black')
        self.summary_box.grid(row=5, column=0, pady=10, padx=10, sticky="ew")

        self.summary_label = ttk.Label(self.scrollable_frame, text="Summary", style='TLabel')
        self.summary_label.grid(row=6, column=0, pady=[20, 0], padx=10, sticky="w")

        self.summary_box = ScrolledText(self.scrollable_frame, height=10, width=80, 
                                        font=self.custom_font, bg='white', fg='black')
        self.summary_box.grid(row=7, column=0, pady=10, padx=10, sticky="ew")

        self.summary_box.bind("<MouseWheel>", self.on_mouse_wheel_textbox)
        self.bind_all("<MouseWheel>", self.on_mouse_wheel_window)

        
        # # Create an Entry widget for the search term
        # self.search_entry = tk.Entry(self.scrollable_frame)
        # self.search_entry.pack(side='top', fill='x')

        # # Bind the Enter key to the start_search method
        # self.search_entry.bind('<Return>', self.start_search)

        # # Create a Search button
        # search_button = tk.Button(self.scrollable_frame, text='Search', command=self.start_search)
        # search_button.pack(side='top')
        
        print(), print("Widgets Created")


    def update_label(self, event):
        self.value_label.config(text=f"Slider Value: {int(self.slider.get())}")
        # self.generate_openai_summary()


    def search_text(self, search_term, start_index='1.0'):
        """
        Search for a given text in the transcript_box and highlight the matches.
        """
        # Remove any previous highlighting
        self.transcript_box.tag_remove('highlight', '1.0', 'end')

        # Perform the search
        matches = self.transcript_box.search(search_term, start_index, stopindex='end', regexp=False)

        # Highlight the matches
        for match in matches:
            self.transcript_box.tag_add('highlight', match, f"{match}+{len(search_term)}c")
            self.transcript_box.tag_config('highlight', background='yellow')

        # If no matches were found, and the start_index is not already '1.0', restart the search from the beginning
        if not matches and start_index != '1.0':
            self.search_text(search_term, '1.0')



    def start_search(self, event=None):
        """
        Initiate the search when the user presses the Enter key or clicks the search button.
        """
        search_term = self.search_entry.get()
        if search_term:
            self.search_text(search_term)



    def on_mouse_wheel_textbox(self, event):
        """Handle mouse wheel event on the text box"""
        if event.delta > 0:
            self.summary_box.yview_scroll(-1, "units")
        else:
            self.summary_box.yview_scroll(1, "units")



    def on_mouse_wheel_window(self, event):
        """Handle mouse wheel event on the window"""
        if event.delta > 0:
            self.canvas.yview_scroll(-1, "units")
        else:
            self.canvas.yview_scroll(1, "units")



    def open_file(self):
        """
        Open a file dialog to allow the user to select a VTT file and then load its content into the application.
        Upon loading, the function will update the interface to reflect the loaded file and enable further analysis options.
        """
        # Open a file dialog to select a VTT file
        file_path = filedialog.askopenfilename(filetypes=[("VTT files", "*.vtt")])
        if file_path:
            try:
                # Attempt to format and load data from the selected VTT file
                self.df, self.formatted_content = format_VTT(file_path)
                
                self.create_buttons()
                # Enable analysis buttons once file is successfully loaded
                self.ex_analyze_button.config(state='normal')
                self.ab_analyze_button.config(state='normal')
                self.ai_analyze_button.config(state='normal')
                self.transcript_button.config(state='normal')
                self.sentiment_button.config(state='normal')
                
                # Update the upload label to show the loaded file name
                self.upload_label.config(text=f"File loaded: {file_path.split('/')[-1]}")
                
                # Optional debugging message to confirm file load
                print(), print("VTT file loaded successfully.")

                # Display visualizations and summaries based on the loaded data
                self.show_plot(create_timeline_figure)  # Visualize timeline data
                self.show_plot(create_stats_figure)  # Visualize statistical data
                

            except Exception as e:
                # Handle exceptions by showing an error message and updating the UI
                messagebox.showerror("Error", str(e))
                self.upload_label.config(text="Failed to load file.")



    def insert_text(self, text):
        """
        Insert text into the summary box widget, allowing modifications only during the update. The function also
        handles enabling buttons based on the content being displayed, depending on whether it matches predefined
        summaries for extractive or abstractive analysis results.

        Args:
            text (str): The text to be inserted into the summary box.
        """
        # Enable the text box for editing
        self.summary_box.configure(state='normal')
        # Clear existing content
        self.summary_box.delete('1.0', tk.END)
        # Insert new text
        self.summary_box.insert(tk.END, text)
        # Disable the text box to prevent user edits
        self.summary_box.configure(state='disabled')

        # Conditional UI update based on the text content
        match text:
            case self.ex:
                # Re-enable the button for extractive summary analysis if relevant
                self.ex_analyze_button.config(state='normal')
            case self.ab:
                # Re-enable the button for abstractive summary analysis if relevant
                self.ab_analyze_button.config(state='normal')



    def view_transcript(self):
        """
        View the entire transcript
        """
        
        # Setup the text box for the transcript
        
        self.transcript_label = tk.Label(self.scrollable_frame, text="Full Transcript", font=self.custom_font)
        self.transcript_label.grid(row=8, column=0, pady=[20, 0], padx=10, sticky="w")
        
        self.transcript_box = ScrolledText(self.scrollable_frame, height=50, width=80, bg='white', fg='black')
        self.transcript_box.grid(row=9, column=0, pady=10, padx=10, sticky="ew")
        
        # Enable the text box for editing
        self.transcript_box.configure(state='normal')
        # Clear existing content
        self.transcript_box.delete('1.0', tk.END)
        # Insert new text
        self.transcript_box.insert(tk.END, self.formatted_content)
        # Disable the text box to prevent user edits
        self.transcript_box.configure(state='disabled')
        print("Transcript printed")





    def view_sentiment(self):
        """
        View the sentiment analysis
        """
        
        # Setup the text box for the sentiment analysis
        
        self.sentiment_label = tk.Label(self.scrollable_frame, text="Full sentiment analysis", font=self.custom_font)
        self.sentiment_label.grid(row=10, column=0, pady=[20, 0], padx=10, sticky="w")
        
        self.sentiment_box = ScrolledText(self.scrollable_frame, height=20, width=80, bg='white', fg='black')
        self.sentiment_box.grid(row=11, column=0, pady=10, padx=10, sticky="ew")
        
        # Enable the text box for editing
        self.sentiment_box.configure(state='normal')
        # Clear existing content
        self.sentiment_box.delete('1.0', tk.END)
        # Insert new text
        self.sentiment_box.insert(tk.END, sentiment(self.df))
        # Disable the text box to prevent user edits
        self.sentiment_box.configure(state='disabled')
        print("Sentiment printed")





    def generate_ex_summary(self):
        """
        Generate an extractive summary from the loaded VTT content. This function checks if the summary has been
        previously generated. If not, it processes the content, generates the summary, and formats it. The summary
        is then displayed in the GUI.
        """
        # Check if the extractive summary has already been generated
        if self.ex is None:
            # Split the text into chunks if not already done
            if self.chunks is None:
                self.chunks = split_text_into_chunks(self.formatted_content)
            # Generate an extractive summary from the chunks
            final_summary = extractive_summarize_chunks(self.chunks)
            # Format the summary for display
            self.ex = format_vtt_as_dialogue(final_summary)
            # Optional debugging message to confirm the extraction
            print("Key Sentences Extracted")

        # Display the extractive summary in the GUI
        self.insert_text(self.ex)



    def generate_ab_summary(self):
        """
        Generate an abstractive summary from the loaded VTT content. This function checks if the summary has been
        previously generated. If not, it processes the content and generates the summary. The summary is then displayed
        in the GUI.
        """
        # Check if the abstractive summary has already been generated
        if self.ab is None:
            # Split the text into chunks if not already done
            if self.chunks is None:
                self.chunks = split_text_into_chunks(self.formatted_content)
            # Generate an abstractive summary from the chunks
            self.ab = abstractive_summarize_chunks(self.chunks)
            # Optional debugging message to confirm the generation
            print(), print("Summary Generated")

        # Display the abstractive summary in the GUI
        self.insert_text(self.ab)



    def generate_openai_summary(self):
        """
        Generate a summary using an OpenAI model and print it.
        """
        tokens = self.slider.get()
        # Check if the abstractive summary has already been generated
        # if self.ai is None:
        # Split the text into chunks if not already done
        # Generate an abstractive summary from the chunks
        self.ai = summarize_text(self.formatted_content, tokens)
        #debugging message to confirm the generation
        print(), print("AI Summary Generated")
        
        # Display the ai summary in the GUI
        self.insert_text(self.ai)



    def show_plot(self, plot_function):
        """
        Display a matplotlib plot in the GUI. This method generates a plot using a provided function and
        data, then integrates it into the scrollable canvas area of the interface.

        Args:
            plot_function (function): A function that takes a DataFrame and returns a matplotlib figure.
        """
        # Generate a plot with the provided function using the loaded data
        fig = plot_function(self.df)
        # Close the figure to free up memory resources
        plt.close(fig)

        # Embed the figure into the tkinter canvas using FigureCanvasTkAgg
        self.canvas_widget = FigureCanvasTkAgg(fig, master=self.scrollable_frame)
        self.canvas_widget.draw()
        self.canvas_widget.get_tk_widget().grid(row=8, column=0, pady=10, padx=10, sticky="ew")
        # Update the scroll region to include the new plot
        self.update_scroll_region()





    def update_scroll_region(self):
        """
        Update the scroll region of the canvas. This method is called after adding or resizing
        content within the scrollable area to ensure that the entire content is accessible
        through scrolling.
        """
        # Adjust the scroll region to fit the new size of the content
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

