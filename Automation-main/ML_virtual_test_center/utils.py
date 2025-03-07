import ctypes
import ipaddress
import os
import subprocess
import json
from tabulate import tabulate
import time

username = 'administrator'
password = 'Linux4Ever'

def ml_text():
    clear_screen()
    print("""
          
  __  __ _      __     ___      _               _   _____         _      ____           _            
 |  \/  | |     \ \   / (_)_ __| |_ _   _  __ _| | |_   _|__  ___| |_   / ___|___ _ __ | |_ ___ _ __ 
 | |\/| | |      \ \ / /| | '__| __| | | |/ _` | |   | |/ _ \/ __| __| | |   / _ \ '_ \| __/ _ \ '__|
 | |  | | |___    \ V / | | |  | |_| |_| | (_| | |   | |  __/\__ \ |_  | |__|  __/ | | | ||  __/ |   
 |_|  |_|_____|    \_/  |_|_|   \__|\__,_|\__,_|_|   |_|\___||___/\__|  \____\___|_| |_|\__\___|_|   

""")

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def pause():
    input('\nPress ENTER to continue...')
    clear_screen()


def ask_change_network_settings():
    change_settings = input("""
Do you want to change the default settings for the following network configurations?
Gateway: 10.6.67.1
DNS: 10.6.67.2
Subnet Mask: 255.255.255.0

Enter 'y' to change the settings, or 'n' to keep the default settings: 
""")
    return change_settings.lower() == 'y'


def handle_network_settings():
    change_settings = ask_change_network_settings()

    if change_settings:
        gateway = input("Enter new gateway: ")
        dns = input("Enter new DNS: ")
        subnet_mask = input("Enter new subnet mask: ")
    else:
        gateway = "10.6.67.1"
        dns = "10.6.67.2"
        subnet_mask = "255.255.255.0"

    return gateway, dns, subnet_mask

def subnetmask_to_prefix_length(subnet_mask):
    
    # Split the subnet mask into octets
    octets = subnet_mask.split('.')
    
    # Create a string representing the binary representation of all octets
    binary_string = ''.join([bin(int(octet))[2:].zfill(8) for octet in octets])
    
    # Count the number of bits that are 1 in the binary string to get the prefix length
    prefix_length = sum(bit == '1' for bit in binary_string)
    
    return prefix_length


def list_vm(vm_name=None):
    clear_screen()
    ml_text()
    
    if vm_name:
        powershell_command = f"""
            $VMs = Get-VM -Name "{vm_name}"
        """
    else:
        powershell_command = """
            $VMs = Get-VM
        """

    powershell_command += """
        $VMInfo = @()
        foreach ($VM in $VMs) {
            $Cores = Get-VMProcessor -VMName $VM.Name
            $CoreCount = $Cores.Count
            $NetworkAdapter = Get-VMNetworkAdapter -VMName $VM.Name
            $IPAddresses = $NetworkAdapter.IPAddresses

            # Skapa en lista för IPv4-adresser
            $IPv4Addresses = @()

            # Loopa igenom varje IP-adress och filtrera ut IPv4-adresser
            foreach ($IP in $IPAddresses) {
                if ($IP -match '\d+\.\d+\.\d+\.\d+') {
                    $IPv4Addresses += $IP
                }
            }
            $IPAddress1 = $IPv4Addresses[0]
            $IPAddress2 = if ($IPv4Addresses.Length -gt 1) { $IPv4Addresses[1] } else { $null }
            $VMProperties = [PSCustomObject]@{
                'Name' = $VM.Name
                'State' = $VM.State.ToString()
                'NumberOfCores' = $CoreCount
                'StartupRAM' = $VM.MemoryStartup / 1MB
                'CPUusage' = $VM.CPUusage
                'MemoryAssigned' = $VM.MemoryAssigned / 1MB
                'IPAddress1' = $IPAddress1
                'Cluster IP' = $IPAddress2
            }
            $VMInfo += $VMProperties
        }
        $VMInfo | ConvertTo-Json -Compress
    """

    headers = ["Index", "VM Name", "State", "vCores", "Max RAM", "CPU Usage", "Memmory Usage", "IPv4-address 1", "Cluster IP"]
    vm_info_index = show_list(powershell_command, headers)
    return vm_info_index

