from utils import *
from environment import *
from checkpoint import *

main_menu_text = """



  __  __ _      __     ___      _               _   _____         _      ____           _            
 |  \/  | |     \ \   / (_)_ __| |_ _   _  __ _| | |_   _|__  ___| |_   / ___|___ _ __ | |_ ___ _ __ 
 | |\/| | |      \ \ / /| | '__| __| | | |/ _` | |   | |/ _ \/ __| __| | |   / _ \ '_ \| __/ _ \ '__|
 | |  | | |___    \ V / | | |  | |_| |_| | (_| | |   | |  __/\__ \ |_  | |__|  __/ | | | ||  __/ |   
 |_|  |_|_____|    \_/  |_|_|   \__|\__,_|\__,_|_|   |_|\___||___/\__|  \____\___|_| |_|\__\___|_|   
                                                                                                     
 ________________________________________________________
|                                                        |
|                        ML IT                           |
|________________________________________________________|
|                                                        |
|                   Select an option                     |
|________________________________________________________|
|                                                        |
|  1: Show Virtual Machines                              |
|  2: Create Virtual Machine                             |
|  3: Create Test Environment                            |
|  4: Manage Configurations                              |
|  5: Delete Virtual Machine                             |
|  6: Manage Checkpoints                                 |
|                                                        | 
|  7: Exit                                               |
|                                                        |
|________________________________________________________|
"""

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def main_menu():
    print(main_menu_text)

def user_option():
    try:
        option = int(input("Enter your choice: "))
        if option < 1 or option > 8:
            raise ValueError
        return option
    except ValueError:
        print("Invalid input. Please enter a number between 1 and 8.")
        return user_option()

def main():
    main_menu()
    while True:
        option = user_option()
        if option == 1:
            list_vm()
            pause()
        elif option == 2:
            list_vm()
            create_one_vm()
            list_vm()
            pause()
        elif option == 3:
            start_environment()
            pause()
        elif option == 4:
            selected_vm = select()
            if selected_vm == None:
                clear_screen()
                main()
            vm_status = check_vm_status(selected_vm)
            change_configuration(selected_vm, vm_status)
        elif option == 5:
            while True:  # Loop for removing VMs
                selected_vm = select()
                if selected_vm == None:
                    clear_screen()
                    main()
                vm_status = check_vm_status(selected_vm)
                remove_vm(selected_vm, vm_status)
                pause()
        elif option == 6:
            selected_vm = select()
            if selected_vm == None:
                clear_screen()
                main()
            manage_vm_checkpoints(selected_vm)
            pause()
        elif option == 7:
            exit_menu()
            exit()

        main_menu()  # Show main menu again

if __name__ == "__main__":
    clear_screen()
    main()
