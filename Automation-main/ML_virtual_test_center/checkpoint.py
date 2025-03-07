from utils import *

def manage_vm_checkpoints_menu(vm_name):
    print(f"""
          
  __  __ _      __     ___      _               _   _____         _      ____           _            
 |  \/  | |     \ \   / (_)_ __| |_ _   _  __ _| | |_   _|__  ___| |_   / ___|___ _ __ | |_ ___ _ __ 
 | |\/| | |      \ \ / /| | '__| __| | | |/ _` | |   | |/ _ \/ __| __| | |   / _ \ '_ \| __/ _ \ '__|
 | |  | | |___    \ V / | | |  | |_| |_| | (_| | |   | |  __/\__ \ |_  | |__|  __/ | | | ||  __/ |   
 |_|  |_|_____|    \_/  |_|_|   \__|\__,_|\__,_|_|   |_|\___||___/\__|  \____\___|_| |_|\__\___|_|                                                                                                       

 ________________________________________________________
|                                                        |
|                 Checkpoint Management                  |
|________________________________________________________|
|                                                        |
| Selected VM: {vm_name.ljust(41)} |
|________________________________________________________|
|                                                        |
|  1: Create a checkpoint                                |
|  2: Restore a checkpoint                               |
|  3: List checkpoints                                   |
|  4: Remove a checkpoint                                |
|  5: Exit                                               |
|________________________________________________________|
""")

def list_checkpoints(vm_name):
    clear_screen()
    powershell_command = f"Get-VMSnapshot -VMName {vm_name} "+"| Select-Object Name, @{Name='CreationTime';Expression={$_.CreationTime.ToString('yyyy-MM-dd HH:mm:ss')}} | ConvertTo-Json -Compress"
    headers = ["Index", "Checkpoint Name", "Creation Time"]
    return show_list(powershell_command, headers)


def select_checkpoint(vm_name):
    checkpoints = list_checkpoints(vm_name)
    if not checkpoints:
        print("There are no checkpoints available for this VM.")
        return None
    
    while True:
        try:
            index_input = input("Enter the index of the checkpoint (or '0' to cancel): ")
            if index_input == '0':
                return None
            if not index_input:
                print("No index provided. Please enter a valid index.")
                continue
            checkpoint_index = int(index_input) - 1
            if 0 <= checkpoint_index < len(checkpoints):
                return checkpoints[checkpoint_index][1]  # Get the checkpoint name from the tuple
            else:
                print("Invalid checkpoint index. Please choose a valid index.")
        except ValueError:
            print("Invalid input. Please enter a valid number.")

def create_checkpoint(vm_name):
    checkpoint_name = input("Enter the name for the checkpoint: ")
    subprocess.run(["powershell.exe", "-Command", f'Checkpoint-VM -Name {vm_name} -SnapshotName "{checkpoint_name}"'])
    print(f"Checkpoint '{checkpoint_name}' created.")
    pause()

def restore_checkpoint(vm_name):
    clear_screen()
    checkpoint_name = select_checkpoint(vm_name)
    if checkpoint_name:
        subprocess.run(["powershell.exe", "-Command", f'Restore-VMSnapshot -VMName {vm_name} -Name "{checkpoint_name}"'])
        print(f"Checkpoint '{checkpoint_name}' restored.")
        pause()

def remove_checkpoint(vm_name):
    clear_screen()
    checkpoint_name = select_checkpoint(vm_name)
    if checkpoint_name:
        try:
            subprocess.run(["powershell.exe", "-Command", f'Remove-VMSnapshot -VMName {vm_name} -Name "{checkpoint_name}"'], check=True)
            print(f"Checkpoint '{checkpoint_name}' removed successfully.")
        except subprocess.CalledProcessError as e:
            print(f"Error: Failed to remove checkpoint '{checkpoint_name}': {e}")
    else:
        print("No checkpoint selected.")
    pause()

def manage_vm_checkpoints(vm_name):
    print(f"Managing checkpoints for VM '{vm_name}'...")
    pause()
    while True:
        manage_vm_checkpoints_menu(vm_name)
        # Prompt the user for an action
        checkpoint_action = int(input("Enter your choice: "))

        # Process the user's choice
        if checkpoint_action == 1:
            create_checkpoint(vm_name)
        elif checkpoint_action == 2:
            restore_checkpoint(vm_name)
        elif checkpoint_action == 3:
            clear_screen()
            list_checkpoints(vm_name)
            pause()
        elif checkpoint_action == 4:
            remove_checkpoint(vm_name)
        elif checkpoint_action == 5:
            break
        else:
            print("Invalid checkpoint action. Please enter a valid action.")