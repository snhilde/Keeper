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

notes_dir = os.path.expanduser('~/.local/share/keeper/notes')
root = tk.Tk()
root.title("Keeper")
font = tkfont.Font()
main_background_color = '#E6E6E6'
box_color = '#FAFAFA'
gap = 10


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
        open_EditText()
        self.destroy()
        
    def import_files(self, event:tk.Tk):
        open_import_dialog(self, first_run=True)
        
        
class ScrollableNoteBoxView(tk.Frame):
    """The main view of the program, displays all notes.
    
    This view is created when the program loads and hidden/shown when needed.
    
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
        self.get_sizes()
        self.create_frames()
        self.create_boxes()
        self.display_all()
        self.place_buttons()
        self.lift_buttons()
        
    def new_note(self, event:tk.Tk):
        open_EditText()
        
    def import_files(self, event:tk.Tk):
        open_import_dialog(self)
        
    def on_mouse_wheel(self, event:tk.Tk):
        self.canvas.yview_scroll(-1 if event.num == 4 else 1, 'units')
        
    def get_sizes(self):
        root.update_idletasks()
        
        total_width = root.winfo_width() - 2*gap - self.scrollbar.winfo_width()
        window_ratio = root.winfo_width() / root.winfo_height()
        
        self.num_frames = total_width // 300 + 1
        self.frame_width = (total_width + gap) // self.num_frames - gap
        
        self.max_width = int(self.frame_width * 0.95)
        self.max_lines = self.frame_width // window_ratio // \
                         font.metrics('linespace')
        if not self.max_lines:
            self.max_lines = 1
        
    def delete_frames(self):
        items = self.canvas.find_all()
        children = self.canvas.winfo_children()
        for index, child in enumerate(children):
            self.canvas.delete(items[index])
            child.destroy()
        self.frame_list.clear()

    def create_frames(self):
        for frame in range(self.num_frames):
            frame = tk.Frame(self.canvas, width=self.frame_width,
                             background=main_background_color)
            frame.height = 0
            self.frame_list.append(frame)
            frame.pack_propagate(0)

    def get_next_frame(self, frames:List[tk.Tk]) -> tk.Tk:
        smallest = min(frame.height for frame in frames)
        return next(frame for frame in frames if frame.height == smallest)
        
    def get_list_index(self, obj:tk.Tk) -> int:
        return next((index for index, box in enumerate(self.box_list)
                     if box is obj), None)
    
    def create_boxes(self):
        for note in get_notes():
            notebox = self.create_box(note, self.max_width, self.max_lines)
            self.assign_box(notebox)
            
    def create_box(self, path:str=None, width:int=0, lines:int=1,
                   new:bool=False) -> tk.Tk:
        notebox = NoteBox(self, path=path, width=width, lines=lines)
        if new:
            self.box_list.insert(0, notebox)
        else:
            self.box_list.append(notebox)
        return notebox
        
    def assign_box(self, box:tk.Tk):
        frame = self.get_next_frame(self.frame_list)
        box.pack(in_=frame, fill='x', pady=(gap//2))
        frame.height += box.height + gap
            
    def reassign_boxes(self):
        for notebox in self.box_list:
            self.assign_box(notebox)
            
    def insert_box(self, index:int, notebox:tk.Tk):
        self.box_list.insert(index, notebox)
                
    def remove_box(self, notebox:tk.Tk, from_button:bool=False):
        index = self.get_list_index(notebox)
        if index is not None:
            del self.box_list[index]
        if from_button:
            if self.box_list:
                self.refresh_frames()
            else:
                startWelcome()
        
    def display_all(self):
        for index, frame in enumerate(self.frame_list):
            frame.config(height=frame.height)
            frame.tag = self.canvas.create_window(index*self.frame_width +
                                                  index*gap, 0, window=frame,
                                                  anchor='nw')
            #  self.canvas.update()
        self.canvas.config(scrollregion=self.canvas.bbox('all'))
        
    def resize_window(self, event:tk.Tk=None):
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
        import_button_x = root.winfo_width() - self.scrollbar.winfo_width() - 2
        import_button_y = root.winfo_height() - 2
        new_button_x = import_button_x - self.import_button.winfo_reqwidth() - 2
        new_button_y = import_button_y
        self.import_button.place(x=import_button_x, y=import_button_y,
                                 anchor='se')
        self.new_button.place(x=new_button_x, y=new_button_y, anchor='se')
        
    def refresh_frames(self):
        self.delete_frames()
        self.create_frames()
        self.reassign_boxes()
        self.display_all()
        #  self.get_sizes()
        #  self.delete_frames()
        #  self.create_frames()
        #  self.resize_widgets()
        #  self.reassign_boxes()
        #  self.display_all()
        
    def resize_widgets(self):
        for index, frame in enumerate(self.frame_list):
            frame.config(width=self.frame_width)
            self.canvas.coords(frame.tag, index*self.frame_width + index*gap, 0)
        for notebox in self.box_list:
            notebox.wrap_text(self.max_width, self.max_lines)
            
    def lift_buttons(self):
        self.new_button.lift()
        self.import_button.lift()
        
        
class NoteBox(tk.Label):
    """Individual box that displays the note's text.
    
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
        open_EditText(event.widget)
    
    def on_click_delete(self, event:tk.Tk):
        choice = messagebox.askyesno("Confirm...", "Delete note?")
        if choice:
            self.delete_note(from_button=True)
            
    def read_note(self, path:str):
        self.path = path
        fp = open(path, 'r')
        self.title = fp.readline()[:-1]
        self.set_text(fp.readlines())
        fp.close()
        
    def set_text(self, lines:List[str]):
        self.text_lines = [re.split('\n', line)[0] for line in lines]
        self.body_text = '\n'.join(self.text_lines)
        
    def wrap_text(self, width:int, max_lines:int):
        "Wrap text within label according to max width and max line count"
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
        "Calculate longest possible line according to maximum width of label"
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
        "Find most recent blank space to break line"
        # TODO handle word is too long to wrap, must truncate
        start = index
        while line[index] != ' ':
            index -= 1
            if index <= 0:
                return start
        return index
        
    def display_text(self, text:str):
        self.config(text=text)
        self.height = self.winfo_reqheight()
        
    def get_new_date(self) -> str:
        current_time = time.localtime()
        return "{}-{:02}-{:02}T{:02}_{:02}_{:02}.note".\
                format(*current_time[0:6])
    
    def delete_note(self, from_button:bool=False):
        if self.path:
            os.remove(self.path)
        self.parent.remove_box(self, from_button=from_button)
        
    def save_note(self, filename:str):
        self.path = os.path.join(notes_dir, filename)
        fp = open(self.path, 'w+')
        fp.write('\n'.join([self.title, self.body_text]))
        fp.close()
        
    def update_note(self, filename:str):
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
        self.notebox = notebox
        self.title.insert('end', self.notebox.title)
        self.text.insert('end', self.notebox.body_text)
        
    def bind_keys(self):
        self.back.bind('<Button-1>', self.close_frame)
        self.bind_all('<Escape>', self.close_frame)
            
    def close_frame(self, event:tk.Tk):
        self.close_note()
        root.main_view.pack(expand=True, fill='both')
        self.unbind_all('<Escape>')
        self.destroy()
        
    def close_note(self):
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
        root.main_view.refresh_frames()
        
        
