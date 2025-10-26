"""
Безопасный запуск бота с автоматической остановкой предыдущих экземпляров
"""
import os
import sys
import time
import subprocess

try:
    import psutil
except ImportError:
    print("OSHIBKA: biblioteka psutil ne ustanovlena")
    print("Ustanovite: pip install psutil")
    sys.exit(1)

def kill_other_bots():
    """Остановить все процессы main.py кроме текущего"""
    current_pid = os.getpid()
    killed = 0
    
    print("=" * 60)
    print("Proverka zapushennykh botov...")
    print("=" * 60)
    
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            if 'python' in proc.info['name'].lower():
                cmdline = ' '.join(proc.info['cmdline'] or [])
                
                # Ищем процессы с main.py
                if 'main.py' in cmdline and proc.info['pid'] != current_pid:
                    print(f"\nNaydenny zapushenny bot (PID: {proc.info['pid']})")
                    proc.kill()
                    killed += 1
                    print(f"[KILLED] Process {proc.info['pid']} ostanovlen")
                    
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    
    if killed > 0:
        print(f"\nOstanovleno processov: {killed}")
        print("Zhdem 5 sekund dlya osvobozhdeniya soedineniya...")
        time.sleep(5)
    else:
        print("\nZapushennykh botov ne naydeno.")
    
    print("=" * 60)

def start_bot():
    """Запустить бота"""
    print("\n" + "=" * 60)
    print("ZAPUSK BOTA...")
    print("=" * 60 + "\n")
    
    try:
        # Запускаем main.py
        subprocess.run([sys.executable, "main.py"], check=True)
    except KeyboardInterrupt:
        print("\n\nBot ostanovlen polzovatelem (Ctrl+C)")
    except Exception as e:
        print(f"\nOSHIBKA pri zapuske bota: {e}")
        sys.exit(1)

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("BEZOPASNYY ZAPUSK BOTA")
    print("=" * 60)
    
    # Шаг 1: Остановить предыдущие экземпляры
    kill_other_bots()
    
    # Шаг 2: Запустить бота
    start_bot()

