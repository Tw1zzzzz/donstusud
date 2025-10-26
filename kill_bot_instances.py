"""
Скрипт для остановки всех запущенных экземпляров бота
"""
import os
import sys
import psutil

def kill_python_processes():
    """Остановить все процессы Python (кроме текущего)"""
    current_pid = os.getpid()
    killed_count = 0
    
    print("=" * 60)
    print("OSTANOVKA PROCESSOV PYTHON")
    print("=" * 60)
    print(f"\nTekushiy PID: {current_pid}\n")
    
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            # Проверяем, что это процесс Python
            if 'python' in proc.info['name'].lower():
                pid = proc.info['pid']
                
                # Не убиваем текущий процесс
                if pid == current_pid:
                    continue
                
                # Проверяем командную строку
                cmdline = ' '.join(proc.info['cmdline'] or [])
                
                print(f"Naydenny process Python:")
                print(f"  PID: {pid}")
                print(f"  Command: {cmdline[:100]}...")
                
                # Убиваем процесс
                proc.kill()
                killed_count += 1
                print(f"  [KILLED] Process {pid} uspeshno ostanovlen\n")
                
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    
    print("=" * 60)
    if killed_count > 0:
        print(f"Ostanovleno processov: {killed_count}")
    else:
        print("Ne naydeno processov dlya ostanovki")
    print("=" * 60)

if __name__ == "__main__":
    try:
        kill_python_processes()
    except Exception as e:
        print(f"OSHIBKA: {e}")
        import traceback
        traceback.print_exc()

