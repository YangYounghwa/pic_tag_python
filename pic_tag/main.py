from pic_tag.dashboard import app
from pic_tag import camera_manger


def main():
    app.run(debug=True,host='0,0.0.0', port=5000)
    camera_manger.start_all_cameras()

if __name__ == "__main__":
    main()