def show_list(powershell_command, headers):
    # Run the PowerShell command
    result = subprocess.run(['powershell', '-Command', powershell_command], capture_output=True, text=True)

    # Check if the command was successful and produced output
    if result.returncode == 0 and result.stdout.strip():
        # Convert the JSON result to a Python dictionary
        vm_info = json.loads(result.stdout)

        # If vm_info is a dictionary, convert it to a list with one element
        if isinstance(vm_info, dict):
            vm_info = [vm_info]

        # Add index to each element in the list
        vm_info_index = [(i+1, *vm.values()) for i, vm in enumerate(vm_info)]

        # Display data as a table using tabulate
        print(tabulate(vm_info_index, headers=headers, tablefmt="fancy_grid"))
        return vm_info_index
    else:
        print("No data available.")
        return []  # Return an empty list if no data is available

def select():
    vm_info_index = list_vm()
    selected_vm = select_vm(vm_info_index)
    return selected_vm


def list_vm_configurations():
    clear_screen()
    ml_text()
    print("""   
 ________________________________________________________
|                                                        |
|               VM Configurations                        |
|________________________________________________________|
|                                                        |
|  1: Small (4GB RAM, 2 cores)                           |
|  2: Medium (6GB RAM, 3 cores)                          |
|  3: Large (8GB RAM, 4 cores)                           |
|  4: Custom settings                                    |
|________________________________________________________|
""")
    choice = input("Enter the number corresponding to the desired VM configuration: ")
    return choice

def select_vm_configuration():
    choice = list_vm_configurations()
    if choice == '1':
        return "Small", "4GB", 2
    elif choice == '2':
        return "Medium", "6GB", 3
    elif choice == '3':
        return "Large", "8GB", 4
    elif choice == '4':
        ram = input("Enter RAM size (e.g., 4GB): ")
        cores = int(input("Enter number of CPU cores (max 4): "))
        return "Custom", ram, cores
    else:
        print("Invalid choice. Please choose a valid option.")
        return None, None, None

def change_vm_configuration(selected_vm):
    if selected_vm:
        vm_name = selected_vm

        # Check if VM is running
        vm_status = check_vm_status(vm_name)

        # List available VM configurations and allow user to select one
        configuration_name, ram, cores = select_vm_configuration()

        if configuration_name and ram and cores:
            # If VM is running, stop it
            if vm_status.lower() == "running":
                stop_vm(vm_name, vm_status)

            # Update VM configuration
            update_vm_configuration(vm_name, ram, cores)
            print(f"Virtual machine {vm_name} reconfigured successfully with {configuration_name} configuration.")

            # If the VM was originally running, start it again
            if vm_status.lower() == "running":
                start_vm(vm_name, vm_status)
    else:
        print("No VM selected.")

def update_vm_configuration(vm_name, ram, cores):
    # PowerShell commands to update VM configuration
    ps_scripts = [
        f'Set-VMMemory "{vm_name}" -DynamicMemoryEnabled $true',
        f'Set-VM -Name "{vm_name}" -MemoryStartupBytes {ram}',
        f'Set-VM -Name "{vm_name}" -ProcessorCount {cores}'
    ]

    # Execute PowerShell commands
    for command in ps_scripts:
        run_powershell(command)


def create_vm(VMName, ram, cores):
    
    SwitchName = "Internet"
    MotherVHD = "C:\\Production\\VHD\\Motherdisk.vhdx"
    DataVHD = f"C:\\Production\\VHD\\{VMName}.vhdx"

    # PowerShell commands
    ps_scripts = [
        f'New-VHD -ParentPath "{MotherVHD}" -Path "{DataVHD}" -Differencing',
        f'New-VM -VHDPath "{DataVHD}" -MemoryStartupBytes {ram} -Name "{VMName}" -SwitchName "{SwitchName}"',
        f'Set-VM -Name "{VMName}" -ProcessorCount {cores}',
        f'Set-VMMemory "{VMName}" -DynamicMemoryEnabled $true'
    ]
    # Execute PowerShell commands
    for command in ps_scripts:
        run_powershell(command)

