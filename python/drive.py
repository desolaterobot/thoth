import psutil

def driveCapacity(fullpath:str):
    drive = fullpath.split(sep='\\')[0]
    partitions = psutil.disk_partitions()
    for partition in partitions:
        if partition.device.startswith(drive):
            usage = psutil.disk_usage(partition.mountpoint)
            return {
                'drive': drive,
                'total': usage.total,
                'used': usage.used,
                'free': usage.free
            }
    print("invalid path.")
    return None

""" if drive_info:
    print(f"Drive {drive_info['drive']} - Total Capacity: {drive_info['total'] / (1024 ** 3):.2f} GB")
    print(f"Used Capacity: {drive_info['used'] / (1024 ** 3):.2f} GB")
    print(f"Free Capacity: {drive_info['free'] / (1024 ** 3):.2f} GB")
else:
    print(f"Drive not found.") """
