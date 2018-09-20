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
        b1.bind('<Button-1>', self.createFirstNote)
        
        b2 = tk.Button(frame, text="Import Notes")
        b2.config(background=buttonBackground, activebackground=buttonBackground)
        b2.bind('<Button-1>', self.importFiles)
        
        for widget in (l1, b1, b2):
            widget.pack()
            
    def createFirstNote(self, event):
        openEditText()
        self.destroy()
        
    def importFiles(self, event):
        openImportDialog(self, firstBool=True)
        
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
        
        self.newButton.bind('<Button-1>', self.newNote)
        self.importButton.bind('<Button-1>', self.importFiles)
        self.canvas.bind_all('<Button-4>', self.onMouseWheel)
        self.canvas.bind_all('<Button-5>', self.onMouseWheel)
        self.bind('<Configure>', self.resizeWindow)
        
    def init(self):
        self.getSizes()
        self.createFrames()
        self.createBoxes()
        self.displayAll()
        self.placeButtons()
        self.liftButtons()
        
    def newNote(self, event):
        openEditText()
        
    def importFiles(self, event):
        openImportDialog(self)
        
    def onMouseWheel(self, event):
        self.canvas.yview_scroll(-1 if event.num == 4 else 1, 'units')
        
    def getSizes(self):
        root.update_idletasks()
        totalWidth = root.winfo_width() - 2 * gap - self.scrollbar.winfo_width()
        self.numFrames = totalWidth // 300 + 1
        self.frameWidth = (totalWidth + gap) // self.numFrames - gap
        windowRatio = root.winfo_width() / root.winfo_height()
        
        self.maxWidth = int(self.frameWidth * 0.95)
        self.maxLines = self.frameWidth // windowRatio // font.metrics('linespace')
        if not self.maxLines:
            self.maxLines = 1
        
    def deleteFrames(self):
        items = self.canvas.find_all()
        children = self.canvas.winfo_children()
        for index in range(len(children)):
            self.canvas.delete(items[index])
            children[index].destroy()
        self.frameList.clear()

    def createFrames(self):
        for frame in range(self.numFrames):
            frame = tk.Frame(self.canvas, width=self.frameWidth, background=mainBackgroundColor)
            frame.height = 0
            self.frameList.append(frame)
            frame.pack_propagate(0)

    def getNextFrame(self, frames):
        smallest = min(frame.height for frame in frames)
        return next(frame for frame in frames if frame.height == smallest)
        
    def getListIndex(self, obj):
        return next((index for index, box in enumerate(self.boxList) if box is obj), None)
    
    def createBoxes(self):
        for note in getNotes():
            noteBox = self.createBox(note, self.maxWidth, self.maxLines)
            self.assignBox(noteBox)
            
    def createBox(self, path=None, width=0, lines=1, new=False):
        noteBox = NoteBox(self, path=path, width=width, lines=lines)
        if new:
            self.boxList.insert(0, noteBox)
        else:
            self.boxList.append(noteBox)
        return noteBox
        
    def assignBox(self, box):
        frame = self.getNextFrame(self.frameList)
        box.pack(in_=frame, fill='x', pady=(gap//2))
        frame.height += box.height + gap
            
    def reassignBoxes(self):
        for noteBox in self.boxList:
            self.assignBox(noteBox)
            
    def insertBox(self, index, noteBox):
        self.boxList.insert(index, noteBox)
                
    def removeBox(self, noteBox, fromButtonBool=False):
        index = self.getListIndex(noteBox)
        if index is not None:
            del self.boxList[index]
        if fromButtonBool:
            if self.boxList:
                self.refresh()
            else:
                startWelcome()
        
    def displayAll(self):
        for index, frame in enumerate(self.frameList):
            frame.config(height=frame.height)
            frame.tag = self.canvas.create_window(index*self.frameWidth + index*gap, 0,
                    window=frame, anchor='nw')
            #  self.canvas.update()
        self.canvas.config(scrollregion=self.canvas.bbox('all'))
        
    def resizeWindow(self, event=None):
        try:
            currFrames = self.numFrames
        except:
            return
        
        self.placeButtons()
        self.getSizes()
        if currFrames != self.numFrames:
            self.refresh()
        self.resizeWidgets()
        self.liftButtons()
        
    def placeButtons(self):
        importX = root.winfo_width() - self.scrollbar.winfo_width() - 2
        importY = root.winfo_height() - 2
        self.importButton.place(x=importX, y=importY, anchor='se')
        self.newButton.place(x=importX-self.importButton.winfo_reqwidth()-2, y=importY, anchor='se')
        
    def refresh(self):
        self.deleteFrames()
        self.createFrames()
        self.reassignBoxes()
        self.displayAll()
        
    def resizeWidgets(self):
        for index, frame in enumerate(self.frameList):
            frame.config(width=self.frameWidth)
            self.canvas.coords(frame.tag, index*self.frameWidth + index*gap, 0)
        for noteBox in self.boxList:
            noteBox.wrapText(self.maxWidth, self.maxLines)
            
    def liftButtons(self):
        self.newButton.lift()
        self.importButton.lift()
        
class NoteBox(tk.Label):
    def __init__(self, parent, path=None, width=0, lines=0, background=boxColor):
        super().__init__(parent, background=background, anchor='w', justify='left', font=font, wrap=None)
        self.parent = parent
        self.path = path
        self.bind('<Button-1>', self.onClick)
        self.bind('<Button-3>', self.onClickDelete)
        #  self.getFontSize()
        
        self.title = ""
        self.textLines = []
        self.bodyText = ""
        self.height = self.winfo_reqheight()
        
        if path:
            self.path = path
            self.readNote(path)
            self.wrapText(width, lines)
        
    def onClick(self, event):
        openEditText(root.mainView.getListIndex(event.widget))
    
    def onClickDelete(self, event):
        choice = messagebox.askyesno("Confirm...", "Delete note?")
        if choice:
            self.deleteNote(fromButtonBool=True)
            
    def readNote(self, path):
        self.path = path
        fp = open(path, 'r')
        self.title = fp.readline()[:-1]
        self.setText(fp.readlines())
        fp.close()
        
    def setText(self, lines):
        newlineRegex = re.compile('\n')
        self.textLines = [newlineRegex.split(line)[0] for line in lines]
        self.bodyText = '\n'.join(self.textLines)
        
    def wrapText(self, width, maxLines):
        "Wrap text within label according to maximum width and maximum line count of label"
        wrapCount = 0
        wrapList = []
        nonBlankRegex = re.compile('\S')
        numLines = len(self.textLines)
        for line in self.textLines:
            while line and wrapCount < maxLines and nonBlankRegex.search(line):
                index = self.getMaxIndex(line, width)
                if index != len(line) and wrapCount < maxLines - 1:
                    index = self.getWrapIndex(line, index)
                wrapList.append(line[:index])
                line = line[index + 1:]
                wrapCount += 1
            if wrapCount == maxLines:
                if nonBlankRegex.search(line) or index < numLines:
                    wrapList[-1] = wrapList[-1][:-2] + '\u2026'
                break
        self.wrappedText = '\n'.join(wrapList)
        self.displayText(self.wrappedText)
            
    def getMaxIndex(self, line, width):
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
    
    def getWrapIndex(self, line, index):
        "Find most recent blank space to break line"
        # TODO handle word is too long to wrap, must truncate
        start = index
        while line[index] != ' ':
            index -= 1
            if index <= 0:
                return start
        return index
        
    def displayText(self, text):
        self.config(text=text)
        self.height = self.winfo_reqheight()
        
    def getNewDate(self):
        currentTime = time.localtime()
        return "{}-{:02}-{:02}T{:02}_{:02}_{:02}.note".format(*currentTime[0:6])
    
    def deleteNote(self, fromButtonBool=False):
        if self.path:
            os.remove(self.path)
        self.parent.removeBox(self, fromButtonBool=fromButtonBool)
        
    def saveNote(self, filename):
        self.path = os.path.join(notesDir, filename)
        fp = open(self.path, 'w+')
        fp.write('\n'.join([self.title, self.bodyText]))
        fp.close()
        
    def updateNote(self, filename):
        self.deleteNote()
        self.saveNote(filename)
        self.parent.insertBox(0, self)
        self.wrapText(self.parent.maxWidth, self.parent.maxLines)
        
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
            self.loadNote(index)
        
        self.back.grid(row=0, column=0, sticky='ns')
        self.title.grid(row=0, column=1, columnspan=2, sticky='we')
        self.text.grid(row=1, column=0, columnspan=2, sticky='nesw')
        self.scrollbar.grid(row=1, column=2, sticky='ns')
        self.text.config(yscrollcommand=self.scrollbar.set)
        
        self.bindKeys()
        
    def loadNote(self, index):
        self.noteBox = root.mainView.boxList[index]
        self.title.insert('end', self.noteBox.title)
        self.text.insert('end', self.noteBox.bodyText)
        
    def bindKeys(self):
        self.back.bind('<Button-1>', self.closeFrame)
        self.bind_all('<Escape>', self.closeFrame)
            
    def closeFrame(self, event):
        self.closeNote()
        root.mainView.pack(expand=True, fill='both')
        self.unbind_all('<Escape>')
        self.destroy()
        
    def closeNote(self):
        title = self.title.get()
        body = self.text.get(1.0, 'end-1c')
        if not title and not body:
            return
        if self.new:
            self.noteBox = root.mainView.createBox(new=True)
            self.noteBox.title = ""
            self.noteBox.bodyText = ""
        if title != self.noteBox.title or body != self.noteBox.bodyText:
            filename = self.noteBox.getNewDate()
            
            self.noteBox.title = title
            self.noteBox.bodyText = body
            self.noteBox.textLines = [line for line in body.split('\n')]
            
            self.noteBox.updateNote(filename)
        root.mainView.refresh()
        
def getNotes():
    return sorted(glob.glob(os.path.join(notesDir, '*.note')), reverse=True)

def openEditText(index=None):
    root.mainView.pack_forget()
    EditText(root, index=index)
    
def openImportDialog(window, firstBool=False):
    notes = filedialog.askopenfilenames(initialdir=os.path.expanduser('~/Downloads/Takeout/Keep'),
                                        filetypes=(("HTML files", '*.html'), ("All files", '*.*')),
                                        title="Choose note(s) to import")
    if notes:
        importNotes(notes, firstBool)
        if firstBool:
            root.mainView.init()
            window.destroy()

def checkForDir():
    if not os.path.isdir(notesDir):
        os.mkdir(notesDir, mode=0o700)

def importNotes(htmlList, firstBool=False):
    root.mainView.getSizes()
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
            filename = noteBox.getNewDate()
        
        fp = open(htmlFile)
        soup = bs4.BeautifulSoup(fp, 'html.parser')
        
        noteBox.title = soup.title.string
        if not pattern.match(noteBox.title):
            #  note has a title
            heading = str(soup.find_all('div', class_='heading')[0])
            if firstBool:
                filename = processDate(pattern.search(heading).group())
        else:
            #  note does not have a title
            noteBox.title = ""
            
        text = str(soup.find_all('div', class_='content')[0])
        lines = text[21:-6].split('<br/>')
        noteBox.setText(lines)
        noteBox.wrapText(root.mainView.maxWidth, root.mainView.maxLines)
        
        noteBox.saveNote(filename)
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
    if not getNotes():
        checkForDir()
        root.mainView.pack_forget()
        FirstRunView(root)
    else:
        root.mainView.init()
    root.mainloop()

if __name__ == '__main__':
    main()
