from typing import List
import glob
import tkinter as tk
from tkinter import filedialog
from tkinter import messagebox
from tkinter import font as tkfont
import bs4
import os
import re
import time

main_dir = os.path.expanduser('~/.local/share/keeper')
notes_dir = os.path.join(main_dir, 'notes')

main_background_color = '#E6E6E6'
box_color = '#FAFAFA'
gap = 10

root = tk.Tk()
root.title("Keeper")
font = tkfont.Font()


class FirstRunView(tk.Frame):
    """The starting screen a user sees when there are no notes.
    
    Args:
        parent: tkinter object that will contain the class
        frame_background (optional): tkinter color (defined word,
                                     6-digit hex, etc.) for background
        button_background (optional): tkinter color (defined word,
                                      6-digit hex, etc.) for buttons
        
    """
    
    def __init__(self, parent:tk.Tk,
                 frame_background:str=main_background_color,
                 button_background:str=box_color):
        """The constructor for FirstRunView class."""
        super().__init__(parent, background=frame_background)
        root.minsize(root.winfo_width(), root.winfo_height())
        self.pack(expand=True, fill='both')
        
        frame = tk.Frame(self,background=frame_background)
        frame.place(relx=0.5, rely=0.5, anchor='center')
        
        l1 = tk.Label(frame, text="Welcome to Keeper!\n")
        l1.config(background=frame_background)
        
        b1 = tk.Button(frame, text="Create New Note")
        b1.config(background=button_background,
                  activebackground=button_background)
        b1.bind('<Button-1>', self.create_first_note)
        
        b2 = tk.Button(frame, text="Import Notes")
        b2.config(background=button_background,
                  activebackground=button_background)
        b2.bind('<Button-1>', self.import_files)
        
        for widget in (l1, b1, b2):
            widget.pack()
            
    def create_first_note(self, event:tk.Tk):
        """Create the first note of the program."""
        open_EditText()
        self.destroy()
        
    def import_files(self, event:tk.Tk):
        """Open a tkinter filedialog, choose files, and import them."""
        open_import_dialog(self, first_run=True)
        
        
