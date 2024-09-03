from dbr import *
import flet as ft
import pathlib
import google.generativeai as genai
import google.ai.generativelanguage as glm

license_key = "LICENSE-KEY"
BarcodeReader.init_license(license_key)
reader = BarcodeReader()

# https://ai.google.dev/tutorials/python_quickstart
genai.configure(api_key='API_KEY')

# for m in genai.list_models():
#     if 'generateContent' in m.supported_generation_methods:
#         print(m.name)

model_text = genai.GenerativeModel('gemini-pro')
chat_text = model_text.start_chat(history=[])
model_vision = genai.GenerativeModel('gemini-pro-vision')
chat_vision = model_vision.start_chat(history=[])


class Message():
    def __init__(self, user_name: str, text: str, message_type: str, is_image: bool = False):
        self.user_name = user_name
        self.text = text
        self.message_type = message_type
        self.is_image = is_image


class ChatMessage(ft.Row):
    def __init__(self, message: Message):
        super().__init__()
        self.vertical_alignment = "start"
        if message.is_image:
            self.controls = [
                ft.CircleAvatar(
                    content=ft.Text(self.get_initials(message.user_name)),
                    color=ft.colors.WHITE,
                    bgcolor=self.get_avatar_color(message.user_name),
                ),
                ft.Column(
                    [
                        ft.Text(message.user_name, weight="bold"),
                        ft.Image(message.text, width=300,
                                 height=300, fit="contain"),
                    ],
                    tight=True,
                    spacing=5,
                ),
            ]
        else:
            self.controls = [
                ft.CircleAvatar(
                    content=ft.Text(self.get_initials(message.user_name)),
                    color=ft.colors.WHITE,
                    bgcolor=self.get_avatar_color(message.user_name),
                ),
                ft.Column(
                    [
                        ft.Text(message.user_name, weight="bold"),
                        ft.Text(message.text, selectable=True),
                    ],
                    tight=True,
                    spacing=5,
                ),
            ]

    def get_initials(self, user_name: str):
        if user_name:
            return user_name[:1].capitalize()
        else:
            return "Unknown"  # or any default value you prefer

    def get_avatar_color(self, user_name: str):
        if user_name == "Me":
            return ft.colors.BLUE
        elif user_name == "DBR":
            return ft.colors.ORANGE
        else:
            return ft.colors.RED


image_path = None
barcode_text = None


def main(page: ft.Page):
    page.horizontal_alignment = "stretch"
    page.title = "Gemini Chatbot"

    def pick_files_result(e: ft.FilePickerResultEvent):
        global image_path, barcode_text
        barcode_text = None
        image_path = None
        if e.files != None:
            image_path = e.files[0].path
            page.pubsub.send_all(
                Message("Me", image_path, message_type="chat_message", is_image=True))

            text_results = None
            try:
                text_results = reader.decode_file(image_path)

                # if text_results != None:
                #     for text_result in text_results:
                #         print("Barcode Format : ")
                #         print(text_result.barcode_format_string)
                #         print("Barcode Text : ")
                #         print(text_result.barcode_text)
                #         print("Localization Points : ")
                #         print(text_result.localization_result.localization_points)
                #         print("Exception : ")
                #         print(text_result.exception)
                #         print("-------------")
            except BarcodeReaderError as bre:
                print(bre)

            if text_results != None:
                barcode_text = text_results[0].barcode_text
                page.pubsub.send_all(
                    Message("DBR", barcode_text, message_type="chat_message"))

    pick_files_dialog = ft.FilePicker(on_result=pick_files_result)
    page.overlay.append(pick_files_dialog)

    def pick_file(e):
        pick_files_dialog.pick_files()

    def clear_message(e):
        global image_path
        image_path = None
        chat.controls.clear()
        page.update()

    def send_message_click(e):
        global image_path
        if new_message.value != "":
            page.pubsub.send_all(
                Message("Me", new_message.value, message_type="chat_message"))

            question = new_message.value

            new_message.value = ""
            new_message.focus()
            page.update()

            page.pubsub.send_all(
                Message("Gemini", "Thinking...", message_type="chat_message"))

            if question == ":verify":
                question = "recognize text around the barcode"
                response = model_vision.generate_content(
                    glm.Content(
                        parts=[
                            glm.Part(
                                text=question),
                            glm.Part(
                                inline_data=glm.Blob(
                                    mime_type='image/jpeg',
                                    data=pathlib.Path(
                                        image_path).read_bytes()
                                )
                            ),
                        ],
                    ))

                text = response.text
                page.pubsub.send_all(
                    Message("Gemini", text, message_type="chat_message"))

                if barcode_text == None:
                    return

                text = text.replace(" ", "")
                if text.find(barcode_text) != -1:
                    page.pubsub.send_all(
                        Message("Gemini", barcode_text + " is correct ✓", message_type="chat_message"))
                else:
                    page.pubsub.send_all(
                        Message("Gemini", barcode_text + " may not be correct", message_type="chat_message"))
            else:
                if image_path == None:
                    response = chat_text.send_message(
                        question)
                else:
                    response = model_vision.generate_content(
                        glm.Content(
                            parts=[
                                glm.Part(
                                    text=question),
                                glm.Part(
                                    inline_data=glm.Blob(
                                        mime_type='image/jpeg',
                                        data=pathlib.Path(
                                            image_path).read_bytes()
                                    )
                                ),
                            ],
                        ))

                page.pubsub.send_all(
                    Message("Gemini", response.text, message_type="chat_message"))

    def on_message(message: Message):
        if message.message_type == "chat_message":
            m = ChatMessage(message)
        elif message.message_type == "login_message":
            m = ft.Text(message.text, italic=True,
                        color=ft.colors.BLACK45, size=12)
        chat.controls.append(m)
        page.update()

    page.pubsub.subscribe(on_message)

    # Chat messages
    chat = ft.ListView(
        expand=True,
        spacing=10,
        auto_scroll=True,
    )

    # A new message entry form
    new_message = ft.TextField(
        hint_text="Write a message...",
        autofocus=True,
        shift_enter=True,
        min_lines=1,
        max_lines=5,
        filled=True,
        expand=True,
        on_submit=send_message_click,
    )

    # Add everything to the page
    page.add(
        ft.Container(
            content=chat,
            border=ft.border.all(1, ft.colors.OUTLINE),
            border_radius=5,
            padding=10,
            expand=True,
        ),
        ft.Row(
            [
                ft.IconButton(
                    icon=ft.icons.UPLOAD_FILE,
                    tooltip="Pick an image",
                    on_click=pick_file,
                ),
                new_message,
                ft.IconButton(
                    icon=ft.icons.SEND_ROUNDED,
                    tooltip="Send message",
                    on_click=send_message_click,
                ),
                ft.IconButton(
                    icon=ft.icons.CLEAR_ALL,
                    tooltip="Clear all messages",
                    on_click=clear_message,
                ),
            ]
        ),
    )


ft.app(main)
