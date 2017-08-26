from traceback import print_exc
from app import App

def run():
    app = App()
    app.begin()

if __name__ == '__main__':
    try:
        run()
    except:
        print_exc()
        print ''
        raw_input("Press enter to quit...")