def create_one_vm():
    VMName = input("Enter a VM name: ")
    configuration_name, ram, cores = select_vm_configuration()
    create_vm(VMName, ram, cores)
    print(f"Virtual machine {VMName} created successfully with {configuration_name} configuration.")
    vm_status = check_vm_status(VMName)
    start_vm(VMName, vm_status)
 
def web_server(VMName):     
        
    ps_scripts = f"""
    $User = "{username}"
    $PWord = ConvertTo-SecureString -String "{password}" -AsPlainText -Force
    $Credential = New-Object -TypeName System.Management.Automation.PSCredential -ArgumentList $User, $PWord

    Invoke-Command -VMName {VMName} -Credential $Credential -ScriptBlock {{
    Install-WindowsFeature -Name Web-Server -IncludeManagementTools
    Install-WindowsFeature -Name NLB -IncludeManagementTools
}}"""
    run_powershell(ps_scripts)

def select_vm(vm_info_index):
    while True:
        try:
            index_input = input("Enter the index of the desired object (or '0' to cancel): ")
            if index_input == '0':
                return None
            if not index_input:
                print("No index provided. Please enter a valid index.")
                continue
            index = int(index_input) - 1
            if 0 <= index < len(vm_info_index):
                user_choice = vm_info_index[index][1]  
                print("You chose:", user_choice)
                return user_choice
            else:
                print("Invalid index. Please choose a valid index.")
        except ValueError:
            print("Invalid input. Please enter a valid number.")

def is_valid_ip(ip):
    try:
        ipaddress.ip_address(ip)
        return True
    except ValueError:
        return False

def set_ip(msg):
    while True:
        ip_address = input(msg)
        if is_valid_ip(ip_address):
            return ip_address
        else:
            print("Invalid IP address. Please enter a valid IP address.")

def configure_vm_network(VMName, ip, vm_status, dns, gateway, prefix_length):
    print(f"Configuring VM '{VMName}'...")
    if vm_status.lower() == "off":
        print("Strarting VM")
        start_vm(VMName)
        time.sleep(45)
    
    ps_script = f'''
        $User = "{username}"
        $PWord = ConvertTo-SecureString -String "{password}" -AsPlainText -Force
        $Credential = New-Object -TypeName System.Management.Automation.PSCredential -ArgumentList $User, $PWord
    
        Invoke-Command -VMName {VMName} -Credential $Credential -ScriptBlock {{
            
            Rename-Computer -NewName {VMName} -Confirm:$False
            Set-TimeZone -Name 'W. Europe Standard Time' -PassThru
            Set-NetIPInterface -InterfaceAlias "Ethernet" -Dhcp Enabled
            Remove-NetRoute -InterfaceAlias "Ethernet" -Confirm:$false
            New-NetIPAddress -InterfaceAlias "Ethernet" -IPAddress {ip} -PrefixLength {prefix_length} -DefaultGateway {gateway}
            Set-DnsClientServerAddress -InterfaceAlias "Ethernet" -ServerAddresses {dns}
            Restart-Computer
        }}
    '''
    run_powershell(ps_script)

def check_vm_status(vm_name):
    # Check if the VM is running
    ps_check_running = f'''
        $User = "{username}"
        $PWord = ConvertTo-SecureString -String "{password}" -AsPlainText -Force
        $Credential = New-Object -TypeName System.Management.Automation.PSCredential -ArgumentList $User, $PWord

        $VMName = "{vm_name}"
        $VMStatus = Get-VM -Name $VMName | Select-Object -ExpandProperty State
        Write-Output $VMStatus
    '''

    result = subprocess.run(["powershell.exe", "-Command", ps_check_running], capture_output=True, text=True)
    vm_status = result.stdout.strip()
    return vm_status

