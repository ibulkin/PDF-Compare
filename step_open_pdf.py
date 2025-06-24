import PySimpleGUI as sg
import fitz  # pymupdf

layout = [
    [sg.Text('Выберите PDF-файл:'), sg.Input(key='-FILE-'), sg.FileBrowse(file_types=(("PDF Files", "*.pdf"),))],
    [sg.Button('Открыть'), sg.Button('Отмена')]
]

window = sg.Window('Открытие PDF', layout)

while True:
    event, values = window.read()
    if event in (sg.WINDOW_CLOSED, 'Отмена'):
        print("Операция отменена")
        break
    if event == 'Открыть':
        file = values['-FILE-']
        if file:
            print("Файл выбран:", file)
            try:
                doc = fitz.open(file)
                print(f"PDF успешно открыт, страниц: {doc.page_count}")
                doc.close()
            except Exception as e:
                print("Ошибка открытия PDF:", e)
        else:
            print("Файл не выбран!")
        break

window.close()