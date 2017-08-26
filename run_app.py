import traceback
from app import App

def run():
    app = App()
    app.begin()

if __name__ == '__main__':
    try:
        run()
    except:
        traceback.print_exc()
        print ''
        raw_input("Press enter to quit...")
    # stdout.write('\nExiting...\n')
