import tkinter as tk
from tkinter import messagebox, filedialog, ttk
import tkinter.scrolledtext as st
import cv2
from PIL import Image, ImageTk
import os
import numpy as np
import yaml


label_txt_path = "label.txt"
label_yaml_path = "label.yaml"
save_dir_path = ""


height = 0
width = 0
scale = 1
origin_image = None
image = None
cap = None


is_image = True


def toggle_image_video():
    global is_image
    is_image = not is_image
    if is_image:
        toggle_image_video_button.config(text="Image")
        my_log("Image Data Preprocessing...")
        reset()
        create_image_canvas_frame()
    else:
        toggle_image_video_button.config(text="Video")
        my_log("Video Data Preprocessing...")
        reset()
        create_video_canvas_frame()


def create_image_canvas_frame():
    global image_canvas_frame, image_canvas  # 전역 변수로 선언
    image_canvas_frame = tk.Frame(top, width=1020, height=820)
    image_canvas_frame.grid(row=0, column=1)

    image_canvas = tk.Canvas(image_canvas_frame, width=1000, height=800, background="white")
    image_canvas.grid(row=0, column=0)

    yscrollbar = tk.Scrollbar(image_canvas_frame, orient="vertical", command=image_canvas.yview)
    yscrollbar.grid(row=0, column=1, sticky="ns")

    xscrollbar = tk.Scrollbar(image_canvas_frame, orient="horizontal", command=image_canvas.xview)
    xscrollbar.grid(row=1, column=0, sticky="ew")

    image_canvas.configure(yscrollcommand=yscrollbar.set, xscrollcommand=xscrollbar.set)
    image_canvas.configure(scrollregion=image_canvas.bbox("all"))
    # 드래그 스크롤 바인딩
    image_canvas.bind("<Button-1>", start_drag)
    image_canvas.bind("<B1-Motion>", drag_to_scroll)


def create_video_canvas_frame():
    global image_canvas_frame, image_canvas, frame_slider, pause_button  # 전역 변수로 선언
    image_canvas_frame = tk.Frame(top, width=1020, height=820)
    image_canvas_frame.grid(row=0, column=1)

    # 영상 캔버스 생성
    image_canvas = tk.Canvas(image_canvas_frame, width=1000, height=700, background="black")
    image_canvas.grid(row=0, column=0)
    # 영상 제어 위젯을 담을 프레임 생성
    video_controls_frame = tk.Frame(image_canvas_frame)
    video_controls_frame.grid(row=1, column=0, sticky="ew", pady=(5, 0))

    frame_slider = tk.Scale(video_controls_frame, from_=1, to=1, orient="horizontal", command=move_to_frame)
    frame_slider.pack(side="top", fill="x", padx=10, pady=5)

    # 버튼 그룹을 생성하고 배치합니다.
    button_group = tk.Frame(video_controls_frame)
    button_group.pack(side="top", padx=10, pady=5)

    prev_frame_button = tk.Button(button_group, text="⏪", width=5, command=prev_frame)
    prev_frame_button.pack(side="left", padx=(0, 5))

    pause_button = tk.Button(button_group, text="▶", width=5, command=toggle_play)
    pause_button.pack(side="left", padx=(0, 5))

    next_frame_button = tk.Button(button_group, text="⏩", width=5, command=next_frame)
    next_frame_button.pack(side="left", padx=(0, 5))


def configure_frame_slider():
    global frame_slider
    max_frame = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    frame_slider.config(to=max_frame)


def move_to_frame(frame_number):
    global cap
    frame_number = int(frame_number)
    cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number - 1)


def reset():
    global labeled_images, image, origin_image, cap, scale, height, width, brightness
    file_listbox.delete(0, tk.END) # 파일 목록 초기화
    image_canvas.delete("all") # 이미지 캔버스 초기화
    # 라벨링 이미지 초기화
    labeled_images = []
    labeled_image_listbox.delete(0, tk.END)
    # 변수 초기화
    if cap:
        cap.release()
    image = None
    origin_image = None
    scale = 1
    zoom_entry.delete(0, tk.END)
    zoom_entry.insert(tk.END, int(scale*100))
    height = 0
    width = 0
    brightness = 1
    brightness_entry.delete(0, tk.END)
    brightness_entry.insert(tk.END, round(brightness*50))
    my_log("Reset...")


def load_media(media_path):
    if is_image:
        load_image(media_path)
    else:
        load_video(media_path)


