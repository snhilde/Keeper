import glob
import tkinter as tk
from tkinter import filedialog
from tkinter import messagebox
from tkinter import font as tkfont
import bs4
import os
import re
import time

notesDir = os.path.expanduser('~/.local/share/keeper/notes')
root = tk.Tk()
root.title("Keeper")
font = tkfont.Font()
mainBackgroundColor = '#E6E6E6'
boxColor = '#FAFAFA'
gap = 10


class FirstRunView(tk.Frame):
    def __init__(self, parent, frameBackground=mainBackgroundColor, buttonBackground=boxColor):
        super().__init__(parent, background=frameBackground)
        root.minsize(root.winfo_width(), root.winfo_height())
        self.pack(expand=True, fill='both')
        
        frame = tk.Frame(self,background=frameBackground)
        frame.place(relx=0.5, rely=0.5, anchor='center')
        
        l1 = tk.Label(frame, text="Welcome to Keeper!\n")
        l1.config(background=frameBackground)
        
        b1 = tk.Button(frame, text="Create New Note")
        b1.config(background=buttonBackground, activebackground=buttonBackground)
        b1.bind('<Button-1>', self.create_first_note)
        
        b2 = tk.Button(frame, text="Import Notes")
        b2.config(background=buttonBackground, activebackground=buttonBackground)
        b2.bind('<Button-1>', self.import_files)
        
        for widget in (l1, b1, b2):
            widget.pack()
            
    def create_first_note(self, event):
        open_EditText()
        self.destroy()
        
    def import_files(self, event):
        open_import_dialog(self, firstBool=True)
        
        
