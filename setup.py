import os
import platform
import socket
import mysql.connector
import subprocess
import json
import re

from database import cursorInsert, cursorSelect, insert, select

so = platform.system().lower()
version = platform.release()

def formatSize(bytes):
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes < 1024:
            return f"{bytes:.2f}"
        bytes /= 1024
    return f"{bytes:.2f}"

def getMobuId(so):
    try:
        if so == "windows":
            mobuId = subprocess.check_output(["powershell", "-Command",
                                                      "Get-WmiObject Win32_BaseBoard | Select-Object -ExpandProperty SerialNumber"],
                                                     shell=True).decode().strip()
            if not mobuId:
                mobuId = "UUID não encontrado"
        elif so == "linux":
            mobuId = subprocess.check_output("sudo dmidecode -s system-uuid", shell=True).decode().strip()
        else:
            mobuId = "Desconhecido"
        return mobuId
    except Exception as e:
        print(f"Erro ao obter ID da placa-mãe: {str(e)}")
        return None

def getHostname(so):
    try:
        hostname = socket.gethostname()

        if so == 'linux' and not hostname:
            hostname = os.uname().nodename

        elif so == 'windows' and not hostname:
            hostname = os.popen('hostname').read().strip()

        return hostname

    except Exception as e:

        print(f"Erro ao obter hostname: {e}")
        return None

def getMacAddress(system):
    if system == "windows":
        try:
            output = subprocess.check_output(
                "getmac /v /FO list",
                shell=True,
                text=True,
                stderr=subprocess.DEVNULL
            )
            mac_match = re.search(r"([0-9A-F]{2}[:-]){5}([0-9A-F]{2})", output, re.IGNORECASE)
            if mac_match:
                return mac_match.group(0).upper()
        except:
            pass

    elif system == "linux":
        try:
            output = subprocess.check_output(
                "ip link show | grep 'link/ether' | head -n 1",
                shell=True,
                text=True,
                stderr=subprocess.DEVNULL
            )
            mac_match = re.search(r"([0-9a-f]{2}[:]){5}([0-9a-f]{2})", output.lower())
            if mac_match:
                return mac_match.group(0)
        except:
            try:
                output = subprocess.check_output(
                    "ifconfig | grep 'ether' | head -n 1",
                    shell=True,
                    text=True,
                    stderr=subprocess.DEVNULL
                )
                mac_match = re.search(r"([0-9a-f]{2}[:]){5}([0-9a-f]{2})", output.lower())
                if mac_match:
                    return mac_match.group(0)
            except:
                pass

    return None

def getDiscos(so):
    disks_info = []

    if so == "windows":
        try:
            command = "Get-Volume | Where-Object {$_.DriveLetter -ne $null} | Select-Object DriveLetter, Size | ConvertTo-Json"
            result = subprocess.run(["powershell", "-Command", command], capture_output=True, text=True)

            volumes = json.loads(result.stdout)

            for vol in volumes:
                disks_info.append({
                    'path': f"{vol['DriveLetter']}:",
                    'size': formatSize(vol['Size'])
                })
        except Exception as e:
            print(f"Erro {str(e)}")

    elif so == "linux":
        try:
            command = "lsbdk -d -b -n -o NAME,SIZE --json"
            result = subprocess.run(command, shell=True, capture_output=True, text=True)

            disks = json.loads(result.stdout)['blockdevices']

            for disk in disks:
                if disk['type'] == 'disk':
                    disks_info.append({
                        'path': f"/dev/{disk['name']}",
                        'size': int(formatSize(disk['size']))
                    })
        except Exception as e:
            print(f"Erro: {str(e)}")
    return disks_info

def getRam(so):
    try:
        if so == "windows":
            cmd = 'wmic memorychip get capacity'
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            if result.returncode == 0:
                total_bytes = sum(int(num) for num in re.findall(r'\d+', result.stdout))
                return formatSize(total_bytes)

        elif so == "linux":
            with open('/proc/meminfo', 'r') as f:
                meminfo = f.read()
                match = re.search(r'MemTotal:\s+(\d+)\s+kB', meminfo)
                if match:
                    return int(match.group(1)) * 1024
    except Exception as e:
        print(f"Erro ao obter RAM")

