import tkinter as tk
from tkinter import messagebox, filedialog, ttk
import tkinter.scrolledtext as st
import cv2
from PIL import Image, ImageTk
import os
import numpy as np
import yaml
import threading





class Preprocess():
    def __init__(self, top):
        self.top = top

        self.label_txt_path = "label.txt"
        self.label_yaml_path = "label.yaml"
        self.save_dir_path = ""

        self.height = 0
        self.width = 0
        self.scale = 1
        self.origin_image = None
        self.image = None
        self.cap = None

        self.video_playing = False
        self.is_image = True

        self.selection_active = False

        self.labeled_images = []
        self.toggle_gray_image = False
        self.brightness = 1
        self.selected_data_option = "train"

        self.create_gui()


    def toggle_image_video(self):
        self.is_image = not self.is_image
        if self.is_image:
            self.toggle_image_video_button.config(text="Image")
            self.my_log("Image Data Preprocessing...")
            self.reset()
            self.create_image_canvas_frame()
        else:
            self.toggle_image_video_button.config(text="Video")
            self.my_log("Video Data Preprocessing...")
            self.reset()
            self.create_video_canvas_frame()


    def create_image_canvas_frame(self):
        self.image_canvas_frame = tk.Frame(self.top, width=980, height=560)
        self.image_canvas_frame.grid(row=0, column=1, padx=20, pady=10)

        self.image_canvas = tk.Canvas(self.image_canvas_frame, width=960, height=540, background="white")
        self.image_canvas.grid(row=0, column=0)

        self.yscrollbar = tk.Scrollbar(self.image_canvas_frame, orient="vertical", command=self.image_canvas.yview)
        self.yscrollbar.grid(row=0, column=1, sticky="ns")

        self.xscrollbar = tk.Scrollbar(self.image_canvas_frame, orient="horizontal", command=self.image_canvas.xview)
        self.xscrollbar.grid(row=1, column=0, sticky="ew")

        self.image_canvas.configure(yscrollcommand=self.yscrollbar.set, xscrollcommand=self.xscrollbar.set)
        self.image_canvas.configure(scrollregion=self.image_canvas.bbox("all"))
        # 드래그 스크롤 바인딩
        self.image_canvas.bind("<Button-1>", self.start_drag)
        self.image_canvas.bind("<B1-Motion>", self.drag_to_scroll)


    def create_video_canvas_frame(self):
        self.image_canvas_frame = tk.Frame(self.top, width=980, height=560)
        self.image_canvas_frame.grid(row=0, column=1, padx=20, pady=10)

        # 영상 캔버스 생성
        self.image_canvas = tk.Canvas(self.image_canvas_frame, width=960, height=540, background="black")
        self.image_canvas.grid(row=0, column=0)
        # 영상 제어 위젯을 담을 프레임 생성
        self.video_controls_frame = tk.Frame(self.image_canvas_frame)
        self.video_controls_frame.grid(row=1, column=0, sticky="ew", pady=(5, 0))

        self.frame_slider = tk.Scale(self.video_controls_frame, from_=1, to=1, orient="horizontal", command=self.move_to_frame)
        self.frame_slider.pack(side="top", fill="x", padx=10, pady=5)

        # 버튼 그룹을 생성하고 배치합니다.
        self.button_group = tk.Frame(self.video_controls_frame)
        self.button_group.pack(side="top", padx=10, pady=5)

        self.prev_frame_button = tk.Button(self.button_group, text="⏪", width=5, command=self.prev_frame)
        self.prev_frame_button.pack(side="left", padx=(0, 5))

        self.pause_button = tk.Button(self.button_group, text="▶", width=5, command=self.toggle_play)
        self.pause_button.pack(side="left", padx=(0, 5))

        self.next_frame_button = tk.Button(self.button_group, text="⏩", width=5, command=self.next_frame)
        self.next_frame_button.pack(side="left", padx=(0, 5))


    def configure_frame_slider(self):
        max_frame = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.frame_slider.config(to=max_frame)


    def move_to_frame(self, frame_number):
        frame_number = int(frame_number)
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number - 1)


    def reset(self):
        self.file_listbox.delete(0, tk.END) # 파일 목록 초기화
        self.image_canvas.delete("all") # 이미지 캔버스 초기화
        # 라벨링 이미지 초기화
        self.labeled_images = []
        self.labeled_image_listbox.delete(0, tk.END)
        # 변수 초기화
        if self.cap:
            self.cap.release()
        self.image = None
        self.origin_image = None
        self.scale = 1
        self.zoom_entry.delete(0, tk.END)
        self.zoom_entry.insert(tk.END, int(self.scale*100))
        self.height = 0
        self.width = 0
        self.brightness = 1
        self.brightness_entry.delete(0, tk.END)
        self.brightness_entry.insert(tk.END, round(self.brightness*50))
        self.my_log("Reset...")


    def load_media(self, media_path):
        if self.is_image:
            self.load_image(media_path)
        else:
            self.load_video(media_path)


    def load_image(self, image_path):
        # 이미지 로드
        self.image = cv2.imread(image_path)
        self.image = cv2.cvtColor(self.image, cv2.COLOR_BGR2RGB)

        # 오리지날 이미지 저장
        self.origin_image = self.image.copy()

        self.height, self.width, _ = self.image.shape

        # 이미지 캔버스에 이미지가 없는 경우에만 이미지 크기 조정
        if not self.image_canvas.find_all():
            # 이미지 크기 조정 (캔버스 크기에 맞게)
            self.scale = min(self.scale, 1000.0 / max(self.height, self.width))
            self.zoom_entry.delete(0, tk.END)
            self.zoom_entry.insert(tk.END, int(self.scale*100))

        # 라벨링 이미지 초기화
        self.labeled_images = []
        self.labeled_image_listbox.delete(0, tk.END)

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
            with open(self.label_txt_path, 'r') as file:
                for line in file:
                    line = line.strip()
                    label_list.append(line)

            with open(label_file_path, 'r') as file:
                for line in file:
                    # 각 줄에서 띄어쓰기를 기준으로 리스트 생성
                    line_list = line.strip().split()

                    label_index, normalized_center_x, normalized_center_y, normalized_w, normalized_h = line_list

                    center_x = float(normalized_center_x) * self.width
                    center_y = float(normalized_center_y) * self.height
                    w = float(normalized_w) * self.width
                    h = float(normalized_h) * self.height

                    converted_line = [label_list[int(label_index)], center_x-w//2, center_y-h//2, center_x+w//2, center_y+h//2]
                    
                    # 이미지 라벨 리스트박스에 추가
                    self.labeled_images.append(converted_line)
                    self.labeled_image_listbox.insert(tk.END, converted_line[0])
            self.my_log("loading labels...")
        else:
            self.my_log("no label file.")

        self.my_log("load image : " + image_path)
        self.image_print()


    def load_video(self, video_path):
        # 기존 캡처 객체가 존재하는지 확인하고 있으면 해제
        if self.cap and self.cap.isOpened():
            self.cap.release()
        
        # 비디오 캡처 객체 생성
        self.cap = cv2.VideoCapture(video_path)

        # 비디오 캡처 객체가 성공적으로 열렸는지 확인
        if not self.cap.isOpened():
            messagebox.showerror("경고", "비디오 파일을 열 수 없습니다.")
            return

        # 비디오 프레임의 너비와 높이
        self.width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        # 이미지 캔버스에 이미지가 없는 경우에만 이미지 크기 조정
        if not self.image_canvas.find_all():
            # 이미지 크기 조정 (캔버스 크기에 맞게)
            self.scale = min(self.scale, 1000.0 / max(self.height, self.width))
            self.zoom_entry.delete(0, tk.END)
            self.zoom_entry.insert(tk.END, int(self.scale*100))
        
        self.video_width, self.video_height = int(self.width * self.scale), int(self.height * self.scale)

        # 캔버스 초기화
        self.image_canvas.delete("all")

        # 비디오 재생
        self.my_log("load video : " + video_path)
        self.configure_frame_slider()
        if not self.video_playing:
            self.toggle_play()
        else:
            self.play_video_thread()


    def toggle_play(self):
        self.video_playing = not self.video_playing
        if self.video_playing:
            self.pause_button.config(text="⏸️")
            self.play_video_thread()

        else:
            self.pause_button.config(text="▶")


    def play_video_thread(self):
        self.video_thread = threading.Thread(target=self.play_video)
        self.video_thread.daemon = True
        self.video_thread.start()


    def play_video(self):
        # 라벨링 이미지 초기화
        if self.labeled_images:
            self.labeled_images = []
            self.labeled_image_listbox.delete(0, tk.END)

        if self.cap.isOpened() and self.video_playing:
            # 비디오에서 프레임 읽기
            ret, frame = self.cap.read()

            if ret:
                self.image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

                resized_image = cv2.resize(self.image, (self.video_width, self.video_height))
                # OpenCV 이미지를 PIL 이미지로 변환
                pil_image = Image.fromarray(resized_image)

                # PIL 이미지를 tkinter PhotoImage로 변환
                photo = ImageTk.PhotoImage(image=pil_image)

                # 이미지를 캔버스에 출력합니다.
                self.image_canvas.create_image(0, 0, anchor=tk.NW, image=photo)
                self.image_canvas.image = photo

                # 다음 프레임 재생
                self.top.after(15, self.play_video_thread)

                # 프레임 슬라이더 업데이트
                if self.cap.get(cv2.CAP_PROP_POS_FRAMES) % 50 == 0:
                    current_frame = int(self.cap.get(cv2.CAP_PROP_POS_FRAMES))
                    self.frame_slider.set(current_frame)
            else:
                # 비디오가 종료되면 재생 중지
                self.toggle_play()
                self.cap.release()
                self.my_log("video close...")
        else:
            self.origin_image = self.image.copy()
            self.image_print()


    def image_print(self):
        if self.toggle_gray_image:
            self.image = cv2.cvtColor(self.image, cv2.COLOR_BGR2GRAY)
        else:
            self.image = self.origin_image.copy()

        resized_image = cv2.resize(self.image, (int(self.width * self.scale), int(self.height * self.scale)))

        # 밝기 조정
        adjust_image = np.clip(resized_image * self.brightness, 0, 255).astype(np.uint8)

        # OpenCV 이미지를 PIL 이미지로 변환
        pil_image = Image.fromarray(adjust_image)

        # PIL 이미지를 tkinter PhotoImage로 변환
        photo = ImageTk.PhotoImage(image=pil_image)

        # 이미지를 캔버스에 출력합니다.
        self.image_canvas.create_image(0, 0, anchor=tk.NW, image=photo)
        self.image_canvas.image = photo

        # 이미지의 크기를 기반으로 캔버스의 스크롤 영역을 설정합니다.
        self.image_canvas.config(scrollregion=(0, 0, photo.width(), photo.height()))


    def file_open(self):
        if self.is_image:
            # 이미지 파일 확장자
            filetypes = [("Image files", "*.jpg;*.jpeg;*.png;*.gif;*.bmp")]
        else:
            # 동영상 파일 확장자
            filetypes = [("Video files", "*.mp4;*.avi;*.mov")]

        file_paths = filedialog.askopenfilenames(initialdir="./data", filetypes=filetypes)
        if file_paths:
            self.file_listbox.delete(0, tk.END)
            for file_path in file_paths:
                self.file_listbox.insert(tk.END, file_path)
            self.file_listbox.selection_set(0)  # 첫 번째 아이템 선택
            self.file_listbox_selected()
            self.my_log("open file : " + file_path)


    def dir_open(self):
        if self.is_image:
            # 이미지 파일 확장자
            extensions = [".jpg", ".jpeg", ".png", ".gif", ".bmp"]
        else:
            # 동영상 파일 확장자
            extensions = [".mp4", ".avi", ".mov"]

        dir_path = filedialog.askdirectory(initialdir="./data")
        if dir_path:
            self.my_log("open dir : " + dir_path)
            self.file_listbox.delete(0, tk.END)
            for file_name in os.listdir(dir_path):
                file_path = os.path.join(dir_path, file_name)

                # 파일이 이미지 파일인지 확인
                if os.path.isfile(file_path) and file_name.lower().endswith(tuple(extensions)):
                    self.file_listbox.insert(tk.END, file_path)
            self.file_listbox.selection_set(0)  # 첫 번째 아이템 선택
            self.file_listbox_selected()


    def next_file(self):
        # 현재 선택된 아이템의 인덱스를 가져옵니다.
        selected_index = self.file_listbox.curselection()
        if selected_index:
            # 다음 아이템의 인덱스를 계산합니다.
            next_index = selected_index[0] + 1
            # 다음 아이템이 리스트박스의 범위를 넘어가지 않도록 조정합니다.
            if next_index < self.file_listbox.size():
                # 다음 아이템을 선택합니다.
                self.file_listbox.selection_clear(0, tk.END)
                self.file_listbox.selection_set(next_index)
                self.file_listbox.activate(next_index)
                # 선택된 아이템에 해당하는 이미지를 출력합니다.
                self.file_listbox_selected()
                # 선택된 아이템이 화면에 표시되도록 스크롤바를 이동시킵니다.
                self.file_listbox.see(next_index)
                self.my_log("next image...")


    def prev_file(self):
        # 현재 선택된 아이템의 인덱스를 가져옵니다.
        selected_index = self.file_listbox.curselection()
        if selected_index:
            # 이전 아이템의 인덱스를 계산합니다.
            prev_index = selected_index[0] - 1
            # 이전 아이템이 리스트박스의 범위를 넘어가지 않도록 조정합니다.
            if prev_index >= 0:
                # 다음 아이템을 선택합니다.
                self.file_listbox.selection_clear(0, tk.END)
                self.file_listbox.selection_set(prev_index)
                self.file_listbox.activate(prev_index)
                # 선택된 아이템에 해당하는 이미지를 출력합니다.
                self.file_listbox_selected()
                # 선택된 아이템이 화면에 표시되도록 스크롤바를 이동시킵니다.
                self.file_listbox.see(prev_index)
                self.my_log("prev image")


    def save_file(self):
        if self.labeled_images:
            # grab_image를 numpy 배열에서 PIL 이미지로 변환
            image_pil = Image.fromarray(self.image)
            image_pil_width, image_pil_height = image_pil.size

            file_name = "data.jpg"
            
            if self.save_dir_path:
                # train, valid, test 데이터 셋 나누기
                data_save_dir_path = os.path.join(self.save_dir_path, self.selected_data_option)
                # 폴더가 없으면 생성
                if not os.path.exists(data_save_dir_path):
                    os.makedirs(data_save_dir_path)
                    self.my_log("make dir : " + data_save_dir_path)

                image_save_path = os.path.join(data_save_dir_path, "images")
                label_save_path = os.path.join(data_save_dir_path, "labels")

                # 폴더가 없으면 생성
                if not os.path.exists(image_save_path):
                    os.makedirs(image_save_path)
                    self.my_log("make dir : " + image_save_path)
                
                if not os.path.exists(label_save_path):
                    os.makedirs(label_save_path)
                    self.my_log("make dir : " + label_save_path)

                image_file_path = os.path.join(image_save_path, file_name)
                base, ext = os.path.splitext(file_name)
                label_text_file_name = base + ".txt"
                label_file_path = os.path.join(label_save_path, label_text_file_name)

            else:
                self.change_save_dir()
                self.save_file()
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
                with open(self.label_txt_path, 'r') as file:
                    for line in file:
                        line = line.strip()
                        label_list.append(line)

                # 라벨 텍스트 파일 저장
                with open(label_file_path, 'w') as file:
                    for item in self.labeled_images:
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
                
                self.my_log("save success!")

        else:
            self.my_log("save fail.")
            messagebox.showerror("경고", "학습할 데이터를 지정해 주세요.")


    def change_save_dir(self):
        # 파일 저장 경로 재지정
        dir_path = filedialog.askdirectory(initialdir="./data")

        if dir_path:
            self.save_dir_path = dir_path
            self.my_log("change save dir!")


    def open_save_folder(self):
        # 파일 저장 경로 폴더 오픈
        if self.save_dir_path:
            os.startfile(self.save_dir_path)
            self.my_log("open save folder.")
        else:
            # 경로 미지정 시 경로 지정 함수 로딩
            self.change_save_dir()
            self.open_save_folder()


    def start_drag(self, event):
        self.image_canvas.scan_mark(event.x, event.y)

    def drag_to_scroll(self, event):
        # 이미지 캔버스를 드래그하여 스크롤합니다.
        self.image_canvas.scan_dragto(event.x, event.y, gain=1)


    def create_rectbox(self):
        if not self.selection_active:
            # create_rectbox 활성화
            self.image_canvas.unbind("<Button-1>")
            self.image_canvas.unbind("<B1-Motion>")
            self.image_canvas.bind("<Button-1>", self.start_selection)
            self.image_canvas.bind("<ButtonRelease-1>", self.end_selection)
            self.selection_active = True
            self.create_rectbox_button.configure(bg="#A0A0A0")  # 버튼 색상을 변경합니다.
        else:
            # create_rectbox 비활성화
            self.image_canvas.unbind("<Button-1>")
            self.image_canvas.unbind("<ButtonRelease-1>")
            self.image_canvas.bind("<Button-1>", self.start_drag)
            self.image_canvas.bind("<B1-Motion>", self.drag_to_scroll)
            self.selection_active = False
            self.create_rectbox_button.configure(bg="SystemButtonFace")  # 버튼 색상을 원래대로 변경합니다.


    def start_selection(self, event):
        # 캔버스 좌표에서 이미지 좌표로 변환합니다.
        self.start_x = self.image_canvas.canvasx(event.x) // self.scale
        self.start_y = self.image_canvas.canvasy(event.y) // self.scale


    def end_selection(self, event):
        # 캔버스 좌표에서 이미지 좌표로 변환합니다.
        end_x = self.image_canvas.canvasx(event.x) // self.scale
        end_y = self.image_canvas.canvasy(event.y) // self.scale
        if self.label_entry.get() in self.label_listbox.get(0, tk.END):  # 라벨이 리스트박스안에 있는지 체크
            self.labeled_images.append([self.label_entry.get(), self.start_x, self.start_y, end_x, end_y])
            self.labeled_image_listbox.insert(tk.END, self.label_entry.get())

            # 새로운 항목을 추가한 후에 해당 항목을 선택합니다.
            self.labeled_image_listbox.selection_clear(0, tk.END)  # 기존 선택 해제
            self.labeled_image_listbox.selection_set(tk.END)
            self.on_labeled_image_listbox_select()
            self.create_rectbox()
            self.my_log("create rectbox.")
        else:
            messagebox.showerror("경고", "라벨을 확인해 주세요.")


    def on_labeled_image_listbox_select(self, event=None):
        labeled_image_index = self.labeled_image_listbox.curselection()
        if labeled_image_index:
            label, start_x, start_y, end_x, end_y = self.labeled_images[labeled_image_index[0]]

            self.label_entry.delete(0, tk.END)
            self.label_entry.insert(tk.END, label)

            # 확대 비율에 맞게 사각형 확대
            start_x *= self.scale
            start_y *= self.scale
            end_x *= self.scale
            end_y *= self.scale

            self.image_canvas.delete("selection")  # 이전 선택 영역을 삭제합니다.
            self.image_canvas.create_rectangle(start_x, start_y, end_x, end_y, outline="gray", fill="blue", width=2, tag="selection")
            self.image_canvas.itemconfig("selection", stipple="gray50")  # 투명한 사각형을 만듭니다.


    def delete_rectbox(self):
        selected_index = self.labeled_image_listbox.curselection()
        
        if selected_index:
            # 선택된 항목의 인덱스를 가져옵니다.
            index = selected_index[0]

            # labeled_images 리스트에서 선택된 항목을 제거합니다.
            del self.labeled_images[index]

            # labeled_image_listbox에서 선택된 항목을 삭제합니다.
            self.labeled_image_listbox.delete(index)

            # 캔버스에서 사각형을 지웁니다.
            self.image_canvas.delete("selection")

            if index < self.labeled_image_listbox.size():
                self.labeled_image_listbox.selection_clear(0, tk.END)  # 기존 선택 해제
                self.labeled_image_listbox.selection_set(index)  # 다음 항목 선택
            else:
                self.labeled_image_listbox.selection_set(tk.END)
            self.on_labeled_image_listbox_select()
            self.my_log("delete rectbox.")


    def zoom_in(self):
        self.scale += 0.1
        if self.scale > 5:
            self.scale = 5
        self.zoom_entry.delete(0, tk.END)
        self.zoom_entry.insert(tk.END, int(self.scale*100))

        self.image_print()


    def zoom_out(self):
        self.scale -= 0.1
        if self.scale < 0.1:
            self.scale = 0.1
        self.zoom_entry.delete(0, tk.END)
        self.zoom_entry.insert(tk.END, int(self.scale*100))

        self.image_print()


    def update_zoom_entry(self, event):
        if event.keysym == "Return": # "Enter"키 입력 시 이벤트 연결
            self.update_zoom(event)


    def update_zoom(self, event):
        # 엔트리에서 입력된 값을 가져와서 확대 비율로 설정합니다.
        new_scale = float(self.zoom_entry.get()) / 100
        # 현재 확대 비율을 변경된 값으로 업데이트합니다.
        self.scale = new_scale
        if self.scale < 0.1:
            self.scale = 0.1
        if self.scale > 5:
            self.scale = 5
        self.zoom_entry.delete(0, tk.END)
        self.zoom_entry.insert(tk.END, int(self.scale*100))

        self.image_print()


    def original_image(self):
        # 오리지날 이미지 불러오기
        self.brightness = 1 # 밝기 초기화
        self.brightness_entry.delete(0, tk.END)
        self.brightness_entry.insert(tk.END, round(self.brightness*50))

        self.image = self.origin_image.copy()

        # 그레이 이미지 토글 초기화
        if self.toggle_gray_image:
            self.gray_image()
        else:
            self.image_print()
            self.my_log("original image...")


    def gray_image(self):
        self.toggle_gray_image = not self.toggle_gray_image
        if self.toggle_gray_image:
            self.gray_image_button.configure(bg="#A0A0A0")  # 버튼 색상을 변경합니다.
            self.my_log("gray image...")
        else:
            self.gray_image_button.configure(bg="SystemButtonFace")
            self.my_log("original image...")

        self.image_print()


    def brightly_image(self):
        self.brightness += 0.2 # 밝기를 10% 증가시킵니다.
        if self.brightness >= 2:
            self.brightness = 1.999 # 밝기가 100%가 되면 이미지 깨짐 현상 발생
        self.brightness_entry.delete(0, tk.END)
        self.brightness_entry.insert(tk.END, round(self.brightness*50))

        self.image_print()


    def darkly_image(self):
        self.brightness -= 0.2 # 밝기를 10% 감소시킵니다.
        if self.brightness < 0:
            self.brightness = 0
        self.brightness_entry.delete(0, tk.END)
        self.brightness_entry.insert(tk.END, round(self.brightness*50))

        self.image_print()


    def update_brightness_entry(self, event):
        if event.keysym == "Return":
            self.update_brightness(event)


    def update_brightness(self, event):
        new_brightness = float(self.brightness_entry.get()) / 50
        # 현재 밝기 비율을 변경된 값으로 업데이트합니다.
        self.brightness = new_brightness
        if self.brightness < 0:
            self.brightness = 0
        if self.brightness >= 2:
            self.brightness = 1.999
        self.brightness_entry.delete(0, tk.END)
        self.brightness_entry.insert(tk.END, round(self.brightness*50))

        self.image_print()


    def handle_data_option_event(self, event):
        self.selected_data_option = self.data_option.get()
        self.my_log("data option : " + self.selected_data_option)


    def label_add(self):
        label = self.label_entry.get()

        if label:
            if label not in self.label_listbox.get(0, tk.END):
                # 라벨 추가
                self.label_listbox.insert(tk.END, label)

                # label.txt 라벨 추가
                with open(self.label_txt_path, 'a', encoding='utf-8') as f:
                    f.write(label + '\n')

                # label.yaml 라벨 추가
                with open(self.label_yaml_path, 'r', encoding='utf-8') as f:
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

                with open(self.label_yaml_path, 'w', encoding='utf-8') as f:
                    yaml.dump(data, f, default_flow_style=False, allow_unicode=True)
                
                self.my_log("add label : " + label)

            else:
                messagebox.showinfo("알림", "이미 존재하는 라벨입니다.")
        else:
            messagebox.showinfo("경고", "라벨을 입력하세요.")


    def label_update(self):
        old_label_index = self.label_listbox.curselection()
        old_label = self.label_listbox.get(old_label_index)
        new_label = self.label_entry.get()

        if old_label and new_label:
            # txt 파일에서 기존 라벨을 수정
            with open(self.label_txt_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            with open(self.label_txt_path, 'w', encoding='utf-8') as f:
                for line in lines:
                    if line.strip() == old_label:
                        f.write(new_label + '\n')
                    else:
                        f.write(line)

            # YAML 파일에서 기존 라벨을 수정
            with open(self.label_yaml_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)

            if 'names' in data and old_label in data['names']:
                data['names'][data['names'].index(old_label)] = new_label

            with open(self.label_yaml_path, 'w', encoding='utf-8') as f:
                yaml.dump(data, f, default_flow_style=False, allow_unicode=True)

            # 리스트 박스에서 기존 라벨을 삭제하고 새로운 라벨을 삽입
            self.label_listbox.delete(old_label_index)
            self.label_listbox.insert(old_label_index, new_label)

            self.my_log("label update : " + old_label + "→" + new_label)
        else:
            messagebox.showinfo("경고", "라벨을 입력하세요.")


    def label_del(self):
        label = self.label_entry.get()

        if label:
            if label in self.label_listbox.get(0, tk.END):
                self.label_listbox.delete(self.label_listbox.get(0, tk.END).index(label))

                # 파일에서 라벨 삭제
                with open(self.label_txt_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                with open(self.label_txt_path, 'w', encoding='utf-8') as f:
                    for line in lines:
                        if line.strip() != label:
                            f.write(line)

                # YAML 파일에서 라벨 삭제
                with open(self.label_yaml_path, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f)
                
                if 'names' in data:
                    if label in data['names']:
                        data['names'].remove(label)
                
                if 'nc' in data:
                    data['nc'] -= 1

                with open(self.label_yaml_path, 'w', encoding='utf-8') as f:
                    yaml.dump(data, f, default_flow_style=False, allow_unicode=True)
                
                self.my_log("delete label : " + label)

            else:
                messagebox.showinfo("알림", "삭제할 라벨이 리스트에 없습니다.")
        else:
            messagebox.showinfo("경고", "라벨을 입력하세요.")


    def label_list_show(self):
        # 라벨 텍스트 파일에서 라벨 데이터 불러오기
        with open(self.label_txt_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        self.label_listbox.delete(0, tk.END)
        for line in lines:
            self.label_listbox.insert(tk.END, line.strip())
        
        self.label_entry.delete(0, tk.END)
        self.label_entry.insert(0, self.label_listbox.get(0))
        self.on_label_entry_change()


    def on_label_listbox_select(self, event):
        # 리스트 박스에서 항목을 선택했을 때 entry 값 설정
        selection = event.widget.curselection()
        if selection:
            index = selection[0]
            data = event.widget.get(index)
            self.label_entry.delete(0, tk.END)
            self.label_entry.insert(0, data)


    def on_label_entry_click(self, event):
        # 엔트리를 클릭할 때 리스트 박스의 선택을 다시 설정
        self.label_listbox.select_set(self.label_listbox.curselection())


    def on_label_entry_change(self, event=None):
        label = self.label_entry.get()
        if label in self.label_listbox.get(0, tk.END):
            index = self.label_listbox.get(0, tk.END).index(label)
            self.label_listbox.selection_clear(0, tk.END)  # 기존 선택 해제
            self.label_listbox.selection_set(index)  # 새로운 값 선택
            self.label_listbox.see(index)  # 선택된 항목이 보이도록 스크롤 조정


    def file_listbox_selected(self, event=None):
        selected_index = self.file_listbox.curselection()  # 선택된 아이템의 인덱스를 가져옵니다.
        if selected_index:
            selected_item = self.file_listbox.get(selected_index)  # 선택된 아이템의 내용을 가져옵니다.
            self.load_media(selected_item)  # 선택된 아이템에 해당하는 이미지를 출력합니다.


    def my_log(self, msg):
        self.text_log.config(state="normal")  # 텍스트 위젯을 편집 가능한 상태로 설정
        self.text_log.insert(tk.INSERT, msg + "\r\n")  # 텍스트 삽입
        self.text_log.see("end")  # 스크롤바를 맨 아래로 이동하여 가장 최근에 추가된 텍스트를 표시
        self.text_log.config(state="disabled")  # 텍스트 위젯을 읽기 전용 상태로 다시 설정






    def on_key(self, event):
        # Control키와 Shift키와 동시에 눌렀을 때
        if event.keysym == 'O' and (event.state & 0x4) != 0 and (event.state & 0x1) != 0: # 0x1은 Shift 키
            self.dir_open()

        # Control키와 동시에 눌렀을 때
        if (event.state & 0x4) != 0: # 0x4는 Control 키
            if event.keysym == 's':
                self.save_file()
            if event.keysym == 'o':
                self.file_open()

        # 단일 키
        if event.keysym == 'w':
            self.create_rectbox()
        if event.keysym == 'q':
            self.prev_file()
        if event.keysym == 'e':
            self.next_file()

        if not self.is_image:
            if event.keysym == 'space':
                self.toggle_play()
            if event.keysym == 'Right':
                self.next_frame()
            if event.keysym == 'Left':
                self.prev_frame()



    def next_frame(self):
        if self.cap.isOpened():
            # 현재 프레임 위치
            current_frame = self.cap.get(cv2.CAP_PROP_POS_FRAMES)
            # 다음 프레임으로 이동
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, current_frame + 150)

    def prev_frame(self):
        if self.cap.isOpened():
            # 현재 프레임 위치
            current_frame = self.cap.get(cv2.CAP_PROP_POS_FRAMES)
            # 이전 프레임으로 이동
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, max(0, current_frame - 150))


    def stop_process(self):
        if self.cap:
            self.cap.release()




    def create_gui(self):
        self.setting_frame = tk.Frame(self.top)
        self.setting_frame.grid(row=0, column=0, padx=30, pady=10)

        # 이미지 비디오 토글 버튼
        self.toggle_image_video_button = tk.Button(self.setting_frame, text="Image", width=18, height=2, bg="#FFFFEE", command=self.toggle_image_video)
        self.toggle_image_video_button.pack()

        # 이미지 로드
        self.file_open_button = tk.Button(self.setting_frame, text="Open File", width=18, height=2, command=self.file_open)
        self.file_open_button.pack()

        self.dir_open_button = tk.Button(self.setting_frame, text="Dir Open", width=18, height=2, command=self.dir_open)
        self.dir_open_button.pack()



        self.separator_frame = tk.Frame(self.setting_frame, height=3, bg="white")
        self.separator_frame.pack(fill=tk.X, pady=(5, 5))


        # 앞뒤 이미지 로드
        self.next_image_button = tk.Button(self.setting_frame, text="Next File", width=18, height=2, command=self.next_file)
        self.next_image_button.pack()

        self.prev_image_button = tk.Button(self.setting_frame, text="Prev File", width=18, height=2, command=self.prev_file)
        self.prev_image_button.pack()



        self.separator_frame1 = tk.Frame(self.setting_frame, height=3, bg="white")
        self.separator_frame1.pack(fill=tk.X, pady=(5, 5))


        # 이미지 저장
        self.save_button = tk.Button(self.setting_frame, text="Save", width=18, height=2, command=self.save_file)
        self.save_button.pack()

        self.change_save_dir_button = tk.Button(self.setting_frame, text="Change Save Dir", width=18, height=2, command=self.change_save_dir)
        self.change_save_dir_button.pack()

        self.open_save_folder_button = tk.Button(self.setting_frame, text="Open Save Folder", width=18, height=2, command=self.open_save_folder)
        self.open_save_folder_button.pack()



        self.separator_frame2 = tk.Frame(self.setting_frame, height=3, bg="white")
        self.separator_frame2.pack(fill=tk.X, pady=(5, 5))


        # 이미지 선택 사각형 그리기
        self.create_rectbox_button = tk.Button(self.setting_frame, text="Create Rectbox", width=18, height=2, command=self.create_rectbox)
        self.create_rectbox_button.pack()

        self.delete_rectbox_button = tk.Button(self.setting_frame, text="Delete Rectbox", width=18, height=2, command=self.delete_rectbox)
        self.delete_rectbox_button.pack()



        self.separator_frame3 = tk.Frame(self.setting_frame, height=3, bg="white")
        self.separator_frame3.pack(fill=tk.X, pady=(5, 5))


        # 줌
        self.zoom_in_button = tk.Button(self.setting_frame, text="Zoom In", width=18, height=2, command=self.zoom_in)
        self.zoom_in_button.pack()

        self.zoom_frame = tk.Frame(self.setting_frame, width=18)
        self.zoom_frame.pack()

        self.zoom_entry = tk.Entry(self.zoom_frame, width=8)
        self.zoom_entry.insert(tk.END, int(self.scale*100))
        self.zoom_entry.pack(side=tk.LEFT)
        self.zoom_entry.bind("<KeyRelease-Return>", self.update_zoom_entry)

        self.zoom_percent_label = tk.Label(self.zoom_frame, width=6, text="%")
        self.zoom_percent_label.pack(side=tk.LEFT)

        self.zoom_out_button = tk.Button(self.setting_frame, text="Zoom Out", width=18, height=2, command=self.zoom_out)
        self.zoom_out_button.pack()



        self.separator_frame4 = tk.Frame(self.setting_frame, height=3, bg="white")
        self.separator_frame4.pack(fill=tk.X, pady=(5, 5))


        # 이미지 에디터
        self.original_image_button = tk.Button(self.setting_frame, text="Original", width=18, height=2, command=self.original_image)
        self.original_image_button.pack()

        self.gray_image_button = tk.Button(self.setting_frame, text="Gray", width=18, height=2, command=self.gray_image)
        self.gray_image_button.pack()

        self.brightly_image_button = tk.Button(self.setting_frame, text="Brightly", width=18, height=2, command=self.brightly_image)
        self.brightly_image_button.pack()

        self.brightness_frame = tk.Frame(self.setting_frame, width=18)
        self.brightness_frame.pack()

        self.brightness_entry = tk.Entry(self.brightness_frame, width=8)
        self.brightness_entry.insert(tk.END, int(self.brightness*50))
        self.brightness_entry.pack(side=tk.LEFT)
        self.brightness_entry.bind("<KeyRelease-Return>", self.update_brightness_entry)

        self.brightness_percent_label = tk.Label(self.brightness_frame, width=6, text="%")
        self.brightness_percent_label.pack(side=tk.LEFT)

        self.darkly_image_button = tk.Button(self.setting_frame, text="Darkly", width=18, height=2, command=self.darkly_image)
        self.darkly_image_button.pack()



        # 이미지 캔버스
        self.create_image_canvas_frame()




        self.label_frame = tk.Frame(self.top)
        self.label_frame.grid(row=0, column=2, padx=30, pady=10)

        # 학습 데이터 분류
        self.data_option_label = tk.Label(self.label_frame, text="Data Option")
        self.data_option_label.grid(row=0, column=0, columnspan=4, sticky="w")

        self.data_option = tk.StringVar()

        self.data_option_combobox = ttk.Combobox(self.label_frame, textvariable=self.data_option, width=32, state="readonly") #콤보박스 선언
        self.data_option_combobox['value'] = ('train','valid','test') #콤보박스 요소 삽입
        self.data_option_combobox.current(0) #0번째로 콤보박스 초기화
        self.data_option_combobox.grid(row=1, column=0, columnspan=4) #콤보박스 배치

        self.data_option_combobox.bind("<<ComboboxSelected>>", self.handle_data_option_event)



        self.separator_frame_label = tk.Frame(self.label_frame, height=3, bg="white")
        self.separator_frame_label.grid(row=2, column=0, columnspan=4, pady=(5, 5), sticky="ew")



        # 라벨링한 이미지 박스
        self.labeled_image_label = tk.Label(self.label_frame, text="Labeled Image")
        self.labeled_image_label.grid(row=3, column=0, columnspan=4, sticky="w")

        self.labeled_image_listbox = tk.Listbox(self.label_frame, width=35, height=7, selectmode="single", exportselection=False)
        self.labeled_image_listbox.grid(row=4, column=0, columnspan=4)
        self.labeled_image_listbox.bind("<<ListboxSelect>>", self.on_labeled_image_listbox_select)



        self.separator_frame_label1 = tk.Frame(self.label_frame, height=3, bg="white")
        self.separator_frame_label1.grid(row=5, column=0, columnspan=4, pady=(5, 5), sticky="ew")


        # 라벨 리스트 박스
        self.label_label = tk.Label(self.label_frame, text="Label")
        self.label_label.grid(row=6, column=0, columnspan=4, sticky="w")

        self.label_entry = tk.Entry(self.label_frame, width=28)
        self.label_entry.grid(row=7, column=0, columnspan=3)
        self.label_entry.bind("<Button-1>", self.on_label_entry_click)
        self.label_entry.bind("<KeyRelease>", self.on_label_entry_change)

        self.label_add_button = tk.Button(self.label_frame, text="+", width=5, command=self.label_add)
        self.label_add_button.grid(row=7, column=3)

        self.label_listbox = tk.Listbox(self.label_frame, width=35, height=7, selectmode="single", exportselection=False)
        self.label_listbox.grid(row=8, column=0, columnspan=4)
        self.label_listbox.bind("<<ListboxSelect>>", self.on_label_listbox_select)

        self.label_edit_button = tk.Button(self.label_frame, text="Update", width=16, height=2, command=self.label_update)
        self.label_edit_button.grid(row=9, column=0, columnspan=2)

        self.label_del_button = tk.Button(self.label_frame, text="Delete", width=16, height=2, command=self.label_del)
        self.label_del_button.grid(row=9, column=2, columnspan=2)

        self.label_list_show()



        self.separator_frame_label2 = tk.Frame(self.label_frame, height=3, bg="white")
        self.separator_frame_label2.grid(row=10, column=0, columnspan=4, pady=(5, 5), sticky="ew")


        # 파일 리스트 박스
        self.file_list_label = tk.Label(self.label_frame, text="File List")
        self.file_list_label.grid(row=11, column=0, columnspan=4, sticky="w")

        self.file_listbox = tk.Listbox(self.label_frame, width=35, selectmode="single", exportselection=False)
        self.file_listbox.grid(row=12, column=0, columnspan=4)
        self.file_listbox.bind("<<ListboxSelect>>", self.file_listbox_selected)



        # 로그
        self.text_log_label = tk.Label(self.label_frame, text="Text Log")
        self.text_log_label.grid(row=13, column=0, columnspan=4, sticky="w")

        self.text_log = st.ScrolledText(self.label_frame,
                                    width = 38,
                                    height = 8,
                                    font = ("Times New Roman",10),
                                    state="disabled")
        self.text_log.grid(row=14, column=0, columnspan=4)



        self.my_log("start data preprocessing...")

        # 키보드 이벤트 바인딩
        self.top.bind('<Key>', self.on_key)

if __name__ == "__main__":
    top = tk.Tk()

    Preprocess(top)

    top.mainloop()