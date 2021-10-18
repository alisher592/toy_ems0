from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class FileModifiedHandler(FileSystemEventHandler):

    def __init__(self, path, file_name, callback):
        self.file_name = file_name
        self.callback = callback

        # set observer to watch for changes in the directory
        self.observer = Observer()
        self.observer.schedule(self, path, recursive=False)
        self.observer.start()
        self.observer.join()

    def on_modified(self, event): 
        # only act on the change that we're looking for
        if not event.is_directory and event.src_path.endswith(self.file_name):
            self.observer.stop() # stop watching
            self.callback() # call callback


from sys import argv, exit

if __name__ == '__main__':

    if not len(argv) == 2:
        print("No file specified")
        exit(1)

    def callback():
        print("FILE WAS MODIFED")

    FileModifiedHandler('.', argv[1], callback)