class ScrollableNoteBoxView(tk.Frame):
    """The main view of the program, displays all notes.
    
    This view is created when the program loads and is hidden/shown when needed.
    The view consists of four layers:
    Layer 1: A frame that fills the entire window area.
    Layer 2: The grid contents. These include the canvas on which everything
             else is drawn, the scrollbar, and padding spaces.
    Layer 3: The frame(s) that structure the noteboxes.
    Layer 4: The notebox(es).
    
    Args:
        parent: Tkinter object that will contain the class.
        background (optional): Tkinter color (defined word, 6-digit hex, etc.)
                               for background.
    
    Attributes:
        frame_list (list): List of all frames on the drawing canvas.
        box_list (list): List of all boxes created, independent from frames.
        frame_width (int): Width of frames (same for all).
        num_frames (int): Number of frames, calculated at init and when window
                          size changes.
        max_width (int): Maximum width in pixels of text that a box can
                         display.
        max_lines (int): Maximum rows of text that a box can hold.
    
    """
    
    def __init__(self, parent:tk.Tk, background:str=main_background_color):
        """The constructor for ScrollableNoteBoxView class."""
        super().__init__(parent, background=background)
        self.frame_list = []
        self.box_list = []
        self.frame_width = 0
        
        self.pack(expand=True, fill='both')
        self.grid_rowconfigure(1, weight=1)
        self.grid_rowconfigure(0, minsize=gap//2)
        self.grid_rowconfigure(2, minsize=gap//2)
        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure(0, minsize=gap)
        self.grid_columnconfigure(2, minsize=gap)
        
        self.canvas = tk.Canvas(self, background=background, borderwidth=0,
                                highlightthickness=0)
        self.scrollbar = tk.Scrollbar(self, command=self.canvas.yview,
                                      background=background, width=3)
        self.new_button = tk.Button(self, text="+", padx=0,
                                    background=background,
                                    activebackground=background)
        self.import_button = tk.Button(self, text="\u2026", padx=0,
                                       background=background,
                                       activebackground=background)
        
        self.canvas.grid(row=1, column=1, sticky='nesw')
        self.scrollbar.grid(row=0, column=3, sticky='nesw', rowspan=3)
        self.canvas.config(yscrollcommand=self.scrollbar.set)
        
        self.new_button.bind('<Button-1>', self.new_note)
        self.import_button.bind('<Button-1>', self.import_files)
        self.canvas.bind_all('<Button-4>', self.on_mouse_wheel)
        self.canvas.bind_all('<Button-5>', self.on_mouse_wheel)
        self.bind('<Configure>', self.resize_window)
        
    def init(self):
        """Set up the view."""
        self.get_sizes()
        self.create_frames()
        self.create_boxes()
        self.display_all()
        self.place_buttons()
        self.lift_buttons()
        
    def new_note(self, event:tk.Tk):
        """Open an EditText window to create a new note."""
        open_EditText()
        
    def import_files(self, event:tk.Tk):
        """Open a tkinter filedialog, choose file(s) to import, and import them."""
        open_import_dialog(self)
        
    def on_mouse_wheel(self, event:tk.Tk):
        """Bind mouse wheel to scrolling."""
        self.canvas.yview_scroll(-1 if event.num == 4 else 1, 'units')
        
    def get_sizes(self):
        """Calculate sizes for the columns, noteboxes, and text."""
        root.update_idletasks()
        
        self.window_width = root.winfo_width()
        self.window_height = root.winfo_height()
        
        total_width = self.window_width - 2*gap - self.scrollbar.winfo_width()
        window_ratio = self.window_width / self.window_height
        
        self.num_frames = total_width // 300 + 1
        self.frame_width = (total_width + gap) // self.num_frames - gap
        
        self.max_width = int(self.frame_width * 0.95)
        self.max_lines = self.frame_width // window_ratio // \
                         font.metrics('linespace')
        if not self.max_lines:
            self.max_lines = 1
        
    def delete_frames(self):
        """Delete all frames on the canvas."""
        items = self.canvas.find_all()
        children = self.canvas.winfo_children()
        for index, child in enumerate(children):
            self.canvas.delete(items[index])
            child.destroy()
        self.frame_list.clear()

    def create_frames(self):
        """Create num_frames frames, do not place on canvas yet."""
        for frame in range(self.num_frames):
            frame = tk.Frame(self.canvas, width=self.frame_width,
                             background=main_background_color)
            frame.height = 0
            self.frame_list.append(frame)
            frame.pack_propagate(0)

    def get_next_frame(self, frames:List[tk.Tk]) -> tk.Tk:
        """Return the next (shortest) frame that a notebox should be added to."""
        shortest = min(frame.height for frame in frames)
        return next(frame for frame in frames if frame.height == shortest)
        
    def get_list_index(self, obj:tk.Tk) -> int:
        """Return the index of the notebox in root's box_list."""
        return next((index for index, box in enumerate(self.box_list)
                     if box is obj), None)
    
    def create_boxes(self):
        """Create a notebox for each note in the stored folder."""
        for note in get_notes():
            notebox = self.create_box(note, self.max_width, self.max_lines)
            self.assign_box(notebox)
            
    def create_box(self, path:str=None, width:int=0, lines:int=1,
                   new:bool=False) -> tk.Tk:
        """Create and return a notebox and place it into root's box_list."""
        notebox = NoteBox(self, path=path, width=width, lines=lines)
        if new:
            self.box_list.insert(0, notebox)
        else:
            self.box_list.append(notebox)
        return notebox
        
    def assign_box(self, box:tk.Tk):
        """Pack a notebox into the next available frame."""
        frame = self.get_next_frame(self.frame_list)
        box.pack(in_=frame, fill='x', pady=(gap//2))
        frame.height += box.height + gap
            
    def reassign_boxes(self):
        """Repack all the boxes into the frames."""
        for notebox in self.box_list:
            self.assign_box(notebox)
            
    def insert_box(self, index:int, notebox:tk.Tk):
        """Place a notebox into root's box_list at index."""
        self.box_list.insert(index, notebox)
                
    def remove_box(self, notebox:tk.Tk, from_button:bool=False):
        """Remove notebox from root's box_list, do not destroy the object."""
        index = self.get_list_index(notebox)
        if index is not None:
            del self.box_list[index]
        if from_button:
            if self.box_list:
                self.refresh_frames()
            else:
                startWelcome()
        
    def display_all(self):
        """Place and show all frames onto the canvas and update the scrollregion."""
        for index, frame in enumerate(self.frame_list):
            frame.config(height=frame.height)
            frame.tag = self.canvas.create_window(index*self.frame_width +
                                                  index*gap, 0, window=frame,
                                                  anchor='nw')
            #  self.canvas.update()
        self.canvas.config(scrollregion=self.canvas.bbox('all'))
        
    def resize_window(self, event:tk.Tk=None):
        """Recalculate sizes and move objects to new spaces."""
        try:
            current_num_frames = self.num_frames
        except:
            return
        
        self.place_buttons()
        self.get_sizes()
        if current_num_frames != self.num_frames:
            self.refresh_frames()
        self.resize_widgets()
        self.lift_buttons()
        
    def place_buttons(self):
        """Place 'new' and 'import' buttons on the bottom right corner."""
        import_button_x = self.window_width - self.scrollbar.winfo_width() - 2
        import_button_y = self.window_height - 2
        new_button_x = import_button_x - self.import_button.winfo_reqwidth() - 2
        new_button_y = import_button_y
        self.import_button.place(x=import_button_x, y=import_button_y,
                                 anchor='se')
        self.new_button.place(x=new_button_x, y=new_button_y, anchor='se')
        
    def refresh_frames(self):
        """Update the positions of the frames and noteboxes."""
        self.delete_frames()
        self.create_frames()
        self.reassign_boxes()
        self.display_all()
        
    def resize_widgets(self):
        """Update the frame widths and rewrap the notebox texts accordingly."""
        for index, frame in enumerate(self.frame_list):
            frame.config(width=self.frame_width)
            self.canvas.coords(frame.tag, index*self.frame_width + index*gap, 0)
        for notebox in self.box_list:
            notebox.wrap_text(self.max_width, self.max_lines)
            
    def lift_buttons(self):
        """Raise the 'new' and 'import' buttons to the top visible layer."""
        self.new_button.lift()
        self.import_button.lift()
        
        
class NoteBox(tk.Label):
    """Individual box that displays the note's text.
    
    The box's contents are read from a saved note file or imported via
    the filedialog. There are three components to each note: title,
    date created, and body text.
    Title (optional): This is the first line of the saved note file. If there
                      is no text, then the first line is blank.
    Date: This comes from the filename of the saved note file. If a note is
          imported from Google Keep, then it retains the original date. If a
          note is changed, then it is given a new date and saved with that
          new date. Modification date is more important than creation date.
          This means that the most recently modified notes will always
          appear first.
    Body Text: The actual note. Lines are stored with newlines in the saved
               file but are stripped of newlines when imported.
    
    There is always one box per note. Clicking on the box will open an EditText
    window to edit the note's text. During a window resizing event, boxes are
    not created or destroyed; their containing text is re-wrapped, and the
    boxes are reassigned to the frames to ensure proper stacking.
    
    Args:
        parent (obj): Tkinter object that will contain the class.
        path (str, optional): Absolute path to a note that the box will read in.
        width (int, optional): Maximum width in pixels of text that the box can
                               display. Usually comes from max_width in
                               ScrollableNoteBoxView.
        lines (int, optional): Maximum rows of text that the box can hold.
                               Usually comes from max_lines in
                               ScrollableNoteBoxView.
        background (str, optional): Tkinter color (defined word, 6-digit hex,
                                    etc.) for background.
    
    Attributes:
        parent (obj): Tkinter object that contains the box.
        path (str): Absolute path to the saved note's location on disk.
        title (str): Title of the note.
        text_lines (list): Lines of text as read from the note, stripped
                           of newlines.
        body_text (str): Full text of the note's body. Formed by joining
                         text_lines together with newlines.
        wrapped_text (str): Body text wrapped to correctly display in the box.
        height (int): Height of the box in pixels.
    
    """
    
    def __init__(self, parent:tk.Tk, path:str=None, width:int=0, lines:int=0,
                 background:str=box_color):
        """The constructor for NoteBox class."""
        super().__init__(parent, background=background, anchor='w',
                         justify='left', font=font, wrap=None)
        self.parent = parent
        self.path = path
        self.bind('<Button-1>', self.on_click)
        self.bind('<Button-3>', self.on_click_delete)
        #  self.getFontSize()
        
        self.title = ""
        self.text_lines = []
        self.body_text = ""
        self.height = self.winfo_reqheight()
        
        if path:
            self.read_note(path)
            self.wrap_text(width, lines)
        
    def on_click(self, event:tk.Tk):
        """Open a new EditText view when a notebox is clicked."""
        open_EditText(event.widget)
    
    def on_click_delete(self, event:tk.Tk):
        """Open a confirmation dialog and delete (or not) the clicked notebox"""
        choice = messagebox.askyesno("Confirm...", "Delete note?")
        if choice:
            self.delete_note(from_button=True)
            
    def read_note(self, path:str):
        """Set the notebox object's path, title, and body texts from the saved file."""
        self.path = path
        fp = open(path, 'r')
        self.title = fp.readline()[:-1]
        self.set_text(fp.readlines())
        fp.close()
        
    def set_text(self, lines:List[str]):
        """Format the text and set the notebox's text_lines and body_text."""
        self.text_lines = [re.split('\n', line)[0] for line in lines]
        self.body_text = '\n'.join(self.text_lines)
        
    def wrap_text(self, width:int, max_lines:int):
        """Wrap text within label according to max width and max line count."""
        wrap_count = 0
        wrap_list = []
        non_blank_regex = re.compile('\S')
        num_lines = len(self.text_lines)
        for line in self.text_lines:
            while line and wrap_count < max_lines and \
                  non_blank_regex.search(line):
                index = self.get_max_index(line, width)
                if index != len(line) and wrap_count < max_lines - 1:
                    index = self.get_wrap_index(line, index)
                wrap_list.append(line[:index])
                line = line[index + 1:]
                wrap_count += 1
            if wrap_count == max_lines:
                if non_blank_regex.search(line) or index < num_lines:
                    wrap_list[-1] = wrap_list[-1][:-2] + '\u2026'
                break
        self.wrapped_text = '\n'.join(wrap_list)
        self.display_text(self.wrapped_text)
            
    def get_max_index(self, line:str, width:int) -> int:
        """Calculate longest possible line according to maximum width of label."""
        line_width = font.measure(line)
        if line_width < width:
            return len(line)
        index = int(width * len(line) // line_width)
        while font.measure(line[:index]) < width:
            index += 1
        while font.measure(line[:index]) > width:
            index -= 1
        return index
    
    def get_wrap_index(self, line:str, index:int) -> int:
        """Find most recent blank space to break line."""
        # TODO handle word is too long to wrap, must truncate
        start = index
        while line[index] != ' ':
            index -= 1
            if index <= 0:
                return start
        return index
        
    def display_text(self, text:str):
        """Change the notebox's displayed text."""
        self.config(text=text)
        self.height = self.winfo_reqheight()
        
    def get_new_date(self) -> str:
        """Return the formatted date according to the current time and date."""
        current_time = time.localtime()
        return "{}-{:02}-{:02}T{:02}_{:02}_{:02}.note".\
                format(*current_time[0:6])
    
    def delete_note(self, from_button:bool=False):
        """Delete saved note file from disk and remove notebox from window."""
        if self.path:
            os.remove(self.path)
        self.parent.remove_box(self, from_button=from_button)
        
    def save_note(self, filename:str):
        """Save notebox contents to disk."""
        self.path = os.path.join(notes_dir, filename)
        fp = open(self.path, 'w+')
        fp.write('\n'.join([self.title, self.body_text]))
        fp.close()
        
    def update_note(self, filename:str):
        """Rename saved file to new date, move notebox to top of list, rewrap text."""
        self.delete_note()
        self.save_note(filename)
        self.parent.insert_box(0, self)
        self.wrap_text(self.parent.max_width, self.parent.max_lines)
        
        
class EditText(tk.Frame):
    """Editor window to edit a note's title and body.
    
    Args:
        parent (obj): Tkinter object that will contain the class.
        notebox (int): Notebox that will be edited.
        
    """
    
    def __init__(self, parent:tk.Tk, notebox:tk.Tk):
        """The constructor for EditText class."""
        super().__init__(parent)
        self.pack(expand=True, fill='both', side='top')
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        self.back = tk.Label(self, text='\u2190',
                             background=main_background_color)
        self.title = tk.Entry(self, background=box_color, font=font)
        self.text = tk.Text(self, wrap='word', background=box_color,
                            font=font, undo=True)
        self.scrollbar = tk.Scrollbar(self, command=self.text.yview,
                                      background=box_color, width=3)
        
        if notebox is None:
            self.new = True
        else:
            self.new = False
            self.load_note(notebox)
        
        self.back.grid(row=0, column=0, sticky='ns')
        self.title.grid(row=0, column=1, columnspan=2, sticky='we')
        self.text.grid(row=1, column=0, columnspan=2, sticky='nesw')
        self.scrollbar.grid(row=1, column=2, sticky='ns')
        self.text.config(yscrollcommand=self.scrollbar.set)
        
        self.bind_keys()
        
    def load_note(self, notebox:tk.Tk):
        """Load the contents of the selected notebox."""
        self.notebox = notebox
        self.title.insert('end', self.notebox.title)
        self.text.insert('end', self.notebox.body_text)
        
    def bind_keys(self):
        """Bind the back button to close when clicked and the escape to close."""
        self.back.bind('<Button-1>', self.close_frame)
        self.bind_all('<Escape>', self.close_frame)
            
    def close_frame(self, event:tk.Tk):
        """Destroy the view from the window, show the main ScrollableNoteBoxView."""
        self.close_note()
        root.main_view.refresh_frames()
        root.main_view.pack(expand=True, fill='both')
        self.unbind_all('<Escape>')
        self.destroy()
        
    def close_note(self):
        """If the note was changed, save the changes."""
        title = self.title.get()
        body = self.text.get(1.0, 'end-1c')
        if not title and not body:
            return
        if self.new:
            self.notebox = root.main_view.create_box(new=True)
            self.notebox.title = ""
            self.notebox.body_text = ""
        if title != self.notebox.title or body != self.notebox.body_text:
            filename = self.notebox.get_new_date()
            
            self.notebox.title = title
            self.notebox.body_text = body
            self.notebox.text_lines = [line for line in body.split('\n')]
            
            self.notebox.update_note(filename)
        
        
def get_notes() -> List[str]:
    """Return a list of all notes, sorted by most recent first."""
    return sorted(glob.glob(os.path.join(notes_dir, '*.note')), reverse=True)

def open_EditText(notebox:tk.Tk=None):
    """Create an EditText view and hide the main ScrollableNoteBoxView."""
    root.main_view.pack_forget()
    EditText(root, notebox=notebox)
    
def open_import_dialog(window:tk.Tk, first_run:bool=False):
    """Create and display a tkinter filedialog, import selected notes."""
    notes = filedialog.askopenfilenames(initialdir=os.path.expanduser\
                                        ('~/Downloads/Takeout/Keep'),
                                        filetypes=(("HTML files", '*.html'),
                                        ("All files", '*.*')),
                                        title="Choose note(s) to import")
    if notes:
        import_notes(notes, first_run)
        if first_run:
            root.main_view.pack(expand=True, fill='both')
            root.main_view.init()
            window.destroy()

def check_for_directory():
    """If note folder does not exist, create it with 700 permission."""
    if not os.path.isdir(notes_dir):
        os.mkdir(notes_dir, mode=0o700)

def import_notes(html_list:List[str], first_run:bool=False):
    """Import all html files in html_list, save to disk, and create noteboxes."""
    root.main_view.get_sizes()
    new_boxes = []
    for html_file in html_list:
        if html_file[-4:] != 'html':
            continue
        
        fp = open(html_file)
        soup = bs4.BeautifulSoup(fp, 'html.parser')
        
        notebox = NoteBox(root.main_view, width=root.main_view.max_width,
                          lines=root.main_view.max_lines)
        new_boxes.append(notebox)
        
        notebox.title = get_title(soup)
        filename = get_filename(soup, html_file, notebox, first_run)
        
        text = str(soup.find_all('div', class_='content')[0])
        lines = text[21:-6].split('<br/>')
        notebox.set_text(lines)
        notebox.wrap_text(root.main_view.max_width, root.main_view.max_lines)
        
        notebox.save_note(filename)
    root.main_view.box_list = new_boxes + root.main_view.box_list
    root.main_view.refresh_frames()
                
def get_title(soup:bs4.BeautifulSoup) -> str:
    """Return the title of the note, or an empty string if none."""
    pattern = re.compile('[JFMASOND][aepuco][nbrylgptvc] \d\d?, \d\d\d\d, \d[012]?:\d\d:\d\d [AP]M')
    soup_string = soup.title.string
    if not pattern.match(soup_string):
        # note has a title
        return soup_string
    else:
        # note does not have a title
        return ""
    
def get_filename(soup:bs4.BeautifulSoup, path:str, notebox:tk.Tk, first_run:bool) -> str:
    """Return the new filename for the note, which is equal to its creation date."""
    pattern = re.compile('[JFMASOND][aepuco][nbrylgptvc] \d\d?, \d\d\d\d, \d[012]?:\d\d:\d\d [AP]M')
    if not pattern.match(soup.title.string) and first_run:
        heading = str(soup.find_all('div', class_='heading')[0])
        return process_date(pattern.search(heading).group())
    elif first_run:
        return os.path.basename(path)[:-15] + '.note'
    else:
        return notebox.get_new_date()
        
def process_date(date:str) -> str:
    """Convert a date string into a date/filename string, return it."""
    months = {'Jan': '01', 'Feb': '02', 'Mar': '03', 'Apr': '04',
              'May': '05', 'Jun': '06', 'Jul': '07', 'Aug': '08',
              'Sep': '09', 'Oct': '10', 'Nov': '11', 'Dec': '12'}
    
    year = re.search('\d\d\d\d', date).group()
    month = months[date[0:3]]
    day = int(re.search('\d\d?(?=,)', date).group())
    hour = int(re.search('(?<= )\d\d?(?=:)', date).group())
    minute = int(re.search('(?<=:)\d\d(?=:)', date).group())
    second = int(re.search('(?<=:)\d\d(?= )', date).group())
    
    daytime_bool = re.search('AM', date)
    if not daytime_bool:
        hour = hour + 12
    
    return "{}-{}-{:02}T{:02}_{:02}_{:02}.note".format(year,
                                                       month,
                                                       day,
                                                       hour,
                                                       minute,
                                                       second)
    
def save_window_dimensions():
    """Write the formatted window dimensions to disk."""
    path = os.path.join(main_dir, 'win_size')
    fp = open(path, 'w+')
    fp.write("{}x{}".format(root.winfo_width(), root.winfo_height()))
    fp.close()
    
def read_window_dimensions():
    """Load previous session's window dimensions from disk and resize root window."""
    path = os.path.join(main_dir, 'win_size')
    if os.path.exists(path):
        fp = open(path, 'r')
        dimensions = fp.readline()
        fp.close()
        
        root.geometry(dimensions)
    
def on_close():
    """Save window dimensions, destroy root window, close program."""
    save_window_dimensions()
    root.destroy()
    
def main():
    """Main function."""
    read_window_dimensions()
    root.protocol("WM_DELETE_WINDOW", on_close)
    root.main_view = ScrollableNoteBoxView(root)
    if not get_notes():
        check_for_directory()
        root.main_view.pack_forget()
        FirstRunView(root)
    else:
        root.main_view.init()
    root.mainloop()

if __name__ == '__main__':
    main()
