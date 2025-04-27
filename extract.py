import os

import psutil
import requests

urlFlask = "http://44.208.193.41:5000/s3/raw/upload"

def cpuData():
    cpuFreq = psutil.cpu_freq()
    cpuPercent = psutil.cpu_percent()
    
    return cpuFreq, cpuPercent

def ramData():
    ramUsed = psutil.virtual_memory().used
    ramPercent = psutil.virtual_memory().percent
    
    return ramUsed, ramPercent

def diskData(path):
    diskUsed = psutil.disk_usage(path).used
    diskPercent = psutil.disk_usage(path).percent

    return diskUsed, diskPercent

import csv
from datetime import datetime
import time

from setup import getDiscos, so, getMobuId

def processData():
    processes = []
    for proc in psutil.process_iter(['name', 'memory_percent', 'cpu_percent', 'memory_info']):
        try:
            process_info = {
                'name': proc.info['name'],
                'memory_percent': proc.info['memory_percent'],
                'cpu_percent': proc.info['cpu_percent'],
                'vms': proc.info['memory_info'].vms if proc.info['memory_info'] else None
            }
            processes.append(process_info)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return processes

def send_file_to_api(file_path, api_url):
    try:
        with open(file_path, 'rb') as file:
            files = {'file': (os.path.basename(file_path), file)}
            response = requests.post(api_url, files=files)

        if response.status_code == 200:
            print(f"Arquivo {file_path} enviado com sucesso para a API")
            os.remove(file_path)
            return True
        else:
            print(f"Erro ao enviar arquivo: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"Falha ao enviar arquivo {file_path} para a API: {str(e)}")
        return False

def monitor_and_send(companyName, mobuID, api_url):
    record_count = 0
    current_file = None
    current_process_file = None
    discos = None

    def create_new_files():
        nonlocal current_file, current_process_file, discos, record_count
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        output_file = f"{companyName}_{mobuID}_{timestamp}.csv"

        process_file = f"{companyName}_{mobuID}_{timestamp}_process.csv"

        discos = getDiscos(so)

        with open(output_file, mode='w', newline='') as file:
            writer = csv.writer(file)
            headers = ['data_hora', 'cpu_freq', 'cpu_percent', 'ram_used', 'ram_percent']

            for disco in discos:
                path_safe = disco['path'].replace('/', '_').replace('\\', '_').replace(':', '')
                headers.extend([
                    f'disco_{path_safe}_used',
                    f'disco_{path_safe}_percent'
                ])

            writer.writerow(headers)

        with open(process_file, mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['data_hora', 'process_name', 'memory_percent', 'cpu_percent', 'vms'])

        print(f"Novos arquivos de monitoramento criados:")
        print(f"- {output_file}")
        print(f"- {process_file}")

        record_count = 0
        return output_file, process_file, discos

    current_file, current_process_file, discos = create_new_files()

    while True:
        try:
            if record_count >= 100:

                send_file_to_api(current_file, api_url)
                send_file_to_api(current_process_file, api_url)

                current_file, current_process_file, discos = create_new_files()

            data_hora = datetime.now().strftime('%d/%m/%Y %H:%M:%S')

            cpuFreq, cpuPercent = cpuData()
            ramUsed, ramPercent = ramData()

            row = [
                data_hora,
                cpuFreq.current,
                cpuPercent,
                ramUsed,
                ramPercent
            ]

            for disco in discos:
                try:
                    disk_used, disk_percent = diskData(disco['path'])
                    row.extend([disk_used, disk_percent])
                except Exception as e:
                    print(f"Erro ao acessar disco {disco['path']}: {str(e)}")
                    row.extend([None, None])

            with open(current_file, mode='a', newline='') as file:
                writer = csv.writer(file)
                writer.writerow(row)

            processes = processData()
            with open(current_process_file, mode='a', newline='') as file:
                writer = csv.writer(file)
                for proc in processes:
                    writer.writerow([
                        data_hora,
                        proc['name'],
                        proc['memory_percent'],
                        proc['cpu_percent'],
                        proc['vms']
                    ])

            record_count += 1
            time.sleep(2)

        except KeyboardInterrupt:
            print("\nMonitoramento encerrado pelo usuário")

            send_file_to_api(current_file, api_url)
            send_file_to_api(current_process_file, api_url)
            break

        except Exception as e:
            print(f"Erro durante o monitoramento: {str(e)}")
            time.sleep(2)