def load_image(image_path):
    global image, origin_image, height, width, scale, labeled_images
    # 이미지 로드
    image = cv2.imread(image_path)
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

    # 오리지날 이미지 저장
    origin_image = image.copy()

    height, width, _ = image.shape

    # 이미지 캔버스에 이미지가 없는 경우에만 이미지 크기 조정
    if not image_canvas.find_all():
        # 이미지 크기 조정 (캔버스 크기에 맞게)
        scale = min(scale, 1000.0 / max(height, width))
        zoom_entry.delete(0, tk.END)
        zoom_entry.insert(tk.END, int(scale*100))

    # 라벨링 이미지 초기화
    labeled_images = []
    labeled_image_listbox.delete(0, tk.END)

    # 이미지 파일 경로에서 파일이름 가져오기
    filename_with_extension = os.path.basename(image_path)
    filename, _ = os.path.splitext(filename_with_extension)

    # labels 폴더 경로 가져오기
    current_folder = os.path.dirname(image_path)
    parent_folder = os.path.dirname(current_folder)
    labels_folder_path = os.path.join(parent_folder, "labels")
    label_filename = filename + ".txt"
    label_file_path = os.path.join(labels_folder_path, label_filename)

    # 라벨 텍스트파일 불러오기
    if os.path.exists(labels_folder_path) and os.path.exists(label_file_path):
        label_list = []
        with open(label_txt_path, 'r') as file:
            for line in file:
                line = line.strip()
                label_list.append(line)

        with open(label_file_path, 'r') as file:
            for line in file:
                # 각 줄에서 띄어쓰기를 기준으로 리스트 생성
                line_list = line.strip().split()

                label_index, normalized_center_x, normalized_center_y, normalized_w, normalized_h = line_list

                center_x = float(normalized_center_x) * width
                center_y = float(normalized_center_y) * height
                w = float(normalized_w) * width
                h = float(normalized_h) * height

                converted_line = [label_list[int(label_index)], center_x-w//2, center_y-h//2, center_x+w//2, center_y+h//2]
                
                # 이미지 라벨 리스트박스에 추가
                labeled_images.append(converted_line)
                labeled_image_listbox.insert(tk.END, converted_line[0])
        my_log("loading labels...")
    else:
        my_log("no label file.")

    my_log("load image : " + image_path)
    image_print()


def load_video(video_path):
    global cap, height, width, scale, labeled_images, video_playing
    
    # 기존 캡처 객체가 존재하는지 확인하고 있으면 해제
    if cap and cap.isOpened():
        cap.release()
    
    # 비디오 캡처 객체 생성
    cap = cv2.VideoCapture(video_path)

    # 비디오 캡처 객체가 성공적으로 열렸는지 확인
    if not cap.isOpened():
        messagebox.showerror("경고", "비디오 파일을 열 수 없습니다.")
        return

    # 비디오 프레임의 너비와 높이
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    # 이미지 캔버스에 이미지가 없는 경우에만 이미지 크기 조정
    if not image_canvas.find_all():
        # 이미지 크기 조정 (캔버스 크기에 맞게)
        scale = min(scale, 1000.0 / max(height, width))
        zoom_entry.delete(0, tk.END)
        zoom_entry.insert(tk.END, int(scale*100))
    
    # 캔버스 초기화
    image_canvas.delete("all")

    # 비디오 재생
    my_log("load video : " + video_path)
    toggle_play()
    configure_frame_slider()
    play_video()


video_playing = False

def toggle_play():
    global video_playing, pause_button
    video_playing = not video_playing
    if video_playing:
        pause_button.config(text="⏸️")
        play_video()
    else:
        pause_button.config(text="▶")


def play_video():
    global cap, image, origin_image, labeled_images, video_playing

    # 라벨링 이미지 초기화
    if labeled_images:
        labeled_images = []
        labeled_image_listbox.delete(0, tk.END)

    if cap.isOpened() and video_playing:
        # 비디오에서 프레임 읽기
        ret, frame = cap.read()

        if ret:
            image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            origin_image = image.copy()

            image_print()

            # 다음 프레임 재생
            top.after(33, play_video)

            # 프레임 슬라이더 업데이트
            current_frame = int(cap.get(cv2.CAP_PROP_POS_FRAMES))
            frame_slider.set(current_frame)
        else:
            # 비디오가 종료되면 재생 중지
            video_playing = False
            cap.release()
            my_log("video close...")


def image_print():
    global image
    if toggle_gray_image:
        image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        image = origin_image

    resized_image = cv2.resize(image, (int(width * scale), int(height * scale)))

    # 밝기 조정
    adjust_image = np.clip(resized_image * brightness, 0, 255).astype(np.uint8)

    # OpenCV 이미지를 PIL 이미지로 변환
    pil_image = Image.fromarray(adjust_image)

    # PIL 이미지를 tkinter PhotoImage로 변환
    photo = ImageTk.PhotoImage(image=pil_image)

    # 이미지를 캔버스에 출력합니다.
    image_canvas.create_image(0, 0, anchor=tk.NW, image=photo)
    image_canvas.image = photo

    # 이미지의 크기를 기반으로 캔버스의 스크롤 영역을 설정합니다.
    image_canvas.config(scrollregion=(0, 0, photo.width(), photo.height()))

    on_labeled_image_listbox_select()


def file_open():
    if is_image:
        # 이미지 파일 확장자
        filetypes = [("Image files", "*.jpg;*.jpeg;*.png;*.gif;*.bmp")]
    else:
        # 동영상 파일 확장자
        filetypes = [("Video files", "*.mp4;*.avi;*.mov")]

    file_paths = filedialog.askopenfilenames(initialdir="./data", filetypes=filetypes)
    if file_paths:
        file_listbox.delete(0, tk.END)
        for file_path in file_paths:
            file_listbox.insert(tk.END, file_path)
        file_listbox.selection_set(0)  # 첫 번째 아이템 선택
        file_listbox_selected()
        my_log("open file : " + file_path)


def dir_open():
    if is_image:
        # 이미지 파일 확장자
        extensions = [".jpg", ".jpeg", ".png", ".gif", ".bmp"]
    else:
        # 동영상 파일 확장자
        extensions = [".mp4", ".avi", ".mov"]

    dir_path = filedialog.askdirectory(initialdir="./data")
    if dir_path:
        my_log("open dir : " + dir_path)
        file_listbox.delete(0, tk.END)
        for file_name in os.listdir(dir_path):
            file_path = os.path.join(dir_path, file_name)

            # 파일이 이미지 파일인지 확인
            if os.path.isfile(file_path) and file_name.lower().endswith(tuple(extensions)):
                file_listbox.insert(tk.END, file_path)
        file_listbox.selection_set(0)  # 첫 번째 아이템 선택
        file_listbox_selected()


def next_file():
    # 현재 선택된 아이템의 인덱스를 가져옵니다.
    selected_index = file_listbox.curselection()
    if selected_index:
        # 다음 아이템의 인덱스를 계산합니다.
        next_index = selected_index[0] + 1
        # 다음 아이템이 리스트박스의 범위를 넘어가지 않도록 조정합니다.
        if next_index < file_listbox.size():
            # 다음 아이템을 선택합니다.
            file_listbox.selection_clear(0, tk.END)
            file_listbox.selection_set(next_index)
            file_listbox.activate(next_index)
            # 선택된 아이템에 해당하는 이미지를 출력합니다.
            file_listbox_selected()
            # 선택된 아이템이 화면에 표시되도록 스크롤바를 이동시킵니다.
            file_listbox.see(next_index)
            my_log("next image...")


def prev_file():
    # 현재 선택된 아이템의 인덱스를 가져옵니다.
    selected_index = file_listbox.curselection()
    if selected_index:
        # 이전 아이템의 인덱스를 계산합니다.
        prev_index = selected_index[0] - 1
        # 이전 아이템이 리스트박스의 범위를 넘어가지 않도록 조정합니다.
        if prev_index >= 0:
            # 다음 아이템을 선택합니다.
            file_listbox.selection_clear(0, tk.END)
            file_listbox.selection_set(prev_index)
            file_listbox.activate(prev_index)
            # 선택된 아이템에 해당하는 이미지를 출력합니다.
            file_listbox_selected()
            # 선택된 아이템이 화면에 표시되도록 스크롤바를 이동시킵니다.
            file_listbox.see(prev_index)
            my_log("prev image")


def save_file():
    if labeled_images:
        # grab_image를 numpy 배열에서 PIL 이미지로 변환
        image_pil = Image.fromarray(image)
        image_pil_width, image_pil_height = image_pil.size

        file_name = "data.jpg"
        
        if save_dir_path:
            # train, valid, test 데이터 셋 나누기
            data_save_dir_path = os.path.join(save_dir_path, selected_data_option)
            # 폴더가 없으면 생성
            if not os.path.exists(data_save_dir_path):
                os.makedirs(data_save_dir_path)
                my_log("make dir : " + data_save_dir_path)

            image_save_path = os.path.join(data_save_dir_path, "images")
            label_save_path = os.path.join(data_save_dir_path, "labels")

            # 폴더가 없으면 생성
            if not os.path.exists(image_save_path):
                os.makedirs(image_save_path)
                my_log("make dir : " + image_save_path)
            
            if not os.path.exists(label_save_path):
                os.makedirs(label_save_path)
                my_log("make dir : " + label_save_path)

            image_file_path = os.path.join(image_save_path, file_name)
            base, ext = os.path.splitext(file_name)
            label_text_file_name = base + ".txt"
            label_file_path = os.path.join(label_save_path, label_text_file_name)

        else:
            change_save_dir()
            save_file()
            return
        
        # 파일 경로가 이미 존재하는 경우 숫자를 추가하여 중복을 피합니다.
        count = 1
        while os.path.exists(image_file_path):
            base, ext = os.path.splitext(file_name)
            if '_' in base:
                base, num = base.rsplit('_', 1)  # 마지막 '_'를 기준으로 분할하여 숫자를 찾음
                if num.isdigit():
                    count = int(num) + 1  # 숫자를 증가시킴
                    file_name = f"{base}_{count}{ext}"
                else:
                    file_name = f"{base}_{count}{ext}"  # 숫자가 아니라면 숫자를 추가함
            else:
                file_name = f"{base}_{count}{ext}"  # '_'가 없는 경우 숫자를 추가함
            
            image_file_path = os.path.join(image_save_path, file_name)
            base, ext = os.path.splitext(file_name)
            label_text_file_name = base + ".txt"
            label_file_path = os.path.join(label_save_path, label_text_file_name)

        if image_file_path and label_file_path:
            # 이미지 저장
            image_pil.save(image_file_path)

            label_list = []
            with open(label_txt_path, 'r') as file:
                for line in file:
                    line = line.strip()
                    label_list.append(line)

            # 라벨 텍스트 파일 저장
            with open(label_file_path, 'w') as file:
                for item in labeled_images:
                    label, min_x, min_y, max_x, max_y = item
                    center_x = (min_x + max_x) / 2
                    center_y = (min_y + max_y) / 2
                    w = max_x - min_x
                    h = max_y - min_y
                    normalized_center_x = round(center_x/image_pil_width, 6)
                    normalized_center_y = round(center_y/image_pil_height, 6)
                    normalized_w = round(w/image_pil_width, 6)
                    normalized_h = round(h/image_pil_height, 6)
                    normalized_item = [label_list.index(label), normalized_center_x, normalized_center_y, normalized_w, normalized_h]
                    line = ' '.join(map(str, normalized_item)) + '\n'  # 각 요소를 문자열로 변환하고 띄어쓰기로 구분
                    file.write(line)
            
            my_log("save success!")

    else:
        my_log("save fail.")
        messagebox.showerror("경고", "학습할 데이터를 지정해 주세요.")


def change_save_dir():
    # 파일 저장 경로 재지정
    global save_dir_path
    dir_path = filedialog.askdirectory(initialdir="./data")

    if dir_path:
        save_dir_path = dir_path
        my_log("change save dir!")


def open_save_folder():
    # 파일 저장 경로 폴더 오픈
    if save_dir_path:
        os.startfile(save_dir_path)
        my_log("open save folder.")
    else:
        # 경로 미지정 시 경로 지정 함수 로딩
        change_save_dir()
        open_save_folder()


def start_drag(event):
    image_canvas.scan_mark(event.x, event.y)

def drag_to_scroll(event):
    # 이미지 캔버스를 드래그하여 스크롤합니다.
    image_canvas.scan_dragto(event.x, event.y, gain=1)


def create_rectbox():
    if not create_rectbox.selection_active:
        # create_rectbox 활성화
        image_canvas.unbind("<Button-1>")
        image_canvas.unbind("<B1-Motion>")
        image_canvas.bind("<Button-1>", start_selection)
        image_canvas.bind("<ButtonRelease-1>", end_selection)
        create_rectbox.selection_active = True
        create_rectbox_button.configure(bg="#A0A0A0")  # 버튼 색상을 변경합니다.
    else:
        # create_rectbox 비활성화
        image_canvas.unbind("<Button-1>")
        image_canvas.unbind("<ButtonRelease-1>")
        image_canvas.bind("<Button-1>", start_drag)
        image_canvas.bind("<B1-Motion>", drag_to_scroll)
        create_rectbox.selection_active = False
        create_rectbox_button.configure(bg="SystemButtonFace")  # 버튼 색상을 원래대로 변경합니다.

create_rectbox.selection_active = False


labeled_images = []

def start_selection(event):
    global start_x, start_y
    # 캔버스 좌표에서 이미지 좌표로 변환합니다.
    start_x = image_canvas.canvasx(event.x) // scale
    start_y = image_canvas.canvasy(event.y) // scale


def end_selection(event):
    global start_x, start_y
    # 캔버스 좌표에서 이미지 좌표로 변환합니다.
    end_x = image_canvas.canvasx(event.x) // scale
    end_y = image_canvas.canvasy(event.y) // scale
    if label_entry.get():
        labeled_images.append([label_entry.get(), start_x, start_y, end_x, end_y])
        labeled_image_listbox.insert(tk.END, label_entry.get())

        # 새로운 항목을 추가한 후에 해당 항목을 선택합니다.
        labeled_image_listbox.selection_clear(0, tk.END)  # 기존 선택 해제
        labeled_image_listbox.selection_set(tk.END)
        on_labeled_image_listbox_select()
        create_rectbox()
        my_log("create rectbox.")
    else:
        messagebox.showerror("경고", "라벨을 입력하세요.")


def on_labeled_image_listbox_select(event=None):
    labeled_image_index = labeled_image_listbox.curselection()
    if labeled_image_index:
        label, start_x, start_y, end_x, end_y = labeled_images[labeled_image_index[0]]

        label_entry.delete(0, tk.END)
        label_entry.insert(tk.END, label)

        # 확대 비율에 맞게 사각형 확대
        start_x *= scale
        start_y *= scale
        end_x *= scale
        end_y *= scale

        image_canvas.delete("selection")  # 이전 선택 영역을 삭제합니다.
        image_canvas.create_rectangle(start_x, start_y, end_x, end_y, outline="gray", fill="blue", width=2, tag="selection")
        image_canvas.itemconfig("selection", stipple="gray50")  # 투명한 사각형을 만듭니다.


def delete_rectbox():
    selected_index = labeled_image_listbox.curselection()
    
    if selected_index:
        # 선택된 항목의 인덱스를 가져옵니다.
        index = selected_index[0]

        # labeled_images 리스트에서 선택된 항목을 제거합니다.
        del labeled_images[index]

        # labeled_image_listbox에서 선택된 항목을 삭제합니다.
        labeled_image_listbox.delete(index)

        # 캔버스에서 사각형을 지웁니다.
        image_canvas.delete("selection")

        if index < labeled_image_listbox.size():
            labeled_image_listbox.selection_clear(0, tk.END)  # 기존 선택 해제
            labeled_image_listbox.selection_set(index)  # 다음 항목 선택
        else:
            labeled_image_listbox.selection_set(tk.END)
        on_labeled_image_listbox_select()
        my_log("delete rectbox.")


def zoom_in():
    global scale

    scale += 0.1
    if scale > 5:
        scale = 5
    zoom_entry.delete(0, tk.END)
    zoom_entry.insert(tk.END, int(scale*100))

    image_print()


def zoom_out():
    global scale

    scale -= 0.1
    if scale < 0.1:
        scale = 0.1
    zoom_entry.delete(0, tk.END)
    zoom_entry.insert(tk.END, int(scale*100))

    image_print()


def update_zoom_entry(event):
    if event.keysym == "Return": # "Enter"키 입력 시 이벤트 연결
        update_zoom(event)


def update_zoom(event):
    global scale
    # 엔트리에서 입력된 값을 가져와서 확대 비율로 설정합니다.
    new_scale = float(zoom_entry.get()) / 100
    # 현재 확대 비율을 변경된 값으로 업데이트합니다.
    scale = new_scale
    if scale < 0.1:
        scale = 0.1
    if scale > 5:
        scale = 5
    zoom_entry.delete(0, tk.END)
    zoom_entry.insert(tk.END, int(scale*100))

    image_print()


def original_image():
    # 오리지날 이미지 불러오기
    global image, brightness, toggle_gray_image
    brightness = 1 # 밝기 초기화
    brightness_entry.delete(0, tk.END)
    brightness_entry.insert(tk.END, round(brightness*50))

    image = origin_image.copy()

    # 그레이 이미지 토글 초기화
    if toggle_gray_image:
        gray_image()
    else:
        image_print()
        my_log("original image...")


toggle_gray_image = False

def gray_image():
    global toggle_gray_image
    toggle_gray_image = not toggle_gray_image
    if toggle_gray_image:
        gray_image_button.configure(bg="#A0A0A0")  # 버튼 색상을 변경합니다.
        my_log("gray image...")
    else:
        gray_image_button.configure(bg="SystemButtonFace")
        my_log("original image...")

    image_print()


brightness = 1

def brightly_image():
    global brightness, image
    
    brightness += 0.2 # 밝기를 10% 증가시킵니다.
    if brightness >= 2:
        brightness = 1.999 # 밝기가 100%가 되면 이미지 깨짐 현상 발생
    brightness_entry.delete(0, tk.END)
    brightness_entry.insert(tk.END, round(brightness*50))

    image_print()


def darkly_image():
    global brightness, image

    brightness -= 0.2 # 밝기를 10% 감소시킵니다.
    if brightness < 0:
        brightness = 0
    brightness_entry.delete(0, tk.END)
    brightness_entry.insert(tk.END, round(brightness*50))

    image_print()


def update_brightness_entry(event):
    if event.keysym == "Return":
        update_brightness(event)


def update_brightness(event):
    global brightness, image
    
    new_brightness = float(brightness_entry.get()) / 50
    # 현재 밝기 비율을 변경된 값으로 업데이트합니다.
    brightness = new_brightness
    if brightness < 0:
        brightness = 0
    if brightness >= 2:
        brightness = 1.999
    brightness_entry.delete(0, tk.END)
    brightness_entry.insert(tk.END, round(brightness*50))

    image_print()



selected_data_option = "train"

def handle_data_option_event(event):
    global selected_data_option
    selected_data_option = data_option.get()
    my_log("data option : " + selected_data_option)


def label_add():
    label = label_entry.get()

    if label:
        if label not in label_listbox.get(0, tk.END):
            # 라벨 추가
            label_listbox.insert(tk.END, label)

            # label.txt 라벨 추가
            with open(label_txt_path, 'a', encoding='utf-8') as f:
                f.write(label + '\n')

            # label.yaml 라벨 추가
            with open(label_yaml_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)

            # names에 새로운 항목 추가
            if 'names' in data:
                data['names'].append(label)
            else:
                data['names'] = [label]

            # nc 값 증가
            if 'nc' in data:
                data['nc'] += 1
            else:
                data['nc'] = 1

            with open(label_yaml_path, 'w', encoding='utf-8') as f:
                yaml.dump(data, f, default_flow_style=False, allow_unicode=True)
            
            my_log("add label : " + label)

        else:
            messagebox.showinfo("알림", "이미 존재하는 라벨입니다.")
    else:
        messagebox.showinfo("경고", "라벨을 입력하세요.")


def label_update():
    old_label_index = label_listbox.curselection()
    old_label = label_listbox.get(old_label_index)
    new_label = label_entry.get()

    if old_label and new_label:
        # txt 파일에서 기존 라벨을 수정
        with open(label_txt_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        with open(label_txt_path, 'w', encoding='utf-8') as f:
            for line in lines:
                if line.strip() == old_label:
                    f.write(new_label + '\n')
                else:
                    f.write(line)

        # YAML 파일에서 기존 라벨을 수정
        with open(label_yaml_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)

        if 'names' in data and old_label in data['names']:
            data['names'][data['names'].index(old_label)] = new_label

        with open(label_yaml_path, 'w', encoding='utf-8') as f:
            yaml.dump(data, f, default_flow_style=False, allow_unicode=True)

        # 리스트 박스에서 기존 라벨을 삭제하고 새로운 라벨을 삽입
        label_listbox.delete(old_label_index)
        label_listbox.insert(old_label_index, new_label)

        my_log("label update : " + old_label + "→" + new_label)
    else:
        messagebox.showinfo("경고", "라벨을 입력하세요.")


def label_del():
    label = label_entry.get()

    if label:
        if label in label_listbox.get(0, tk.END):
            label_listbox.delete(label_listbox.get(0, tk.END).index(label))

            # 파일에서 라벨 삭제
            with open(label_txt_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            with open(label_txt_path, 'w', encoding='utf-8') as f:
                for line in lines:
                    if line.strip() != label:
                        f.write(line)

            # YAML 파일에서 라벨 삭제
            with open(label_yaml_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            
            if 'names' in data:
                if label in data['names']:
                    data['names'].remove(label)
            
            if 'nc' in data:
                data['nc'] -= 1

            with open(label_yaml_path, 'w', encoding='utf-8') as f:
                yaml.dump(data, f, default_flow_style=False, allow_unicode=True)
            
            my_log("delete label : " + label)

        else:
            messagebox.showinfo("알림", "삭제할 라벨이 리스트에 없습니다.")
    else:
        messagebox.showinfo("경고", "라벨을 입력하세요.")


def label_list_show():
    # 라벨 텍스트 파일에서 라벨 데이터 불러오기
    with open(label_txt_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    label_listbox.delete(0, tk.END)
    for line in lines:
        label_listbox.insert(tk.END, line.strip())
    
    label_entry.delete(0, tk.END)
    label_entry.insert(0, label_listbox.get(0))
    on_label_entry_change()


def on_label_listbox_select(event):
    # 리스트 박스에서 항목을 선택했을 때 entry 값 설정
    selection = event.widget.curselection()
    if selection:
        index = selection[0]
        data = event.widget.get(index)
        label_entry.delete(0, tk.END)
        label_entry.insert(0, data)


def on_label_entry_click(event):
    # 엔트리를 클릭할 때 리스트 박스의 선택을 다시 설정
    label_listbox.select_set(label_listbox.curselection())


def on_label_entry_change(event=None):
    label = label_entry.get()
    if label in label_listbox.get(0, tk.END):
        index = label_listbox.get(0, tk.END).index(label)
        label_listbox.selection_clear(0, tk.END)  # 기존 선택 해제
        label_listbox.selection_set(index)  # 새로운 값 선택
        label_listbox.see(index)  # 선택된 항목이 보이도록 스크롤 조정


def file_listbox_selected(event=None):
    selected_index = file_listbox.curselection()  # 선택된 아이템의 인덱스를 가져옵니다.
    if selected_index:
        selected_item = file_listbox.get(selected_index)  # 선택된 아이템의 내용을 가져옵니다.
        load_media(selected_item)  # 선택된 아이템에 해당하는 이미지를 출력합니다.


def my_log(msg):
    text_log.insert(tk.INSERT, msg + "\r\n")
    text_log.see("end")











def on_key(event):
    # Control키와 Shift키와 동시에 눌렀을 때
    if event.keysym == 'O' and (event.state & 0x4) != 0 and (event.state & 0x1) != 0: # 0x1은 Shift 키
        dir_open()

    # Control키와 동시에 눌렀을 때
    if (event.state & 0x4) != 0: # 0x4는 Control 키
        if event.keysym == 's':
            save_file()
        if event.keysym == 'o':
            file_open()

    # 단일 키
    if event.keysym == 'w':
        create_rectbox()
    if event.keysym == 'q':
        prev_file()
    if event.keysym == 'e':
        next_file()

    if not is_image:
        if event.keysym == 'space':
            toggle_play()
        if event.keysym == 'Right':
            next_frame()
        if event.keysym == 'Left':
            prev_frame()



def next_frame():
    global cap
    if cap.isOpened():
        # 현재 프레임 위치
        current_frame = cap.get(cv2.CAP_PROP_POS_FRAMES)
        # 다음 프레임으로 이동
        cap.set(cv2.CAP_PROP_POS_FRAMES, current_frame + 150)

def prev_frame():
    global cap
    if cap.isOpened():
        # 현재 프레임 위치
        current_frame = cap.get(cv2.CAP_PROP_POS_FRAMES)
        # 이전 프레임으로 이동
        cap.set(cv2.CAP_PROP_POS_FRAMES, max(0, current_frame - 150))








top = tk.Tk()
top.title("Data Preprocessing")

setting_frame = tk.Frame(top)
setting_frame.grid(row=0, column=0, padx=5, pady=5)

# 이미지 비디오 토글 버튼
toggle_image_video_button = tk.Button(setting_frame, text="Image", width=12, height=2, bg="#FFFFEE", command=toggle_image_video)
toggle_image_video_button.pack()

# 이미지 로드
file_open_button = tk.Button(setting_frame, text="Open File", width=12, height=2, command=file_open)
file_open_button.pack()

dir_open_button = tk.Button(setting_frame, text="Dir Open", width=12, height=2, command=dir_open)
dir_open_button.pack()



separator_frame = tk.Frame(setting_frame, height=3, bg="white")
separator_frame.pack(fill=tk.X, pady=(5, 5))


# 앞뒤 이미지 로드
next_image_button = tk.Button(setting_frame, text="Next File", width=12, height=2, command=next_file)
next_image_button.pack()

prev_image_button = tk.Button(setting_frame, text="Prev File", width=12, height=2, command=prev_file)
prev_image_button.pack()



separator_frame1 = tk.Frame(setting_frame, height=3, bg="white")
separator_frame1.pack(fill=tk.X, pady=(5, 5))


# 이미지 저장
save_button = tk.Button(setting_frame, text="Save", width=12, height=2, command=save_file)
save_button.pack()

change_save_dir_button = tk.Button(setting_frame, text="Change Save Dir", width=12, height=2, command=change_save_dir)
change_save_dir_button.pack()

open_save_folder_button = tk.Button(setting_frame, text="Open Save Folder", width=12, height=2, command=open_save_folder)
open_save_folder_button.pack()



separator_frame2 = tk.Frame(setting_frame, height=3, bg="white")
separator_frame2.pack(fill=tk.X, pady=(5, 5))


# 이미지 선택 사각형 그리기
create_rectbox_button = tk.Button(setting_frame, text="Create Rectbox", width=12, height=2, command=create_rectbox)
create_rectbox_button.pack()

delete_rectbox_button = tk.Button(setting_frame, text="Delete Rectbox", width=12, height=2, command=delete_rectbox)
delete_rectbox_button.pack()



separator_frame3 = tk.Frame(setting_frame, height=3, bg="white")
separator_frame3.pack(fill=tk.X, pady=(5, 5))


# 줌
zoom_in_button = tk.Button(setting_frame, text="Zoom In", width=12, height=2, command=zoom_in)
zoom_in_button.pack()

zoom_frame = tk.Frame(setting_frame, width=12)
zoom_frame.pack()

zoom_entry = tk.Entry(zoom_frame, width=5)
zoom_entry.insert(tk.END, int(scale*100))
zoom_entry.pack(side=tk.LEFT)
zoom_entry.bind("<KeyRelease-Return>", update_zoom_entry)

zoom_percent_label = tk.Label(zoom_frame, width=4, text="%")
zoom_percent_label.pack(side=tk.LEFT)

zoom_out_button = tk.Button(setting_frame, text="Zoom Out", width=12, height=2, command=zoom_out)
zoom_out_button.pack()



separator_frame4 = tk.Frame(setting_frame, height=3, bg="white")
separator_frame4.pack(fill=tk.X, pady=(5, 5))


# 이미지 에디터
original_image_button = tk.Button(setting_frame, text="Original", width=12, height=2, command=original_image)
original_image_button.pack()

gray_image_button = tk.Button(setting_frame, text="Gray", width=12, height=2, command=gray_image)
gray_image_button.pack()

brightly_image_button = tk.Button(setting_frame, text="Brightly", width=12, height=2, command=brightly_image)
brightly_image_button.pack()

brightness_frame = tk.Frame(setting_frame, width=12)
brightness_frame.pack()

brightness_entry = tk.Entry(brightness_frame, width=5)
brightness_entry.insert(tk.END, int(brightness*50))
brightness_entry.pack(side=tk.LEFT)
brightness_entry.bind("<KeyRelease-Return>", update_brightness_entry)

brightness_percent_label = tk.Label(brightness_frame, width=4, text="%")
brightness_percent_label.pack(side=tk.LEFT)

darkly_image_button = tk.Button(setting_frame, text="Darkly", width=12, height=2, command=darkly_image)
darkly_image_button.pack()



# 이미지 캔버스
create_image_canvas_frame()




label_frame = tk.Frame(top)
label_frame.grid(row=0, column=2, padx=5, pady=5)

# 학습 데이터 분류
data_option_label = tk.Label(label_frame, text="Data Option")
data_option_label.grid(row=0, column=0, columnspan=4, sticky="w")

data_option = tk.StringVar()

data_option_combobox = ttk.Combobox(label_frame, textvariable=data_option, width=22) #콤보박스 선언
data_option_combobox['value'] = ('train','valid','test') #콤보박스 요소 삽입
data_option_combobox.current(0) #0번째로 콤보박스 초기화
data_option_combobox.grid(row=1, column=0, columnspan=4) #콤보박스 배치

data_option_combobox.bind("<<ComboboxSelected>>", handle_data_option_event)



separator_frame_label = tk.Frame(label_frame, height=3, bg="white")
separator_frame_label.grid(row=2, column=0, columnspan=4, pady=(5, 5), sticky="ew")



# 라벨링한 이미지 박스
labeled_image_label = tk.Label(label_frame, text="Labeled Image")
labeled_image_label.grid(row=3, column=0, columnspan=4, sticky="w")

labeled_image_listbox = tk.Listbox(label_frame, width=25, height=7, selectmode="single", exportselection=False)
labeled_image_listbox.grid(row=4, column=0, columnspan=4)
labeled_image_listbox.bind("<<ListboxSelect>>", on_labeled_image_listbox_select)



separator_frame_label1 = tk.Frame(label_frame, height=3, bg="white")
separator_frame_label1.grid(row=5, column=0, columnspan=4, pady=(5, 5), sticky="ew")


# 라벨 리스트 박스
label_label = tk.Label(label_frame, text="Label")
label_label.grid(row=6, column=0, columnspan=4, sticky="w")

label_entry = tk.Entry(label_frame)
label_entry.grid(row=7, column=0, columnspan=3)
label_entry.bind("<Button-1>", on_label_entry_click)
label_entry.bind("<KeyRelease>", on_label_entry_change)

label_add_button = tk.Button(label_frame, text="+", width=3, command=label_add)
label_add_button.grid(row=7, column=3)

label_listbox = tk.Listbox(label_frame, width=25, height=7, selectmode="single", exportselection=False)
label_listbox.grid(row=8, column=0, columnspan=4)
label_listbox.bind("<<ListboxSelect>>", on_label_listbox_select)

label_edit_button = tk.Button(label_frame, text="Update", width=11, height=2, command=label_update)
label_edit_button.grid(row=9, column=0, columnspan=2)

label_del_button = tk.Button(label_frame, text="Delete", width=11, height=2, command=label_del)
label_del_button.grid(row=9, column=2, columnspan=2)

label_list_show()



separator_frame_label2 = tk.Frame(label_frame, height=3, bg="white")
separator_frame_label2.grid(row=10, column=0, columnspan=4, pady=(5, 5), sticky="ew")


# 파일 리스트 박스
file_list_label = tk.Label(label_frame, text="File List")
file_list_label.grid(row=11, column=0, columnspan=4, sticky="w")

file_listbox = tk.Listbox(label_frame, width=25, selectmode="single", exportselection=False)
file_listbox.grid(row=12, column=0, columnspan=4)
file_listbox.bind("<<ListboxSelect>>", file_listbox_selected)



# 로그
text_log_label = tk.Label(label_frame, text="Text Log")
text_log_label.grid(row=13, column=0, columnspan=4, sticky="w")

text_log = st.ScrolledText(label_frame,
                            width = 26,
                            height = 8,
                            font = ("Times New Roman",10))
text_log.grid(row=14, column=0, columnspan=4)



my_log("start data preprocessing...")

# 키보드 이벤트 바인딩
top.bind('<Key>', on_key)




top.mainloop()