def getCpu(so):
    try:
        if so == "windows":
            command = 'wmic cpu get name'
            result = subprocess.run(command, shell=True, capture_output=True, text=True)
            if result.returncode == 0:
                cpu_name = [line.strip() for line in result.stdout.split('\n') if line.strip()][1]
                return cpu_name

        elif so == "linux":
            command = "cat /proc/cpuinfo | grep 'model name' | uniq | cut -d ':' -f 2 | xargs"
            result = subprocess.run(command, shell=True, capture_output=True, text=True)
            if result.returncode == 0:
                return result.stdout.strip()

    except Exception as e:
        print(f"Erro ao obter informações da CPU: {str(e)}")

    return "Informação não disponível"

def get_system_components(so):
    components = []

    disks = getDiscos(so)
    for disk in disks:
        components.append({
            'name': disk['path'],
            'type': 'Disk',
            'description': disk['size']
        })
    ram_size = getRam(so)
    components.append({
        'name': 'Memoria Ram',
        'type': 'Ram',
        'description': ram_size
    })

    cpu_name = getCpu(so)
    components.append({
        'name': cpu_name,
        'type': 'Cpu',
        'description': None
    })

    return components

def sync_components(fkServer, fkCompany, so):
    try:
        current_components = get_system_components(so)
        current_names = {comp['name'] for comp in current_components}

        query_select = """
                       SELECT idComponent, name, type, description
                       FROM Component
                       WHERE fkServer = %s
                       """
        cursorSelect.execute(query_select, (fkServer,))
        db_components = []

        for (idComponent, name, type_, description) in cursorSelect:
            db_components.append({
                'idComponent': idComponent,
                'name': name,
                'type': type_,
                'description': description
            })

        db_name_map = {comp['name']: comp for comp in db_components}
        for db_comp in db_components:
            if db_comp['name'] not in current_names:
                deactivate_query = """
                                   UPDATE Component
                                   SET active     = 0
                                   WHERE idComponent = %s
                                     AND fkServer = %s
                                   """
                cursorInsert.execute(deactivate_query, (db_comp['idComponent'], fkServer))
                print(f"[DESATIVADO] Componente: {db_comp['name']}")
        for current_comp in current_components:
            current_desc = str(current_comp['description']) if current_comp['description'] else None

            if current_comp['name'] in db_name_map:
                db_comp = db_name_map[current_comp['name']]
                needs_update = (
                        db_comp['type'] != current_comp['type'] or
                        str(db_comp['description']) != current_desc
                )

                if needs_update:
                    update_query = """
                                   UPDATE Component
                                   SET type        = %s,
                                       description = %s,
                                       active      = 1
                                   WHERE idComponent = %s
                                     AND fkServer = %s
                                   """
                    cursorInsert.execute(update_query, (
                        current_comp['type'],
                        current_desc,
                        db_comp['idComponent'],
                        fkServer
                    ))
                    print(f"[ATUALIZADO] Componente: {current_comp['name']}")
            else:
                insert_query = """
                               INSERT INTO Component
                                   (name, type, description, fkServer, active)
                               VALUES (%s, %s, %s, %s, 1)
                               """
                cursorInsert.execute(insert_query, (
                    current_comp['name'],
                    current_comp['type'],
                    current_desc,
                    fkServer,
                ))
                print(f"[INSERIDO] Novo componente: {current_comp['name']}")

        insert.commit()
        print(f"✅ Sincronização concluída para servidor {fkServer} (Empresa {fkCompany})")
        return True

    except mysql.connector.Error as err:
        print(f"❌ Erro MySQL durante sincronização: {err}")
        insert.rollback()
        return False

    except Exception as e:
        print(f"❌ Erro inesperado durante sincronização: {str(e)}")
        insert.rollback()
        return False