def get_notes() -> List[str]:
    return sorted(glob.glob(os.path.join(notes_dir, '*.note')), reverse=True)

def open_EditText(notebox:tk.Tk=None):
    root.main_view.pack_forget()
    EditText(root, notebox=notebox)
    
def open_import_dialog(window:tk.Tk, first_run:bool=False):
    notes = filedialog.askopenfilenames(initialdir=os.path.expanduser\
                                        ('~/Downloads/Takeout/Keep'),
                                        filetypes=(("HTML files", '*.html'),
                                        ("All files", '*.*')),
                                        title="Choose note(s) to import")
    if notes:
        import_notes(notes, first_run)
        if first_run:
            root.main_view.init()
            window.destroy()

def check_for_directory():
    if not os.path.isdir(notes_dir):
        os.mkdir(notes_dir, mode=0o700)

def import_notes(html_list:List[str], first_run:bool=False):
    root.main_view.get_sizes()
    new_boxes = []
    pattern = re.compile('[JFMASOND][aepuco][nbrylgptvc] \d\d?, \d\d\d\d, \d[012]?:\d\d:\d\d [AP]M')
    for html_file in html_list:
        if html_file[-4:] != 'html':
            continue
        
        notebox = NoteBox(root.main_view, width=root.main_view.max_width,
                          lines=root.main_view.max_lines)
        new_boxes.append(notebox)
        
        if first_run:
            filename = os.path.basename(html_file)[:-15]
        else:
            filename = notebox.get_new_date()
        
        fp = open(html_file)
        soup = bs4.BeautifulSoup(fp, 'html.parser')
        
        notebox.title = soup.title.string
        if not pattern.match(notebox.title):
            #  note has a title
            heading = str(soup.find_all('div', class_='heading')[0])
            if first_run:
                filename = process_date(pattern.search(heading).group())
        else:
            #  note does not have a title
            notebox.title = ""
            
        text = str(soup.find_all('div', class_='content')[0])
        lines = text[21:-6].split('<br/>')
        notebox.set_text(lines)
        notebox.wrap_text(root.main_view.max_width, root.main_view.max_lines)
        
        notebox.save_note(filename)
    root.main_view.box_list = new_boxes + root.main_view.box_list
    root.main_view.refresh_frames()
                
def process_date(date:str) -> str:
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
    
def main():
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
