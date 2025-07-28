from camera_worker import start_all_cameras
import os

def main():
    if len(os.sys.argv) > 1 and os.sys.argv[1] == "live":
        print("Starting all cameras...")
        start_all_cameras()
    if (len(os.sys.argv) > 1 and os.sys.argv[1] == "video"):
        num_of_videos = os.sys.argv[3]
        v_list = []
        for i in range(int(num_of_videos)):
            v_list.append(os.sys.argv[4+i])
        start_all_cameras(live=False,camera_path_list=v_list)
        pass 
        # Implement stop logic if needed
if __name__ == "__main__":
    main()