from utils import *
from tabulate import tabulate
import subprocess


def start_environment(): 
    clear_screen()
    ml_text()
    print("""
    Welcome to the Test Environment Setup Wizard.
    This wizard will guide you through the process of setting up your virtual test environment.
    Please provide the following information to proceed:
    """) 

    gateway, dns, subnet_mask = handle_network_settings()
    prefix_length = subnetmask_to_prefix_length(subnet_mask)

    vm = {}
    num_vms = int(input("Enter the number of VMs to create: "))
    clear_screen()
    msg = ("Enter new cluster IP-address: ")
    nlb_ip = set_ip(msg)
    
    
    for _ in range(num_vms):
        VMName = input("Enter a VM name: ")
        msg = ("Enter IP-address: ")
        ip = set_ip(msg)
        vm[VMName] = ip
    clear_screen()
    print("\nConfirm the following configuration:")
    
    print(tabulate(vm.items(), headers=["VM Name", "IP Address"]))
    
    print(f"""
        Cluster IP-address: {nlb_ip}
        
        Subnet Mask: {subnet_mask}   
        Default Gateway: {gateway}
        DNS: {dns}
             
    """)
    confirmation = input("\nIs the configuration correct? (y/n): ").lower()
    if confirmation != "y":
        print("Configuration canceled.")
        return

    vm_list = list(vm.keys())
    configuration_name, ram, cores = select_vm_configuration()
    nlb_master = next(iter(vm.keys()))
 
    for VMName, ip in vm.items():
        print(f"Creating Virtual machine: {VMName}")
        create_vm(VMName, ram, cores)
        time.sleep(1)
        print(f"Starting: {VMName}")
        ps_scripts = f"Start-VM -Name {VMName}"
        run_powershell(ps_scripts)
    print("Waiting for Windows Server 2022 to install")
    time.sleep(120)
    
    for VMName, ip in vm.items():
        vm_status = check_vm_status(VMName)
        configure_vm_network(VMName, ip, vm_status, gateway, dns, prefix_length)
        print(f"Setting up network configuration for'{VMName}' : '{ip}' ")
        time.sleep(10)

    for VMName, ip in vm.items():
        print(f"Installing Internet Information Services and Network Load Balancer'{VMName}'")
        web_server(VMName)

    for vm in vm_list:
        print(f"Setting up Web page and Network Load Balacer for'{vm}'")
        config_nlb(nlb_ip, vm, nlb_master)
        time.sleep(50)
        create_website(vm)


def config_nlb(nlb_ip, vm, nlb_master):
        ps_script = f"""
        $User = "{username}"
        $PWord = ConvertTo-SecureString -String "{password}" -AsPlainText -Force
        $Credential = New-Object -TypeName System.Management.Automation.PSCredential -ArgumentList $User, $PWord
        Invoke-Command -VMName {vm} -Credential $Credential -ScriptBlock {{
            if ("{vm}" -eq "{nlb_master}") {{
                # NLB Configuration for NLB_Master
                New-NlbCluster -InterfaceName "Ethernet" -ClusterName "nlbcluster.local" -ClusterPrimaryIP {nlb_ip} -OperationMode Multicast    
                Get-NlbClusterPortRule | Remove-NlbClusterPortRule -Force
                Get-NlbCluster | Add-NlbClusterPortRule -StartPort 80 -EndPort 80 -Affinity None
         }} else {{
                # NLB Configuration for other VMs
                Get-NlbCluster {nlb_master} | Add-NlbClusterNode -NewNodeName {vm} -NewNodeInterface "Ethernet"    
            }}
            Set-NetFirewallRule -DisplayGroup "File And Printer Sharing" -Enabled True -Profile Any    
            
            }}
        """
        run_powershell(ps_script)
        
def create_website(vm):
    # HTML content for webpage.
    html_content = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>ML Test Site</title>
        </head>
        <body>
            <h1>Welcome to our test website!</h1>
            <p>You are connected to server: {vm}</p>
        </body>
        </html>
    """

    # Path to the target file on the server
    remote_path = f'\\\\{vm}\\c$\\inetpub\\wwwroot\\index.html'

    try:
        # Check if the file already exists; if not, create it.
        ps_command_check_file = f"""
        if (-not (Test-Path "{remote_path}")) {{
            New-Item -Path "{remote_path}" -ItemType "file" -Force | Out-Null
        }}
        """

        # Create PowerShell command.
        ps_scripts = f"""
              
        {ps_command_check_file}
        Set-Content -Path {remote_path} -Value '{html_content}'
        """

        # Run the PowerShell command with subprocess
        run_powershell(ps_scripts)

        print(f"Web page created on {vm} with Network Load Balancing")

    except subprocess.CalledProcessError as e:
        print(f"Failed to create web page on {vm}: {e}")