class ScrollableNoteBoxView(tk.Frame):
    def __init__(self, parent, background=mainBackgroundColor, init=True):
        super().__init__(parent, background=background)
        self.frameList = []
        self.boxList = []
        self.frameWidth = 0
        
        self.pack(expand=True, fill='both')
        self.grid_rowconfigure(1, weight=1)
        self.grid_rowconfigure(0, minsize=gap//2)
        self.grid_rowconfigure(2, minsize=gap//2)
        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure(0, minsize=gap)
        self.grid_columnconfigure(2, minsize=gap)
        
        self.canvas = tk.Canvas(self, background=background, borderwidth=0, highlightthickness=0)
        self.scrollbar = tk.Scrollbar(self, command=self.canvas.yview, background=background, width=3)
        self.newButton = tk.Button(self, text="+", padx=0,
                background=background, activebackground=background)
        self.importButton = tk.Button(self, text="\u2026", padx=0,
                background=background, activebackground=background)
        
        self.canvas.grid(row=1, column=1, sticky='nesw')
        self.scrollbar.grid(row=0, column=3, sticky='nesw', rowspan=3)
        self.canvas.config(yscrollcommand=self.scrollbar.set)
        
        self.newButton.bind('<Button-1>', self.new_note)
        self.importButton.bind('<Button-1>', self.import_files)
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
        
    def new_note(self, event):
        open_EditText()
        
    def import_files(self, event):
        open_import_dialog(self)
        
    def on_mouse_wheel(self, event):
        self.canvas.yview_scroll(-1 if event.num == 4 else 1, 'units')
        
    def get_sizes(self):
        root.update_idletasks()
        totalWidth = root.winfo_width() - 2 * gap - self.scrollbar.winfo_width()
        self.numFrames = totalWidth // 300 + 1
        self.frameWidth = (totalWidth + gap) // self.numFrames - gap
        windowRatio = root.winfo_width() / root.winfo_height()
        
        self.maxWidth = int(self.frameWidth * 0.95)
        self.maxLines = self.frameWidth // windowRatio // font.metrics('linespace')
        if not self.maxLines:
            self.maxLines = 1
        
    def delete_frames(self):
        items = self.canvas.find_all()
        children = self.canvas.winfo_children()
        for index in range(len(children)):
            self.canvas.delete(items[index])
            children[index].destroy()
        self.frameList.clear()

    def create_frames(self):
        for frame in range(self.numFrames):
            frame = tk.Frame(self.canvas, width=self.frameWidth, background=mainBackgroundColor)
            frame.height = 0
            self.frameList.append(frame)
            frame.pack_propagate(0)

    def get_next_frame(self, frames):
        smallest = min(frame.height for frame in frames)
        return next(frame for frame in frames if frame.height == smallest)
        
    def get_list_index(self, obj):
        return next((index for index, box in enumerate(self.boxList) if box is obj), None)
    
    def create_boxes(self):
        for note in get_notes():
            noteBox = self.create_box(note, self.maxWidth, self.maxLines)
            self.assign_box(noteBox)
            
    def create_box(self, path=None, width=0, lines=1, new=False):
        noteBox = NoteBox(self, path=path, width=width, lines=lines)
        if new:
            self.boxList.insert(0, noteBox)
        else:
            self.boxList.append(noteBox)
        return noteBox
        
    def assign_box(self, box):
        frame = self.get_next_frame(self.frameList)
        box.pack(in_=frame, fill='x', pady=(gap//2))
        frame.height += box.height + gap
            
    def reassign_boxes(self):
        for noteBox in self.boxList:
            self.assign_box(noteBox)
            
    def insert_box(self, index, noteBox):
        self.boxList.insert(index, noteBox)
                
    def remove_box(self, noteBox, fromButtonBool=False):
        index = self.get_list_index(noteBox)
        if index is not None:
            del self.boxList[index]
        if fromButtonBool:
            if self.boxList:
                self.refresh()
            else:
                startWelcome()
        
    def display_all(self):
        for index, frame in enumerate(self.frameList):
            frame.config(height=frame.height)
            frame.tag = self.canvas.create_window(index*self.frameWidth + index*gap, 0,
                    window=frame, anchor='nw')
            #  self.canvas.update()
        self.canvas.config(scrollregion=self.canvas.bbox('all'))
        
    def resize_window(self, event=None):
        try:
            currFrames = self.numFrames
        except:
            return
        
        self.place_buttons()
        self.get_sizes()
        if currFrames != self.numFrames:
            self.refresh()
        self.resize_widgets()
        self.lift_buttons()
        
    def place_buttons(self):
        importX = root.winfo_width() - self.scrollbar.winfo_width() - 2
        importY = root.winfo_height() - 2
        self.importButton.place(x=importX, y=importY, anchor='se')
        self.newButton.place(x=importX-self.importButton.winfo_reqwidth()-2, y=importY, anchor='se')
        
    def refresh(self):
        self.delete_frames()
        self.create_frames()
        self.reassign_boxes()
        self.display_all()
        
    def resize_widgets(self):
        for index, frame in enumerate(self.frameList):
            frame.config(width=self.frameWidth)
            self.canvas.coords(frame.tag, index*self.frameWidth + index*gap, 0)
        for noteBox in self.boxList:
            noteBox.wrap_text(self.maxWidth, self.maxLines)
            
    def lift_buttons(self):
        self.newButton.lift()
        self.importButton.lift()
        
        
class NoteBox(tk.Label):
    def __init__(self, parent, path=None, width=0, lines=0, background=boxColor):
        super().__init__(parent, background=background, anchor='w', justify='left', font=font, wrap=None)
        self.parent = parent
        self.path = path
        self.bind('<Button-1>', self.on_click)
        self.bind('<Button-3>', self.on_click_delete)
        #  self.getFontSize()
        
        self.title = ""
        self.textLines = []
        self.bodyText = ""
        self.height = self.winfo_reqheight()
        
        if path:
            self.path = path
            self.read_note(path)
            self.wrap_text(width, lines)
        
    def on_click(self, event):
        open_EditText(root.mainView.get_list_index(event.widget))
    
    def on_click_delete(self, event):
        choice = messagebox.askyesno("Confirm...", "Delete note?")
        if choice:
            self.delete_note(fromButtonBool=True)
            
    def read_note(self, path):
        self.path = path
        fp = open(path, 'r')
        self.title = fp.readline()[:-1]
        self.set_text(fp.readlines())
        fp.close()
        
    def set_text(self, lines):
        newlineRegex = re.compile('\n')
        self.textLines = [newlineRegex.split(line)[0] for line in lines]
        self.bodyText = '\n'.join(self.textLines)
        
    def wrap_text(self, width, maxLines):
        "Wrap text within label according to maximum width and maximum line count of label"
        wrapCount = 0
        wrapList = []
        nonBlankRegex = re.compile('\S')
        numLines = len(self.textLines)
        for line in self.textLines:
            while line and wrapCount < maxLines and nonBlankRegex.search(line):
                index = self.get_max_index(line, width)
                if index != len(line) and wrapCount < maxLines - 1:
                    index = self.get_wrap_index(line, index)
                wrapList.append(line[:index])
                line = line[index + 1:]
                wrapCount += 1
            if wrapCount == maxLines:
                if nonBlankRegex.search(line) or index < numLines:
                    wrapList[-1] = wrapList[-1][:-2] + '\u2026'
                break
        self.wrappedText = '\n'.join(wrapList)
        self.display_text(self.wrappedText)
            
    def get_max_index(self, line, width):
        "Calculate longest possible line according to maximum width of label"
        lineWidth = font.measure(line)
        if lineWidth < width:
            return len(line)
        index = int(width * len(line) // lineWidth)
        while font.measure(line[:index]) < width:
            index += 1
        while font.measure(line[:index]) > width:
            index -= 1
        return index
    
    def get_wrap_index(self, line, index):
        "Find most recent blank space to break line"
        # TODO handle word is too long to wrap, must truncate
        start = index
        while line[index] != ' ':
            index -= 1
            if index <= 0:
                return start
        return index
        
    def display_text(self, text):
        self.config(text=text)
        self.height = self.winfo_reqheight()
        
    def get_new_date(self):
        currentTime = time.localtime()
        return "{}-{:02}-{:02}T{:02}_{:02}_{:02}.note".format(*currentTime[0:6])
    
    def delete_note(self, fromButtonBool=False):
        if self.path:
            os.remove(self.path)
        self.parent.remove_box(self, fromButtonBool=fromButtonBool)
        
    def save_note(self, filename):
        self.path = os.path.join(notesDir, filename)
        fp = open(self.path, 'w+')
        fp.write('\n'.join([self.title, self.bodyText]))
        fp.close()
        
    def update_note(self, filename):
        self.delete_note()
        self.save_note(filename)
        self.parent.insert_box(0, self)
        self.wrap_text(self.parent.maxWidth, self.parent.maxLines)
        
        
class EditText(tk.Frame):
    def __init__(self, parent, index):
        super().__init__(parent)
        self.pack(expand=True, fill='both', side='top')
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        self.back = tk.Label(self, text='\u2190', background=mainBackgroundColor)
        self.title = tk.Entry(self, background=boxColor, font=font)
        self.text = tk.Text(self, wrap='word', background=boxColor, font=font, undo=True)
        self.scrollbar = tk.Scrollbar(self, command=self.text.yview, background=boxColor, width=3)
        
        if index is None:
            self.new = True
        else:
            self.new = False
            self.load_note(index)
        
        self.back.grid(row=0, column=0, sticky='ns')
        self.title.grid(row=0, column=1, columnspan=2, sticky='we')
        self.text.grid(row=1, column=0, columnspan=2, sticky='nesw')
        self.scrollbar.grid(row=1, column=2, sticky='ns')
        self.text.config(yscrollcommand=self.scrollbar.set)
        
        self.bind_keys()
        
    def load_note(self, index):
        self.noteBox = root.mainView.boxList[index]
        self.title.insert('end', self.noteBox.title)
        self.text.insert('end', self.noteBox.bodyText)
        
    def bind_keys(self):
        self.back.bind('<Button-1>', self.close_frame)
        self.bind_all('<Escape>', self.close_frame)
            
    def close_frame(self, event):
        self.close_note()
        root.mainView.pack(expand=True, fill='both')
        self.unbind_all('<Escape>')
        self.destroy()
        
    def close_note(self):
        title = self.title.get()
        body = self.text.get(1.0, 'end-1c')
        if not title and not body:
            return
        if self.new:
            self.noteBox = root.mainView.create_box(new=True)
            self.noteBox.title = ""
            self.noteBox.bodyText = ""
        if title != self.noteBox.title or body != self.noteBox.bodyText:
            filename = self.noteBox.get_new_date()
            
            self.noteBox.title = title
            self.noteBox.bodyText = body
            self.noteBox.textLines = [line for line in body.split('\n')]
            
            self.noteBox.update_note(filename)
        root.mainView.refresh()
        
        
def get_notes():
    return sorted(glob.glob(os.path.join(notesDir, '*.note')), reverse=True)

def open_EditText(index=None):
    root.mainView.pack_forget()
    EditText(root, index=index)
    
def open_import_dialog(window, firstBool=False):
    notes = filedialog.askopenfilenames(initialdir=os.path.expanduser('~/Downloads/Takeout/Keep'),
                                        filetypes=(("HTML files", '*.html'), ("All files", '*.*')),
                                        title="Choose note(s) to import")
    if notes:
        import_notes(notes, firstBool)
        if firstBool:
            root.mainView.init()
            window.destroy()

def check_for_directory():
    if not os.path.isdir(notesDir):
        os.mkdir(notesDir, mode=0o700)

def import_notes(htmlList, firstBool=False):
    root.mainView.get_sizes()
    newBoxes = []
    pattern = re.compile('[JFMASOND][aepuco][nbrylgptvc] \d\d?, \d\d\d\d, \d[012]?:\d\d:\d\d [AP]M')
    for htmlFile in htmlList:
        if htmlFile[-4:] != 'html':
            continue
        
        noteBox = NoteBox(root.mainView, width=root.mainView.maxWidth, lines=root.mainView.maxLines)
        newBoxes.append(noteBox)
        
        if firstBool:
            filename = os.path.basename(htmlFile)[:-15]
        else:
            filename = noteBox.get_new_date()
        
        fp = open(htmlFile)
        soup = bs4.BeautifulSoup(fp, 'html.parser')
        
        noteBox.title = soup.title.string
        if not pattern.match(noteBox.title):
            #  note has a title
            heading = str(soup.find_all('div', class_='heading')[0])
            if firstBool:
                filename = process_date(pattern.search(heading).group())
        else:
            #  note does not have a title
            noteBox.title = ""
            
        text = str(soup.find_all('div', class_='content')[0])
        lines = text[21:-6].split('<br/>')
        noteBox.set_text(lines)
        noteBox.wrap_text(root.mainView.maxWidth, root.mainView.maxLines)
        
        noteBox.save_note(filename)
    root.mainView.boxList = newBoxes + root.mainView.boxList
    root.mainView.refresh()
                
def processDate(date):
    months = {'Jan': '01', 'Feb': '02', 'Mar': '03', 'Apr': '04', 'May': '05', 'Jun': '06',
                'Jul': '07', 'Aug': '08', 'Sep': '09', 'Oct': '10', 'Nov': '11', 'Dec': '12'}
    
    year = re.search('\d\d\d\d', date).group()
    month = months[date[0:3]]
    day = int(re.search('\d\d?(?=,)', date).group())
    hour = int(re.search('(?<= )\d\d?(?=:)', date).group())
    minute = int(re.search('(?<=:)\d\d(?=:)', date).group())
    second = int(re.search('(?<=:)\d\d(?= )', date).group())
    
    daytime = re.search('AM', date)
    
    return "{}-{}-{:02}T{:02}_{:02}_{:02}.note".format(year,
                                            month, 
                                            day,
                                            hour if daytime else hour + 12,
                                            minute,
                                            second)
    
def main():
    root.mainView = ScrollableNoteBoxView(root)
    if not get_notes():
        check_for_directory()
        root.mainView.pack_forget()
        FirstRunView(root)
    else:
        root.mainView.init()
    root.mainloop()

if __name__ == '__main__':
    main()
