import PySimpleGUI as sg

layout = [[sg.Text("Тестовое окно PySimpleGUI")], [sg.Button("OK")]]

window = sg.Window("Test PySimpleGUI", layout)

while True:
    event, values = window.read()
    if event == sg.WIN_CLOSED or event == "OK":
        break

window.close()