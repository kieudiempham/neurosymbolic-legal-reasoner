import win32com.client as win32
import os

def extract_text_from_doc(doc_path):
    word = win32.gencache.EnsureDispatch('Word.Application')
    word.Visible = False
    doc = word.Documents.Open(doc_path)
    text = doc.Content.Text
    doc.Close()
    word.Quit()
    return text

if __name__ == "__main__":
    doc_path = r"d:\IT\THI\PAPER\project\neurosymbolic-legal-reasoner\data\raw\legal_corpus\labor\08_luat_lao_dong_45_2019_QH14.doc"
    if os.path.exists(doc_path):
        text = extract_text_from_doc(doc_path)
        with open('labor_text.txt', 'w', encoding='utf-8') as f:
            f.write(text)
        print("Text extracted to labor_text.txt")
    else:
        print("File not found")