def remove_vm(vm_name, vm_status):
    
    # Ask for user confirmation
    confirmation = input(f"Are you sure you want to remove the VM '{vm_name}'? (yes/no): ").strip().lower()
    
    if confirmation == "yes":
        if vm_status.lower() == "running":
            stop_vm(vm_name, vm_status)
        
        # Remove the VM
        ps_remove_vm = f'''
            $User = "{username}"
            $PWord = ConvertTo-SecureString -String "{password}" -AsPlainText -Force
            $Credential = New-Object -TypeName System.Management.Automation.PSCredential -ArgumentList $User, $PWord

            $VMName = "{vm_name}"
            Remove-VM -Name $VMName -Force
        '''

        run_powershell(ps_remove_vm)
        print(f"VM '{vm_name}' removed.")

        # Remove the VHD file
        vhd_path = f'C:\\Production\\VHD\\{vm_name}.vhdx'
        if os.path.exists(vhd_path):
            os.remove(vhd_path)
            print(f"VHD file '{vhd_path}' removed.")
        else:
            print(f"VHD file '{vhd_path}' not found.")
    else:
        print("VM removal cancelled.")


def configuration_menu(vm_name):
    clear_screen()
    ml_text()
    list_vm(vm_name)
    print(f"""

 ________________________________________________________
|                                                        |
|               Configuration Management                 |
|________________________________________________________|
|                                                        |
| Selected VM: {vm_name.ljust(41)}  |
|________________________________________________________|
|                                                        |
|  1: Change Network Configuration                       |
|  2: Change VM Configuration                            |
|  3: Start VM                                           |
|  4: Stop VM                                            |
|  5: Restart VM                                         |
|  0: Exit                                               |
|________________________________________________________|
""")

def change_ip_address(vm_name,vm_status):
    if vm_status.lower() == "off":
        start_vm(vm_name)
        time.sleep(45)
    msg = f"Enter new IP address for {vm_name}: "
    ip = set_ip(msg)
    gateway, dns, subnet_mask = handle_network_settings()
    prefix_length = subnetmask_to_prefix_length(subnet_mask)

    configure_vm_network(vm_name, ip, vm_status, dns, gateway, prefix_length)
    pause()

def start_vm(vm_name,vm_status):
    if vm_status.lower() == "off":
        command = f"Start-VM -Name {vm_name}"
        subprocess.run(['powershell', '-Command', command])
    print(f"Starting VM '{vm_name}'...")
    pause()

def stop_vm(vm_name,vm_status):
    if vm_status.lower() == "running":
        command = f"Stop-VM -Name {vm_name} -Force"
        run_powershell(command)
    print(f"Stopping VM '{vm_name}'...")
    pause()

def restart_vm(vm_name,vm_status):
    if vm_status.lower() == "running":
        print(f"Restarting VM '{vm_name}'")
        command = "Restart-VM -Name {vm_name} -Force"
        run_powershell(command)
    elif vm_status.lower() == "off":
         start_vm(vm_name,vm_status)
    pause()  
   
def change_configuration(vm_name, vm_status):
    print(f"Managing configuration for VM '{vm_name}'...")
    pause()
    while True:
        configuration_menu(vm_name)
        choice = input("Enter your choice: ")
        if choice == '1':
            change_ip_address(vm_name,vm_status)
        elif choice == '2':
            change_vm_configuration(vm_name)
        elif choice == '3': 
            start_vm(vm_name,vm_status)
        elif choice == '4':
            stop_vm(vm_name,vm_status)
        elif choice == '5':           
            restart_vm(vm_name,vm_status)
        elif choice == '0':
            clear_screen()
            break
        else:
            print("Invalid choice. Please enter a valid option.")


def run_powershell(ps_script):
    subprocess.run(['powershell', '-Command', ps_script], stdout=subprocess.PIPE)

def exit_menu():
    print("\nExiting the Menu...")
    time.sleep(1)  # Add a delay for dramatic effect
    print("See you on the other side of the code")
    print("🚀🐍✨")
